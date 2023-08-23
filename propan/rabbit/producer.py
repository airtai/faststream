from contextlib import asynccontextmanager
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    AsyncIterator,
    Callable,
    Optional,
    Type,
    Union,
)

import aio_pika
import aiormq
import anyio
from anyio.streams.memory import MemoryObjectReceiveStream

from propan.broker.parsers import resolve_custom_func
from propan.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    AsyncDecoder,
    AsyncParser,
)
from propan.exceptions import WRONG_PUBLISH_ARGS
from propan.rabbit.helpers import RabbitDeclarer
from propan.rabbit.parser import AioPikaParser
from propan.rabbit.shared.constants import RABBIT_REPLY
from propan.rabbit.shared.schemas import RabbitExchange, RabbitQueue
from propan.rabbit.shared.types import TimeoutType
from propan.rabbit.types import AioPikaSendableMessage
from propan.types import SendableMessage


class AioPikaPropanProducer:
    _channel: aio_pika.RobustChannel
    _rpc_lock: anyio.Lock
    _decoder: AsyncDecoder[aio_pika.IncomingMessage]
    _parser: AsyncParser[aio_pika.IncomingMessage]
    declarer: RabbitDeclarer

    def __init__(
        self,
        channel: aio_pika.RobustChannel,
        declarer: RabbitDeclarer,
        parser: Optional[AsyncCustomParser[aio_pika.IncomingMessage]],
        decoder: Optional[AsyncCustomDecoder[aio_pika.IncomingMessage]],
    ):
        self._channel = channel
        self.declarer = declarer
        self._parser = resolve_custom_func(parser, AioPikaParser.parse_message)
        self._decoder = resolve_custom_func(decoder, AioPikaParser.decode_message)
        self._rpc_lock = anyio.Lock()

    async def publish(
        self,
        message: AioPikaSendableMessage = "",
        queue: Union[RabbitQueue, str] = "",
        exchange: Union[RabbitExchange, str, None] = None,
        *,
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: TimeoutType = None,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
        persist: bool = False,
        reply_to: Optional[str] = None,
        **message_kwargs: Any,
    ) -> Union[aiormq.abc.ConfirmationFrameType, SendableMessage]:
        p_queue = RabbitQueue.validate(queue)

        context: AsyncContextManager[
            Optional[MemoryObjectReceiveStream[aio_pika.IncomingMessage]]
        ]
        if rpc is True:
            if reply_to is not None:
                raise WRONG_PUBLISH_ARGS
            else:
                context = _RPCCallback(
                    self._rpc_lock,
                    self.declarer.queues[RABBIT_REPLY],
                )
        else:
            context = _fake_context()

        async with context as response_queue:
            r = await self._publish(
                message=message,
                exchange=exchange,
                routing_key=routing_key or p_queue.routing or "",
                mandatory=mandatory,
                immediate=immediate,
                timeout=timeout,
                persist=persist,
                reply_to=RABBIT_REPLY if response_queue else reply_to,
                **message_kwargs,
            )

            if response_queue is None:
                return r

            else:
                scope: Callable[[Optional[float], bool], AsyncContextManager[Any]]
                if raise_timeout:
                    scope = anyio.fail_after
                else:
                    scope = anyio.move_on_after

                msg: Optional[aio_pika.IncomingMessage] = None
                with scope(rpc_timeout):
                    msg = await response_queue.receive()

                if msg:
                    return await self._decoder(await self._parser(msg))

        return None

    async def _publish(
        self,
        message: AioPikaSendableMessage = "",
        exchange: Union[RabbitExchange, str, None] = None,
        *,
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: TimeoutType = None,
        persist: bool = False,
        reply_to: Optional[str] = None,
        **message_kwargs: Any,
    ) -> Union[aiormq.abc.ConfirmationFrameType, SendableMessage]:
        p_exchange = RabbitExchange.validate(exchange)

        if p_exchange is None:
            exchange_obj = self._channel.default_exchange
        else:
            exchange_obj = await self.declarer.declare_exchange(p_exchange)

        message = AioPikaParser.encode_message(
            message=message,
            persist=persist,
            reply_to=reply_to,
            **message_kwargs,
        )

        return await exchange_obj.publish(
            message=message,
            routing_key=routing_key,
            mandatory=mandatory,
            immediate=immediate,
            timeout=timeout,
        )


class _RPCCallback:
    def __init__(self, lock: anyio.Lock, callback_queue: aio_pika.RobustQueue):
        self.lock = lock
        self.queue = callback_queue

    async def __aenter__(self) -> MemoryObjectReceiveStream[aio_pika.IncomingMessage]:
        (
            send_response_stream,
            receive_response_stream,
        ) = anyio.create_memory_object_stream(max_buffer_size=1)
        await self.lock.acquire()

        self.consumer_tag = await self.queue.consume(
            callback=send_response_stream.send,
            no_ack=True,
        )

        return receive_response_stream

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None:
        self.lock.release()
        await self.queue.cancel(self.consumer_tag)


@asynccontextmanager
async def _fake_context() -> AsyncIterator[None]:
    yield None

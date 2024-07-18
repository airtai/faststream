from asyncio import Future
from contextvars import ContextVar
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    ClassVar,
    Dict,
    Optional,
    Type,
    Union,
    cast,
)

import anyio
from typing_extensions import override

from faststream.broker.publisher.proto import ProducerProto
from faststream.broker.utils import resolve_custom_func
from faststream.exceptions import WRONG_PUBLISH_ARGS
from faststream.rabbit.parser import AioPikaParser
from faststream.rabbit.schemas import RABBIT_REPLY, RabbitExchange
from faststream.utils.classes import Singleton
from faststream.utils.functions import fake_context, timeout_scope

if TYPE_CHECKING:
    from types import TracebackType

    import aiormq
    from aio_pika import IncomingMessage, RobustChannel, RobustQueue
    from aio_pika.abc import DateType, HeadersType, TimeoutType

    from faststream.broker.types import (
        AsyncCallable,
        CustomCallable,
    )
    from faststream.rabbit.helpers.declarer import RabbitDeclarer
    from faststream.rabbit.types import AioPikaSendableMessage
    from faststream.types import SendableMessage


class AioPikaFastProducer(ProducerProto):
    """A class for fast producing messages using aio-pika."""

    _decoder: "AsyncCallable"
    _parser: "AsyncCallable"

    def __init__(
        self,
        *,
        declarer: "RabbitDeclarer",
        parser: Optional["CustomCallable"],
        decoder: Optional["CustomCallable"],
    ) -> None:
        self.declarer = declarer
        self.rpc_manager = _RPCManager(declarer=declarer)

        default_parser = AioPikaParser()
        self._parser = resolve_custom_func(parser, default_parser.parse_message)
        self._decoder = resolve_custom_func(decoder, default_parser.decode_message)

    @override
    async def publish(  # type: ignore[override]
        self,
        message: "AioPikaSendableMessage",
        exchange: Union["RabbitExchange", str, None] = None,
        *,
        correlation_id: str = "",
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: "TimeoutType" = None,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
        persist: bool = False,
        reply_to: Optional[str] = None,
        headers: Optional["HeadersType"] = None,
        content_type: Optional[str] = None,
        content_encoding: Optional[str] = None,
        priority: Optional[int] = None,
        expiration: Optional["DateType"] = None,
        message_id: Optional[str] = None,
        timestamp: Optional["DateType"] = None,
        message_type: Optional[str] = None,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
    ) -> Optional[Any]:
        """Publish a message to a RabbitMQ queue."""
        context: AsyncContextManager[Optional[RobustChannel]]
        channel: Optional[RobustChannel]
        response: Optional[Future[IncomingMessage]]

        if rpc:
            if reply_to is not None:
                raise WRONG_PUBLISH_ARGS

            context = await self.rpc_manager(correlation_id=correlation_id)
            response = self.rpc_manager.result
            reply_to = self.rpc_manager.queue.name

        else:
            response = None
            context = fake_context()

        async with context as channel:
            r = await self._publish(
                message=message,
                exchange=exchange,
                routing_key=routing_key,
                mandatory=mandatory,
                immediate=immediate,
                timeout=timeout,
                persist=persist,
                reply_to=reply_to,
                headers=headers,
                content_type=content_type,
                content_encoding=content_encoding,
                priority=priority,
                correlation_id=correlation_id,
                expiration=expiration,
                message_id=message_id,
                timestamp=timestamp,
                message_type=message_type,
                user_id=user_id,
                app_id=app_id,
                channel=channel,
            )

            if response is None:
                return r

            else:
                msg: Optional[IncomingMessage] = None
                with timeout_scope(rpc_timeout, raise_timeout):
                    msg = await response

                if msg:  # pragma: no branch
                    return await self._decoder(await self._parser(msg))

        return None

    async def _publish(
        self,
        message: "AioPikaSendableMessage",
        *,
        correlation_id: str,
        exchange: Union["RabbitExchange", str, None],
        routing_key: str,
        mandatory: bool,
        immediate: bool,
        timeout: "TimeoutType",
        persist: bool,
        reply_to: Optional[str],
        headers: Optional["HeadersType"],
        content_type: Optional[str],
        content_encoding: Optional[str],
        priority: Optional[int],
        expiration: Optional["DateType"],
        message_id: Optional[str],
        timestamp: Optional["DateType"],
        message_type: Optional[str],
        user_id: Optional[str],
        app_id: Optional[str],
        channel: Optional["RobustChannel"],
    ) -> Union["aiormq.abc.ConfirmationFrameType", "SendableMessage"]:
        """Publish a message to a RabbitMQ exchange."""
        message = AioPikaParser.encode_message(
            message=message,
            persist=persist,
            reply_to=reply_to,
            headers=headers,
            content_type=content_type,
            content_encoding=content_encoding,
            priority=priority,
            correlation_id=correlation_id,
            expiration=expiration,
            message_id=message_id,
            timestamp=timestamp,
            message_type=message_type,
            user_id=user_id,
            app_id=app_id,
        )

        exchange_obj = await self.declarer.declare_exchange(
            exchange=RabbitExchange.validate(exchange),
            passive=True,
            channel=channel,
        )

        return await exchange_obj.publish(
            message=message,
            routing_key=routing_key,
            mandatory=mandatory,
            immediate=immediate,
            timeout=timeout,
        )


class _RPCManager(Singleton, AsyncContextManager["RobustChannel"]):
    """A class provides an RPC lock."""

    # Singleton entities (all async tasks share the same context)
    __lock = anyio.Lock()
    __rpc_messages: ClassVar[Dict[str, Future]] = {}  # type: ignore[type-arg]
    __consumer_tags: ClassVar[Dict["RobustChannel", str]] = {}

    # Context variables (async tasks have their own context)
    __current_correlation_id: ContextVar[str] = ContextVar("rpc_correlation_id")
    __current_queue: ContextVar["RobustQueue"] = ContextVar("rpc_queue")
    __current_result: ContextVar[Future] = ContextVar("rpc_result")  # type: ignore[type-arg]

    def __init__(self, declarer: "RabbitDeclarer") -> None:
        self.declarer = declarer

    @property
    def queue(self) -> "RobustQueue":
        return self.__current_queue.get()

    @property
    def correlation_id(self) -> str:
        return self.__current_correlation_id.get()

    @property
    def result(self) -> Future:  # type: ignore[type-arg]
        return self.__current_result.get()

    async def __rpc_callback(self, msg: "IncomingMessage") -> None:
        """A callback function to handle RPC messages."""
        if msg.correlation_id in self.__rpc_messages:
            self.__rpc_messages[msg.correlation_id].set_result(msg)

    async def __call__(self, correlation_id: str) -> "_RPCManager":
        """Sets the current RPC context."""
        async with self.__lock:
            if correlation_id in self.__rpc_messages:
                raise RuntimeError("The correlation ID is already in use.")
            self.__current_result.set(Future())
            self.__rpc_messages[correlation_id] = self.result

        self.__current_queue.set(await self.declarer.declare_queue(RABBIT_REPLY))
        self.__current_correlation_id.set(correlation_id)

        return self

    async def __aenter__(self) -> "RobustChannel":
        async with self.__lock:
            if self.queue.channel not in self.__consumer_tags:
                consumer_tag = await self.queue.consume(
                    callback=self.__rpc_callback,  # type: ignore[arg-type]
                    no_ack=True,
                )
                self.__consumer_tags[self.queue.channel] = consumer_tag  # type: ignore[index]

            return cast("RobustChannel", self.queue.channel)

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> None:
        self.__rpc_messages.pop(self.__current_correlation_id.get())  # type: ignore[call-overload]
        if exc_tb:
            async with self.__lock:
                if self.queue.channel in self.__consumer_tags:
                    await self.queue.cancel(self.__consumer_tags[self.queue.channel])  # type: ignore[index]
                    self.__consumer_tags.pop(self.queue.channel)  # type: ignore[call-overload]

import asyncio
import contextlib
from collections.abc import Iterable, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
)

import anyio
from typing_extensions import override

from faststream._internal.subscriber.usecase import SubscriberUsecase
from faststream._internal.subscriber.utils import process_msg
from faststream.exceptions import SetupError
from faststream.rabbit.parser import AioPikaParser
from faststream.rabbit.publisher.fake import RabbitFakePublisher

if TYPE_CHECKING:
    from aio_pika import IncomingMessage, RobustQueue
    from fast_depends.dependencies import Dependant

    from faststream._internal.basic_types import AnyDict
    from faststream._internal.publisher.proto import BasePublisherProto
    from faststream._internal.state import BrokerState
    from faststream._internal.types import BrokerMiddleware, CustomCallable
    from faststream.message import StreamMessage
    from faststream.middlewares import AckPolicy
    from faststream.rabbit.helpers import RabbitDeclarer
    from faststream.rabbit.message import RabbitMessage
    from faststream.rabbit.publisher.producer import AioPikaFastProducer
    from faststream.rabbit.schemas import (
        Channel,
        RabbitExchange,
        RabbitQueue,
    )


class LogicSubscriber(SubscriberUsecase["IncomingMessage"]):
    """A class to handle logic for RabbitMQ message consumption."""

    app_id: Optional[str]
    declarer: Optional["RabbitDeclarer"]

    _consumer_tag: Optional[str]
    _queue_obj: Optional["RobustQueue"]
    _producer: Optional["AioPikaFastProducer"]

    def __init__(
        self,
        *,
        queue: "RabbitQueue",
        exchange: "RabbitExchange",
        channel: Optional["Channel"],
        consume_args: Optional["AnyDict"],
        # Subscriber args
        ack_policy: "AckPolicy",
        no_reply: bool,
        no_ack: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Sequence["BrokerMiddleware[IncomingMessage]"],
    ) -> None:
        self.queue = queue
        self.exchange = exchange

        parser = AioPikaParser(pattern=queue.path_regex)

        super().__init__(
            default_parser=parser.parse_message,
            default_decoder=parser.decode_message,
            # Propagated options
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
        )

        self.consume_args = consume_args or {}
        self.__no_ack = no_ack

        self._consumer_tag = None
        self._queue_obj = None
        self.channel = channel

        # Setup it later
        self.declarer = None

    @override
    def _setup(  # type: ignore[override]
        self,
        *,
        declarer: "RabbitDeclarer",
        # basic args
        extra_context: "AnyDict",
        # broker options
        broker_parser: Optional["CustomCallable"],
        broker_decoder: Optional["CustomCallable"],
        # dependant args
        state: "BrokerState",
    ) -> None:
        self.declarer = declarer

        super()._setup(
            extra_context=extra_context,
            broker_parser=broker_parser,
            broker_decoder=broker_decoder,
            state=state,
        )

    @override
    async def start(self) -> None:
        """Starts the consumer for the RabbitMQ queue."""
        if self.declarer is None:
            msg = "You should setup subscriber at first."
            raise SetupError(msg)

        self._queue_obj = queue = await self.declarer.declare_queue(
            self.queue, channel=self.channel
        )

        if (
            self.exchange is not None
            and self.queue.declare  # queue just getted from RMQ
            and self.exchange.name  # check Exchange is not default
        ):
            exchange = await self.declarer.declare_exchange(
                self.exchange, channel=self.channel
            )

            await queue.bind(
                exchange,
                routing_key=self.queue.routing,
                arguments=self.queue.bind_arguments,
                timeout=self.queue.timeout,
                robust=self.queue.robust,
            )

        if self.calls:
            self._consumer_tag = await self._queue_obj.consume(
                # NOTE: aio-pika expects AbstractIncomingMessage, not IncomingMessage
                self.consume,  # type: ignore[arg-type]
                no_ack=self.__no_ack,
                arguments=self.consume_args,
            )

        await super().start()

    async def close(self) -> None:
        await super().close()

        if self._queue_obj is not None:
            if self._consumer_tag is not None:  # pragma: no branch
                if not self._queue_obj.channel.is_closed:
                    await self._queue_obj.cancel(self._consumer_tag)
                self._consumer_tag = None

            self._queue_obj = None

    @override
    async def get_one(
        self,
        *,
        timeout: float = 5.0,
        no_ack: bool = True,
    ) -> "Optional[RabbitMessage]":
        assert self._queue_obj, "You should start subscriber at first."  # nosec B101
        assert (  # nosec B101
            not self.calls
        ), "You can't use `get_one` method if subscriber has registered handlers."

        sleep_interval = timeout / 10

        raw_message: Optional[IncomingMessage] = None
        with (
            contextlib.suppress(asyncio.exceptions.CancelledError),
            anyio.move_on_after(timeout),
        ):
            while (  # noqa: ASYNC110
                raw_message := await self._queue_obj.get(
                    fail=False,
                    no_ack=no_ack,
                    timeout=timeout,
                )
            ) is None:
                await anyio.sleep(sleep_interval)

        context = self._state.get().di_state.context

        msg: Optional[RabbitMessage] = await process_msg(  # type: ignore[assignment]
            msg=raw_message,
            middlewares=(
                m(raw_message, context=context) for m in self._broker_middlewares
            ),
            parser=self._parser,
            decoder=self._decoder,
        )
        return msg

    def _make_response_publisher(
        self,
        message: "StreamMessage[Any]",
    ) -> Sequence["BasePublisherProto"]:
        return (
            RabbitFakePublisher(
                self._state.get().producer,
                routing_key=message.reply_to,
                app_id=self.app_id,
            ),
        )

    @staticmethod
    def build_log_context(
        message: Optional["StreamMessage[Any]"],
        queue: "RabbitQueue",
        exchange: Optional["RabbitExchange"] = None,
    ) -> dict[str, str]:
        return {
            "queue": queue.name,
            "exchange": getattr(exchange, "name", ""),
            "message_id": getattr(message, "message_id", ""),
        }

    def get_log_context(
        self,
        message: Optional["StreamMessage[Any]"],
    ) -> dict[str, str]:
        return self.build_log_context(
            message=message,
            queue=self.queue,
            exchange=self.exchange,
        )

    def add_prefix(self, prefix: str) -> None:
        """Include Subscriber in router."""
        self.queue = self.queue.add_prefix(prefix)

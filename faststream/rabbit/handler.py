from dataclasses import asdict
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncContextManager,
    Callable,
    Dict,
    Iterable,
    Optional,
    Sequence,
)

import aio_pika
from typing_extensions import override

from faststream.broker.core.handler import BaseHandler
from faststream.broker.core.publisher import FakePublisher
from faststream.broker.parsers import resolve_custom_func
from faststream.rabbit.helpers import RabbitDeclarer
from faststream.rabbit.parser import AioPikaParser
from faststream.rabbit.schemas.schemas import (
    BaseRMQInformation,
    RabbitExchange,
    RabbitQueue,
    ReplyConfig,
)
from faststream.types import AnyDict

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends

    from faststream.broker.core.handler_wrapper_mixin import WrapperProtocol
    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        BrokerMiddleware,
        CustomDecoder,
        CustomParser,
        Filter,
        PublisherProtocol,
        SubscriberMiddleware,
    )


class LogicHandler(BaseHandler[aio_pika.IncomingMessage], BaseRMQInformation):
    """A class to handle logic for RabbitMQ message consumption.

    Attributes:
        queue : RabbitQueue object representing the queue to consume from
        exchange : Optional RabbitExchange object representing the exchange to bind the queue to
        consume_args : Additional arguments to pass when consuming from the queue
        _consumer_tag : Optional string representing the consumer tag
        _queue_obj : Optional aio_pika.RobustQueue object representing the declared queue

    Methods:
        __init__ : Initializes the LogicHandler object
        add_call : Adds a call to be handled by the LogicHandler
        start : Starts consuming messages from the queue
        close : Closes the consumer and cancels message consumption
    """

    _consumer_tag: Optional[str]
    _queue_obj: Optional[aio_pika.RobustQueue]

    def __init__(
        self,
        *,
        queue: RabbitQueue,
        watcher: Callable[..., AsyncContextManager[None]],
        graceful_timeout: Optional[float],
        middlewares: Iterable["BrokerMiddleware[aio_pika.IncomingMessage]"],
        app_id: Optional[str],
        extra_context: Optional[AnyDict],
        # RMQ information
        exchange: Optional[RabbitExchange],
        consume_args: Optional[AnyDict],
        reply_config: Optional[ReplyConfig],
        # AsyncAPI information
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
        virtual_host: str,
    ) -> None:
        """Initialize a RabbitMQ consumer."""
        super().__init__(
            middlewares=middlewares,
            graceful_timeout=graceful_timeout,
            watcher=watcher,
            extra_context=extra_context,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.consume_args = consume_args or {}
        self.reply_config = asdict(reply_config) if reply_config else {}

        self._consumer_tag = None
        self._queue_obj = None

        self.producer = None

        # BaseRMQInformation
        self.app_id = app_id
        self.queue = queue
        self.exchange = exchange
        self.virtual_host = virtual_host

    @override
    def add_call(  # type: ignore[override]
        self,
        *,
        filter: "Filter[StreamMessage[aio_pika.IncomingMessage]]",
        parser: Optional["CustomParser[aio_pika.IncomingMessage]"],
        decoder: Optional["CustomDecoder[StreamMessage[aio_pika.IncomingMessage]]"],
        middlewares: Iterable["SubscriberMiddleware"],
        dependencies: Sequence["Depends"],
        **wrap_kwargs: Any,
    ) -> "WrapperProtocol[aio_pika.IncomingMessage]":
        return super().add_call(
            parser_=resolve_custom_func(parser, AioPikaParser.parse_message),
            decoder_=resolve_custom_func(decoder, AioPikaParser.decode_message),
            filter_=filter,
            middlewares_=middlewares,
            dependencies_=dependencies,
            **wrap_kwargs,
        )

    @override
    async def start(  # type: ignore[override]
        self,
        declarer: RabbitDeclarer,
        producer: Optional["PublisherProtocol"],
    ) -> None:
        """Starts the consumer for the RabbitMQ queue.

        Args:
            declarer: RabbitDeclarer object used to declare the queue and exchange
        """
        self._queue_obj = queue = await declarer.declare_queue(self.queue)

        if self.exchange is not None:
            exchange = await declarer.declare_exchange(self.exchange)
            if not queue.passive:
                await queue.bind(
                    exchange,
                    routing_key=self.queue.routing,
                    arguments=self.queue.bind_arguments,
                    timeout=self.queue.timeout,
                    robust=self.queue.robust,
                )

        self._consumer_tag = await queue.consume(
            # NOTE: aio-pika expects AbstractIncomingMessage, not IncomingMessage
            self.consume,  # type: ignore[arg-type]
            arguments=self.consume_args,
        )

        await super().start(producer=producer)

    async def close(self) -> None:
        await super().close()

        if self._queue_obj is not None:
            if self._consumer_tag is not None:  # pragma: no branch
                if not self._queue_obj.channel.is_closed:
                    await self._queue_obj.cancel(self._consumer_tag)

                self._consumer_tag = None

            self._queue_obj = None

    def make_response_publisher(
        self, message: "StreamMessage[Any]"
    ) -> Sequence[FakePublisher]:
        if not message.reply_to or self.producer is None:
            return ()

        return (
            FakePublisher(
                self.producer.publish,
                routing_key=message.reply_to,
                app_id=self.app_id,
                **self.reply_config,
            ),
        )

    @staticmethod
    def get_routing_hash(
        queue: RabbitQueue,
        exchange: Optional[RabbitExchange] = None,
    ) -> int:
        """Calculate the routing hash for a RabbitMQ queue and exchange.

        Args:
            queue: The RabbitMQ queue.
            exchange: The RabbitMQ exchange (optional).

        Returns:
            The routing hash as an integer.
        """
        return hash(queue) + hash(exchange or "")

    def __hash__(self) -> int:
        return self.get_routing_hash(self.queue, self.exchange)

    @staticmethod
    def build_log_context(
        message: Optional["StreamMessage[Any]"],
        queue: RabbitQueue,
        exchange: Optional[RabbitExchange] = None,
    ) -> Dict[str, str]:
        return {
            "queue": queue.name,
            "exchange": getattr(exchange, "name", ""),
            "message_id": getattr(message, "message_id", ""),
        }

    def get_log_context(
        self,
        message: Optional["StreamMessage[Any]"],
    ) -> Dict[str, str]:
        return self.build_log_context(
            message=message,
            queue=self.queue,
            exchange=self.exchange,
        )

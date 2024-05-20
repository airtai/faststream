from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Optional,
    Sequence,
    Union,
)

from typing_extensions import override

from faststream.broker.publisher.fake import FakePublisher
from faststream.broker.subscriber.usecase import SubscriberUsecase
from faststream.exceptions import SetupError
from faststream.rabbit.parser import AioPikaParser
from faststream.rabbit.schemas import BaseRMQInformation

if TYPE_CHECKING:
    from aio_pika import IncomingMessage, RobustQueue
    from fast_depends.dependencies import Depends

    from faststream.broker.message import StreamMessage
    from faststream.broker.types import BrokerMiddleware, CustomCallable
    from faststream.rabbit.publisher.producer import AioPikaFastProducer
    from faststream.rabbit.schemas import (
        RabbitExchange,
        RabbitQueue,
        ReplyConfig,
    )
    from faststream.rabbit.utils import RabbitDeclarer
    from faststream.types import AnyDict, Decorator, LoggerProto


class LogicSubscriber(
    SubscriberUsecase["IncomingMessage"],
    BaseRMQInformation,
):
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
        exchange: Optional["RabbitExchange"],
        consume_args: Optional["AnyDict"],
        reply_config: Optional["ReplyConfig"],
        # Subscriber args
        no_ack: bool,
        retry: Union[bool, int],
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[IncomingMessage]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        parser = AioPikaParser(pattern=queue.path_regex)

        super().__init__(
            default_parser=parser.parse_message,
            default_decoder=parser.decode_message,
            # Propagated options
            no_ack=no_ack,
            retry=retry,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.consume_args = consume_args or {}
        self.reply_config = reply_config.to_dict() if reply_config else {}

        self._consumer_tag = None
        self._queue_obj = None

        # BaseRMQInformation
        self.queue = queue
        self.exchange = exchange
        # Setup it later
        self.app_id = None
        self.virtual_host = ""
        self.declarer = None

    @override
    def setup(  # type: ignore[override]
        self,
        *,
        app_id: Optional[str],
        virtual_host: str,
        declarer: "RabbitDeclarer",
        # basic args
        logger: Optional["LoggerProto"],
        producer: Optional["AioPikaFastProducer"],
        graceful_timeout: Optional[float],
        extra_context: "AnyDict",
        # broker options
        broker_parser: Optional["CustomCallable"],
        broker_decoder: Optional["CustomCallable"],
        # dependant args
        apply_types: bool,
        is_validate: bool,
        _get_dependant: Optional[Callable[..., Any]],
        _call_decorators: Iterable["Decorator"],
    ) -> None:
        self.app_id = app_id
        self.virtual_host = virtual_host
        self.declarer = declarer

        super().setup(
            logger=logger,
            producer=producer,
            graceful_timeout=graceful_timeout,
            extra_context=extra_context,
            broker_parser=broker_parser,
            broker_decoder=broker_decoder,
            apply_types=apply_types,
            is_validate=is_validate,
            _get_dependant=_get_dependant,
            _call_decorators=_call_decorators,
        )

    @override
    async def start(self) -> None:
        """Starts the consumer for the RabbitMQ queue."""
        if self.declarer is None:
            raise SetupError("You should setup subscriber at first.")

        self._queue_obj = queue = await self.declarer.declare_queue(self.queue)

        if self.exchange is not None:
            exchange = await self.declarer.declare_exchange(self.exchange)
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

        await super().start()

    async def close(self) -> None:
        await super().close()

        if self._queue_obj is not None:
            if self._consumer_tag is not None:  # pragma: no branch
                if not self._queue_obj.channel.is_closed:
                    await self._queue_obj.cancel(self._consumer_tag)
                self._consumer_tag = None

            self._queue_obj = None

    def _make_response_publisher(
        self,
        message: "StreamMessage[Any]",
    ) -> Sequence["FakePublisher"]:
        if not message.reply_to or self._producer is None:
            return ()

        return (
            FakePublisher(
                self._producer.publish,
                publish_kwargs={
                    **self.reply_config,
                    "routing_key": message.reply_to,
                    "app_id": self.app_id,
                },
            ),
        )

    def __hash__(self) -> int:
        return self.get_routing_hash(self.queue, self.exchange)

    @staticmethod
    def get_routing_hash(
        queue: "RabbitQueue",
        exchange: Optional["RabbitExchange"] = None,
    ) -> int:
        """Calculate the routing hash for a RabbitMQ queue and exchange."""
        return hash(queue) + hash(exchange or "")

    @staticmethod
    def build_log_context(
        message: Optional["StreamMessage[Any]"],
        queue: "RabbitQueue",
        exchange: Optional["RabbitExchange"] = None,
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

    def add_prefix(self, prefix: str) -> None:
        """Include Subscriber in router."""
        self.queue = self.queue.add_prefix(prefix)

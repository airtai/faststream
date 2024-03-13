import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from typing_extensions import Annotated, Doc

from faststream.broker.schemas import NameRequired
from faststream.rabbit.schemas.constants import ExchangeType
from faststream.utils.path import compile_path

if TYPE_CHECKING:
    from aio_pika.abc import TimeoutType

    from faststream.types import AnyDict


class RabbitQueue(NameRequired):
    """A class to represent a RabbitMQ queue."""

    __slots__ = (
        "name",
        "durable",
        "exclusive",
        "passive",
        "auto_delete",
        "arguments",
        "timeout",
        "robust",
        "routing_key",
        "path_regex",
        "bind_arguments",
    )

    def __hash__(self) -> int:
        return sum(
            (
                hash(self.name),
                int(self.durable),
                int(self.exclusive),
                int(self.auto_delete),
            )
        )

    @property
    def routing(self) -> str:
        return self.routing_key or self.name

    def __init__(
        self,
        name: Annotated[
            str,
            Doc("RabbitMQ queue name."),
        ],
        durable: Annotated[
            bool,
            Doc("Whether the object is durable."),
        ] = False,
        exclusive: Annotated[
            bool,
            Doc(
                "The queue can be used only in the current connection "
                "and will be deleted after connection closed."
            ),
        ] = False,
        passive: Annotated[
            bool,
            Doc("Do not create queue automatically."),
        ] = False,
        auto_delete: Annotated[
            bool,
            Doc("The queue will be deleted after connection closed."),
        ] = False,
        arguments: Annotated[
            Optional["AnyDict"],
            Doc(
                "Queue declarationg arguments. "
                "You can find infomration about them in the official RabbitMQ documentation: https://www.rabbitmq.com/docs/queues#optional-arguments"
            ),
        ] = None,
        timeout: Annotated[
            "TimeoutType",
            Doc("Send confirmation time from RabbitMQ."),
        ] = None,
        robust: Annotated[
            bool,
            Doc("Whether to declare queue object as restoreable."),
        ] = True,
        bind_arguments: Annotated[
            Optional["AnyDict"],
            Doc("Queue-exchange binding options."),
        ] = None,
        routing_key: Annotated[
            str,
            Doc("Explicit binding routing key. Uses `name` if not presented."),
        ] = "",
    ) -> None:
        """Initialize a class object.

        You can find information about all options in the official RabbitMQ documentation:
        https://www.rabbitmq.com/docs/queues
        """
        re, routing_key = compile_path(
            routing_key,
            replace_symbol="*",
            patch_regex=lambda x: x.replace(r"\#", ".+"),
        )

        super().__init__(name)

        self.path_regex = re
        self.durable = durable
        self.exclusive = exclusive
        self.bind_arguments = bind_arguments
        self.routing_key = routing_key
        self.robust = robust
        self.passive = passive
        self.auto_delete = auto_delete
        self.arguments = arguments
        self.timeout = timeout


class RabbitExchange(NameRequired):
    """A class to represent a RabbitMQ exchange."""

    __slots__ = (
        "name",
        "type",
        "durable",
        "auto_delete",
        "passive",
        "arguments",
        "timeout",
        "robust",
        "bind_to",
        "bind_arguments",
        "routing_key",
    )

    def __hash__(self) -> int:
        return sum(
            (
                hash(self.name),
                hash(self.type),
                hash(self.routing_key),
                int(self.durable),
                int(self.auto_delete),
            )
        )

    def __init__(
        self,
        name: Annotated[
            str,
            Doc("RabbitMQ exchange name."),
        ],
        type: Annotated[
            ExchangeType,
            Doc(
                "RabbitMQ exchange type. "
                "You can find detail information in the official RabbitMQ documentation: "
                "https://www.rabbitmq.com/tutorials/amqp-concepts#exchanges"
                "\n"
                "Or in the FastStream one: "
                "https://faststream.airt.ai/latest/rabbit/examples/"
            ),
        ] = ExchangeType.DIRECT,
        durable: Annotated[
            bool,
            Doc("Whether the object is durable."),
        ] = False,
        auto_delete: Annotated[
            bool,
            Doc("The exchange will be deleted after connection closed."),
        ] = False,
        passive: Annotated[
            bool,
            Doc("Do not create exchange automatically."),
        ] = False,
        arguments: Annotated[
            Optional["AnyDict"],
            Doc(
                "Exchange declarationg arguments. "
                "You can find usage example in the official RabbitMQ documentation: "
                "https://www.rabbitmq.com/docs/ae"
            ),
        ] = None,
        timeout: Annotated[
            "TimeoutType",
            Doc("Send confirmation time from RabbitMQ."),
        ] = None,
        robust: Annotated[
            bool,
            Doc("Whether to declare exchange object as restoreable."),
        ] = True,
        bind_to: Annotated[
            Optional["RabbitExchange"],
            Doc(
                "Another `RabbitExchange` object to bind the current one to. "
                "You can find more information in the official RabbitMQ blog post: "
                "https://www.rabbitmq.com/blog/2010/10/19/exchange-to-exchange-bindings"
            ),
        ] = None,
        bind_arguments: Annotated[
            Optional["AnyDict"],
            Doc("Exchange-exchange binding options."),
        ] = None,
        routing_key: Annotated[
            str,
            Doc("Explicit binding routing key."),
        ] = "",
    ) -> None:
        """Initialize a RabbitExchange object."""
        if routing_key and bind_to is None:  # pragma: no cover
            warnings.warn(
                (
                    "\nRabbitExchange `routing_key` is using to bind exchange to another one."
                    "\nIt can be used only with the `bind_to` argument, please setup it too."
                ),
                category=RuntimeWarning,
                stacklevel=1,
            )

        super().__init__(name)

        self.type = type
        self.durable = durable
        self.auto_delete = auto_delete
        self.robust = robust
        self.passive = passive
        self.timeout = timeout
        self.arguments = arguments

        self.bind_to = bind_to
        self.bind_arguments = bind_arguments
        self.routing_key = routing_key


@dataclass(slots=True)
class ReplyConfig:
    """Class to store a config for subscribers' replies."""

    mandatory: Annotated[
        bool,
        Doc(
            "Client waits for confimation that the message is placed to some queue. "
            "RabbitMQ returns message to client if there is no suitable queue."
        ),
    ] = True
    immediate: Annotated[
        bool,
        Doc(
            "Client expects that there is consumer ready to take the message to work. "
            "RabbitMQ returns message to client if there is no suitable consumer."
        ),
    ] = False
    persist: Annotated[
        bool,
        Doc("Restore the message on RabbitMQ reboot."),
    ] = False


@dataclass
class BaseRMQInformation:
    """Base class to store AsyncAPI RMQ bindings."""

    queue: RabbitQueue
    exchange: Optional[RabbitExchange]
    virtual_host: str
    app_id: Optional[str]

    def __init__(
        self,
        *,
        virtual_host: str,
        queue: RabbitQueue,
        exchange: Optional[RabbitExchange],
        app_id: Optional[str],
    ) -> None:
        self.virtual_host = virtual_host
        self.exchange = exchange
        self.queue = queue
        self.app_id = app_id

from copy import deepcopy
from typing import TYPE_CHECKING, Optional

from typing_extensions import Annotated, Doc

from faststream.broker.schemas import NameRequired
from faststream.utils.path import compile_path

if TYPE_CHECKING:
    from aio_pika.abc import TimeoutType

    from faststream.types import AnyDict


class RabbitQueue(NameRequired):
    """A class to represent a RabbitMQ queue.

    You can find information about all options in the official RabbitMQ documentation:

    https://www.rabbitmq.com/docs/queues
    """

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
        """Return real routing_key of object."""
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
                "You can find information about them in the official RabbitMQ documentation: https://www.rabbitmq.com/docs/queues#optional-arguments"
            ),
        ] = None,
        timeout: Annotated[
            "TimeoutType",
            Doc("Send confirmation time from RabbitMQ."),
        ] = None,
        robust: Annotated[
            bool,
            Doc("Whether to declare queue object as restorable."),
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

    def add_prefix(self, prefix: str) -> "RabbitQueue":
        new_q: RabbitQueue = deepcopy(self)

        new_q.name = "".join((prefix, new_q.name))

        if new_q.routing_key:
            new_q.routing_key = "".join((prefix, new_q.routing_key))

        return new_q

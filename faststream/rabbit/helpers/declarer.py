from typing import TYPE_CHECKING, cast

from .state import ConnectedState, ConnectionState, EmptyConnectionState

if TYPE_CHECKING:
    import aio_pika

    from faststream.rabbit.schemas import RabbitExchange, RabbitQueue


class RabbitDeclarer:
    """An utility class to declare RabbitMQ queues and exchanges."""

    def __init__(self) -> None:
        self.__queues: dict[RabbitQueue.name, aio_pika.RobustQueue] = {}
        self.__exchanges: dict[RabbitExchange.name, aio_pika.RobustExchange] = {}

        self.__connection: ConnectionState = EmptyConnectionState()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(<{self.__connection.__class__.__name__}>, queues={list(self.__queues.keys())}, exchanges={list(self.__exchanges.keys())})"

    def connect(
        self, connection: "aio_pika.RobustConnection", channel: "aio_pika.RobustChannel"
    ) -> None:
        self.__connection = ConnectedState(connection=connection, channel=channel)

    def disconnect(self) -> None:
        self.__connection = EmptyConnectionState()
        self.__queues = {}
        self.__exchanges = {}

    async def declare_queue(
        self,
        queue: "RabbitQueue",
        passive: bool = False,
    ) -> "aio_pika.RobustQueue":
        """Declare a queue."""
        if (q := self.__queues.get(queue.name)) is None:
            self.__queues[queue.name] = q = cast(
                "aio_pika.RobustQueue",
                await self.__connection.channel.declare_queue(
                    name=queue.name,
                    durable=queue.durable,
                    exclusive=queue.exclusive,
                    passive=passive or queue.passive,
                    auto_delete=queue.auto_delete,
                    arguments=queue.arguments,
                    timeout=queue.timeout,
                    robust=queue.robust,
                ),
            )
        if self.__queues[queue.name]==q:
            return q
        else:
            raise ValueError("Queue mismatch")

    async def declare_exchange(
        self,
        exchange: "RabbitExchange",
        passive: bool = False,
    ) -> "aio_pika.RobustExchange":
        """Declare an exchange, parent exchanges and bind them each other."""
        if not exchange.name:
            return self.__connection.channel.default_exchange

        if (exch := self.__exchanges.get(exchange.name)) is None:
            self.__exchanges[exchange.name] = exch = cast(
                "aio_pika.RobustExchange",
                await self.__connection.channel.declare_exchange(
                    name=exchange.name,
                    type=exchange.type.value,
                    durable=exchange.durable,
                    auto_delete=exchange.auto_delete,
                    passive=passive or exchange.passive,
                    arguments=exchange.arguments,
                    timeout=exchange.timeout,
                    robust=exchange.robust,
                    internal=False,  # deprecated RMQ option
                ),
            )

            if exchange.bind_to is not None:
                parent = await self.declare_exchange(exchange.bind_to)
                await exch.bind(
                    exchange=parent,
                    routing_key=exchange.routing,
                    arguments=exchange.bind_arguments,
                    timeout=exchange.timeout,
                    robust=exchange.robust,
                )
        if self.__exchanges[exchange.name]==exch:
            return exch
        else:
            raise ValueError("Exchange mismatch")
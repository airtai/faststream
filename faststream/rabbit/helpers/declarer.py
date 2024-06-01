from typing import TYPE_CHECKING, Dict, cast

if TYPE_CHECKING:
    import aio_pika

    from faststream.rabbit.schemas import RabbitExchange, RabbitQueue


class RabbitDeclarer:
    """An utility class to declare RabbitMQ queues and exchanges."""

    __channel: "aio_pika.RobustChannel"
    __queues: Dict["RabbitQueue", "aio_pika.RobustQueue"]
    __exchanges: Dict["RabbitExchange", "aio_pika.RobustExchange"]

    def __init__(self, channel: "aio_pika.RobustChannel") -> None:
        self.__channel = channel
        self.__queues = {}
        self.__exchanges = {}

    async def declare_queue(
        self,
        queue: "RabbitQueue",
        passive: bool = False,
    ) -> "aio_pika.RobustQueue":
        """Declare a queue."""
        if (q := self.__queues.get(queue)) is None:
            self.__queues[queue] = q = cast(
                "aio_pika.RobustQueue",
                await self.__channel.declare_queue(
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

        return q

    async def declare_exchange(
        self,
        exchange: "RabbitExchange",
        passive: bool = False,
    ) -> "aio_pika.RobustExchange":
        """Declare an exchange, parent exchanges and bind them each other."""
        if not exchange.name:
            return self.__channel.default_exchange

        if (exch := self.__exchanges.get(exchange)) is None:
            self.__exchanges[exchange] = exch = cast(
                "aio_pika.RobustExchange",
                await self.__channel.declare_exchange(
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

        return exch

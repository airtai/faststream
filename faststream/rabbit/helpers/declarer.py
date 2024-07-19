from contextlib import AsyncExitStack, asynccontextmanager
from typing import TYPE_CHECKING, AsyncGenerator, Dict, Optional, Tuple, cast

if TYPE_CHECKING:
    import aio_pika

    from faststream.rabbit.broker.connection import ConnectionManager
    from faststream.rabbit.schemas import RabbitExchange, RabbitQueue


class RabbitDeclarer:
    """An utility class to declare RabbitMQ queues and exchanges."""

    __connection_manager: "ConnectionManager"
    __queues: Dict[
        Tuple[Optional["aio_pika.RobustChannel"], "RabbitQueue"], "aio_pika.RobustQueue"
    ]
    __exchanges: Dict[
        Tuple[Optional["aio_pika.RobustChannel"], "RabbitExchange"],
        "aio_pika.RobustExchange",
    ]

    def __init__(self, connection_manager: "ConnectionManager") -> None:
        self.__connection_manager = connection_manager
        self.__queues = {}
        self.__exchanges = {}

    async def declare_queue(
        self,
        queue: "RabbitQueue",
        passive: bool = False,
        *,
        channel: Optional["aio_pika.RobustChannel"] = None,
    ) -> "aio_pika.RobustQueue":
        """Declare a queue."""
        # NOTE: It would return the queue linked to another channel if it was already declared
        # unless the channel is part of the key
        if (queue_obj := self.__queues.get((channel, queue))) is None:
            async with AsyncExitStack() as stack:
                if channel is None:
                    channel = await stack.enter_async_context(
                        self.__connection_manager.acquire_channel()
                    )
                    if (channel, queue) in self.__queues:
                        return self.__queues[(channel, queue)]

                self.__queues[(channel, queue)] = queue_obj = cast(
                    "aio_pika.RobustQueue",
                    await channel.declare_queue(
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

        return queue_obj  # type: ignore[return-value]

    async def declare_exchange(
        self,
        exchange: "RabbitExchange",
        passive: bool = False,
        *,
        channel: Optional["aio_pika.RobustChannel"] = None,
    ) -> "aio_pika.RobustExchange":
        """Declare an exchange, parent exchanges and bind them each other."""
        # NOTE: It would return the queue linked to another channel if it was already declared
        # unless the channel is part of the key
        if exch := self.__exchanges.get((channel, exchange)):
            return exch

        async with AsyncExitStack() as stack:
            if channel is None:
                channel = await stack.enter_async_context(
                    self.__connection_manager.acquire_channel()
                )
                if (channel, exchange) in self.__exchanges:
                    return self.__exchanges[(channel, exchange)]

            if not exchange.name:
                return channel.default_exchange

            else:
                self.__exchanges[(channel, exchange)] = exch = cast(
                    "aio_pika.RobustExchange",
                    await channel.declare_exchange(
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
                    parent = await self.declare_exchange(
                        exchange.bind_to,
                        channel=channel,
                    )

                    await exch.bind(
                        exchange=parent,
                        routing_key=exchange.routing,
                        arguments=exchange.bind_arguments,
                        timeout=exchange.timeout,
                        robust=exchange.robust,
                    )

        return exch  # type: ignore[return-value]

    @asynccontextmanager
    async def declare_queue_scope(
        self,
        queue: "RabbitQueue",
        passive: bool = False,
        *,
        channel: Optional["aio_pika.RobustChannel"] = None,
    ) -> AsyncGenerator["aio_pika.RobustQueue", None]:
        """Declare a queue and return it with a context manager."""
        async with AsyncExitStack() as stack:
            if channel is None:
                channel = await stack.enter_async_context(
                    self.__connection_manager.acquire_channel()
                )

            yield await self.declare_queue(
                queue=queue, passive=passive, channel=channel
            )

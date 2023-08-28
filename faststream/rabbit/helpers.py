from typing import Dict, Union, cast

import aio_pika

from faststream._compat import model_to_dict
from faststream.rabbit.shared.schemas import RabbitExchange, RabbitQueue
from faststream.utils.classes import Singleton


class RabbitDeclarer(Singleton):
    channel: aio_pika.RobustChannel
    queues: Dict[Union[RabbitQueue, str], aio_pika.RobustQueue]
    exchanges: Dict[Union[RabbitExchange, str], aio_pika.RobustExchange]

    def __init__(self, channel: aio_pika.RobustChannel) -> None:
        self.channel = channel
        self.queues = {}
        self.exchanges = {}

    async def declare_queue(
        self,
        queue: RabbitQueue,
    ) -> aio_pika.RobustQueue:
        q = self.queues.get(queue)
        if q is None:
            q = cast(
                aio_pika.RobustQueue,
                await self.channel.declare_queue(
                    **model_to_dict(queue, exclude={"routing_key"})
                ),
            )
            self.queues[queue] = q
        return q

    async def declare_exchange(
        self,
        exchange: RabbitExchange,
    ) -> aio_pika.RobustExchange:
        exch = self.exchanges.get(exchange)

        if exch is None:
            exch = cast(
                aio_pika.RobustExchange,
                await self.channel.declare_exchange(**model_to_dict(exchange)),
            )
            self.exchanges[exchange] = exch

        if exchange.bind_to is not None:
            parent = await self.declare_exchange(exchange.bind_to)
            await exch.bind(
                exchange=parent,
                routing_key=exchange.routing_key,
                arguments=exchange.arguments,
            )

        return exch

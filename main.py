from faststream.redis import RedisBroker
from faststream.kafka import KafkaBroker
from faststream.rabbit import RabbitBroker
from faststream.nats import NatsBroker
import asyncio


async def main():
    async with NatsBroker() as redis:
        await redis.connect(servers=234234)

if __name__ == '__main__':
    asyncio.run(main())

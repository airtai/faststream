import asyncio
import ssl

from faststream.broker.security import SASLScram256
from faststream.kafka import KafkaBroker

ssl_context = ssl.create_default_context()
security = SASLScram256(ssl_context=ssl_context, username="admin", password="")

broker = KafkaBroker("kafka.staging.airt.ai:9092", security=security)


async def send_msg():
    async with broker:
        await broker.start()
        await broker.publish("HI!", "testinstallation")


asyncio.run(send_msg())

import ssl

from faststream import FastStream, Logger
from faststream.broker.security import BaseSecurity
from faststream.kafka import KafkaBroker

ssl_context = ssl.create_default_context()
security = BaseSecurity(ssl_context=ssl_context)

broker = KafkaBroker("localhost:9092", security=security)
app = FastStream(broker)


@broker.subscriber("testinstallation")
async def handle_msg(msg: bytes, logger: Logger):
    logger.info(msg)

import ssl

from faststream import FastStream, Logger
from faststream.broker.security import SASLScram256
from faststream.kafka import KafkaBroker

ssl_context = ssl.create_default_context()
security = SASLScram256(ssl_context=ssl_context, username="admin", password="")

broker = KafkaBroker("kafka.staging.airt.ai:9092", security=security)
app = FastStream(broker)


@broker.subscriber("testinstallation")
async def handle_batch(msg: bytes, logger: Logger):
    logger.info(msg)

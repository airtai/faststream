import ssl
from typing import List

from faststream import FastStream, Logger
from faststream.broker.security import BaseSecurity
from faststream.kafka import KafkaBroker

ssl_context = ssl.create_default_context()
# security = SASLPlaintext(username="abc", password="123", use_ssl=False)
# security = SASLScram512(ssl_context=ssl_context, username="abc", password="123")
# security = SASLScram256(ssl_context=ssl_context, username="abc", password="123")
security = BaseSecurity(ssl_context=ssl_context)

broker = KafkaBroker("localhost:9092", security=security)
app = FastStream(broker)


@broker.subscriber("test_batch", batch=True)
async def handle_batch(msg: List[str], logger: Logger):
    logger.info(msg)

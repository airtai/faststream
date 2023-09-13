import ssl

from faststream import FastStream
from faststream.broker.security import BaseSecurity
from faststream.kafka import KafkaBroker

ssl_context = ssl.create_default_context()
security = BaseSecurity(ssl_context=ssl_context)

broker = KafkaBroker("localhost:9092", security=security)
app = FastStream(broker)


@broker.publisher("test_2")
@broker.subscriber("test_1")
async def test_topic(msg: str) -> str:
    pass

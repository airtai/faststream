import ssl

from faststream import FastStream
from faststream.redis import RedisBroker
from faststream.security import SASLPlaintext

ssl_context = ssl.create_default_context()
security = SASLPlaintext(ssl_context=ssl_context, username="admin", password="password")

broker = RedisBroker(security=security)
app = FastStream(broker)


@broker.publisher("test_2")
@broker.subscriber("test_1")
async def test_topic(msg: str) -> str:
    pass

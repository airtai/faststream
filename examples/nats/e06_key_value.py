from nats.js.kv import KeyValue as KV
from typing_extensions import Annotated

from faststream import Context, FastStream, Logger
from faststream.nats import NatsBroker
from faststream.nats.annotations import ContextRepo

KeyValue = Annotated[KV, Context("kv")]

broker = NatsBroker()
app = FastStream(broker)


@broker.subscriber("subject")
async def handler(msg: str, kv: KeyValue, logger: Logger):
    logger.info(msg)
    kv_data = await kv.get("key")
    assert kv_data.value == b"Hello!"


@app.on_startup
async def setup_broker(context: ContextRepo):
    await broker.connect()

    kv = await broker.stream.create_key_value(bucket="bucket")
    context.set_global("kv", kv)


@app.after_startup
async def test_send(kv: KeyValue):
    await kv.put("key", b"Hello!")
    await broker.publish("Hi!", "subject")

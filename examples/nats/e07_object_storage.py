from io import BytesIO

from nats.js.object_store import ObjectStore as OS
from typing_extensions import Annotated

from faststream import Context, FastStream, Logger
from faststream.nats import NatsBroker
from faststream.nats.annotations import ContextRepo

ObjectStorage = Annotated[OS, Context("OS")]

broker = NatsBroker()
app = FastStream(broker)


@broker.subscriber("subject")
async def handler(msg: str, os: ObjectStorage, logger: Logger):
    logger.info(msg)
    obj = await os.get("file")
    assert obj.data == b"File mock"


@app.on_startup
async def setup_broker(context: ContextRepo):
    await broker.connect()

    os = await broker.stream.create_object_store("bucket")
    context.set_global("OS", os)


@app.after_startup
async def test_send(os: ObjectStorage):
    await os.put("file", BytesIO(b"File mock"))

    await broker.publish("Hi!", "subject")

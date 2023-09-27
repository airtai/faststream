from faststream import FastStream, Logger
from faststream.nats import JsStream, NatsBroker

broker = NatsBroker()
app = FastStream(broker)

stream = JsStream(name="stream")


@broker.subscriber("core-subject")
async def core_handler(msg: str, logger: Logger):
    logger.info(msg)


@broker.subscriber("js-subject", stream=stream)
async def js_handler(msg: str, logger: Logger):
    logger.info(msg)


@app.after_startup
async def test_send():
    await broker.publish("Hi!", "core-subject")
    await broker.publish("Hi!", "js-subject", stream="stream")

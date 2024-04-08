from faststream import FastStream, Logger
from faststream.nats import NatsBroker

broker = NatsBroker()
app = FastStream(broker)

@broker.subscriber("test")
async def handler(msg, logger: Logger):
    logger.info(msg)

@app.after_startup
async def t():
    await broker.publish("test", "test")
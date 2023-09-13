import msgpack

from faststream import FastStream, Logger
from faststream.rabbit import RabbitBroker, RabbitMessage

broker = RabbitBroker()
app = FastStream(broker)


async def decode_message(msg: RabbitMessage):
    return msgpack.loads(msg.body)


@broker.subscriber("test", decoder=decode_message)
async def consume(body, logger: Logger):
    logger.info(body)


@app.after_startup
async def publish():
    body = msgpack.dumps({"name": "john", "age": 25}, use_bin_type=True)
    await broker.publish(body, "test")

from faststream import FastStream, Logger
from faststream.redis import RedisBroker

broker = RedisBroker()
app = FastStream(broker)


@broker.subscriber(channel="test-channel")
async def handle_channel(msg: str, logger: Logger):
    logger.info(msg)
    return msg


@broker.subscriber(list="test-list")
async def handle_list(msg: str, logger: Logger):
    logger.info(msg)
    return msg


@broker.subscriber(stream="test-stream")
async def handle_stream(msg: str, logger: Logger):
    logger.info(msg)
    return msg


@app.after_startup
async def t():
    msg = "Hi!"

    assert msg == await broker.publish(
        "Hi!",
        channel="test-channel",
        rpc=True,
        rpc_timeout=3.0,
    )

    assert msg == await broker.publish(
        "Hi!",
        list="test-list",
        rpc=True,
        rpc_timeout=3.0,
    )

    assert msg == await broker.publish(
        "Hi!",
        stream="test-stream",
        rpc=True,
        rpc_timeout=3.0,
    )

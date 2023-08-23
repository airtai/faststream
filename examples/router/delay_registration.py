from propan import Logger, PropanApp
from propan.kafka import KafkaBroker, KafkaRoute, KafkaRouter


async def handle(msg: str, logger: Logger) -> None:
    logger.info(msg)


router = KafkaRouter(
    "prefix_",
    handlers=(KafkaRoute(handle, "in"),),
)

broker = KafkaBroker("localhost:9092")
broker.include_router(router)

app = PropanApp(broker)


@app.after_startup
async def test() -> None:
    await broker.publish("Hello!", "prefix_in")

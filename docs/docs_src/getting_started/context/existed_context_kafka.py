from faststream import Context, FastStream
from faststream.kafka import KafkaBroker
from faststream.kafka.annotations import (
    ContextRepo,
    KafkaMessage,
    Logger,
)
from faststream.kafka.annotations import (
    KafkaBroker as BrokerAnnotation,
)

broker_object = KafkaBroker("localhost:9092")
app = FastStream(broker_object)


@broker_object.subscriber("test-topic")
async def handle(
    msg: str,
    logger=Context(),
    message=Context(),
    broker=Context(),
    context=Context(),
):
    logger.info(msg)
    context.set_global("correlation_id", message.correlation_id)

    await broker.publish(
        "Hi!",
        topic="response-topic",
        correlation_id=message.correlation_id,
    )


@broker_object.subscriber("response-topic")
async def handle_response(
    msg: str,
    logger: Logger,
    message: KafkaMessage,
    context: ContextRepo,
    correlation_id=Context(),
):
    logger.info(msg)

    assert msg == "Hi!"
    assert correlation_id == message.correlation_id == context.get("correlation_id")


@app.after_startup
async def test(broker: BrokerAnnotation):
    await broker.publish("Hi!", "test-topic")

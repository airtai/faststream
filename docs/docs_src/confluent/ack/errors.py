from faststream import FastStream
from faststream.exceptions import AckMessage
from faststream.confluent import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.subscriber(
    "test-error-topic", group_id="test-error-group", auto_commit=False, auto_offset_reset="earliest"
)
async def handle(body):
    smth_processing(body)


def smth_processing(body):
    if True:
        raise AckMessage()


@app.after_startup
async def test_publishing():
    await broker.publish("Hello!", "test-error-topic")

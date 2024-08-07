from faststream import FastStream
from faststream.confluent import KafkaBroker

broker = KafkaBroker()
app = FastStream(broker)


@broker.subscriber("test-confluent-topic", auto_offset_reset="earliest")
async def handle(msg: str):
    assert msg == "Hi!"


@app.after_startup
async def test():
    async with KafkaBroker() as br:
        await br.publish("Hi!", topic="test-confluent-topic")

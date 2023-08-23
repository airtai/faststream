from propan import PropanApp
from propan.exceptions import AckMessage
from propan.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = PropanApp(broker)


@broker.subscriber("test-queue")
async def handle(body):
    smth_processing(body)


def smth_processing(body):
    if True:
        # interrupt msg processing and ack it
        raise AckMessage()
    ...


@app.after_startup
async def test_publishing():
    await broker.publish("Hello!", "test-queue")

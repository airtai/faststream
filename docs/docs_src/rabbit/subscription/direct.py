from faststream import FastStream, Logger
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue

broker = RabbitBroker()
app = FastStream(broker)

exch = RabbitExchange("exchange", auto_delete=True)

queue_1 = RabbitQueue("test-q-1", auto_delete=True)
queue_2 = RabbitQueue("test-q-2", auto_delete=True)


@broker.subscriber(queue_1, exch)
async def base_handler1(logger: Logger):
    logger.info("base_handler1")


@broker.subscriber(queue_1, exch)
async def base_handler2(logger: Logger):
    logger.info("base_handler2")


@broker.subscriber(queue_2, exch)
async def base_handler3(logger: Logger):
    logger.info("base_handler3")


@app.after_startup
async def send_messages():
    await broker.publish(queue="test-q-1", exchange=exch)  # handlers: 1
    await broker.publish(queue="test-q-1", exchange=exch)  # handlers: 2
    await broker.publish(queue="test-q-1", exchange=exch)  # handlers: 1
    await broker.publish(queue="test-q-2", exchange=exch)  # handlers: 3

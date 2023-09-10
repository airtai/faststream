from faststream import FastStream
from faststream.rabbit import RabbitBroker

from config import setting

broker = RabbitBroker(settings.url)
app = FastStream(broker)

@broker.handle(settings.queue)
async def handler(msg):
    ...
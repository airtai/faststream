from faststream import FastStream
from faststream.rabbit import RabbitBroker

broker = RabbitBroker()
app = FastStream(broker)

@app.after_startup
async def _():
    raise ValueError

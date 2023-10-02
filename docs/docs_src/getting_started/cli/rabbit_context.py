from faststream import FastStream, ContextRepo
from faststream.rabbit import RabbitBroker
from pydantic_settings import BaseSettings

broker = RabbitBroker()

app = FastStream(broker)

class Settings(BaseSettings):
    host: str = "amqp://guest:guest@localhost:5672/"

@app.on_startup
async def setup(env: str, context: ContextRepo):
    settings = Settings(_env_file=env)
    await broker.connect(settings.host)
    context.set_global("settings", settings)

from faststream import FastStream, ContextRepo
from faststream.kafka import KafkaBroker
from pydantic_settings import BaseSettings

broker = KafkaBroker()

app = FastStream(broker)

class Settings(BaseSettings):
    host: str = "localhost:9092"

@app.on_startup
async def setup(env: str, context: ContextRepo):
    settings = Settings(_env_file=env)
    await broker.connect(settings.host)
    context.set_global("settings", settings)

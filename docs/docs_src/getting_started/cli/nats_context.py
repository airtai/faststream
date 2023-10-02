from faststream import FastStream, ContextRepo
from faststream.nats import NatsBroker
from pydantic_settings import BaseSettings

broker = NatsBroker()

app = FastStream(broker)

class Settings(BaseSettings):
    host: str = "nats://localhost:4222"

@app.on_startup
async def setup(env: str, context: ContextRepo):
    settings = Settings(_env_file=env)
    await broker.connect(settings.host)
    context.set_global("settings", settings)

from fastapi import FastAPI
from faststream.nats.fastapi import NatsRouter

core_router = NatsRouter()
nested_router = NatsRouter()

@core_router.subscriber("core-subject")
async def handler():
    ...

@nested_router.subscriber("nested-subject")
async def nested_handler():
    ...

core_router.include_router(nested_router)

app = FastAPI()
app.include_router(core_router)

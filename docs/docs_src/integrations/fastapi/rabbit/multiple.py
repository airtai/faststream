from fastapi import FastAPI
from faststream.rabbit.fastapi import RabbitRouter

core_router = RabbitRouter()
nested_router = RabbitRouter()

@core_router.subscriber("core-queue")
async def handler():
    ...

@nested_router.subscriber("nested-queue")
async def nested_handler():
    ...

core_router.include_router(nested_router)

app = FastAPI()
app.include_router(core_router)

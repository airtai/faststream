from contextlib import asynccontextmanager

from fastapi import FastAPI
from faststream.confluent.fastapi import KafkaRouter

core_router = KafkaRouter()
nested_router = KafkaRouter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with (
        core_router.lifespan_context(app),
        nested_router.lifespan_context(app),
    ):
        yield

app = FastAPI(lifespan=lifespan)
app.include_router(core_router)
app.include_router(nested_router)

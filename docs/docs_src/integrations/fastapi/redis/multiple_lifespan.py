from contextlib import asynccontextmanager

from fastapi import FastAPI
from faststream.redis.fastapi import RedisRouter

core_router = RedisRouter()
nested_router = RedisRouter()

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

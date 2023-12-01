from fastapi import FastAPI

from faststream.redis.fastapi import RedisRouter

router = RedisRouter("redis://localhost:6379")

app = FastAPI(lifespan=router.lifespan_context)


@router.get("/")
async def hello_http():
    await router.broker.publish("Hello, Redis!", "test")
    return "Hello, HTTP!"


app.include_router(router)

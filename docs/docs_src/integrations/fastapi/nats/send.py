from fastapi import FastAPI

from faststream.nats.fastapi import NatsRouter

router = NatsRouter("nats://localhost:4222")

app = FastAPI(lifespan=router.lifespan_context)


@router.get("/")
async def hello_http():
    await router.broker.publish("Hello, NATS!", "test")
    return "Hello, HTTP!"


app.include_router(router)

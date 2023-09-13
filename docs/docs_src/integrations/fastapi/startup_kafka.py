from fastapi import FastAPI

from faststream.kafka.fastapi import KafkaRouter

router = KafkaRouter("localhost:9092")


@router.subscriber("test")
async def hello(msg: str):
    return {"response": "Hello, world!"}


@router.after_startup
async def test(app: FastAPI):
    await router.broker.publish("Hello!", "test")


app = FastAPI(lifespan=router.lifespan_context)
app.include_router(router)

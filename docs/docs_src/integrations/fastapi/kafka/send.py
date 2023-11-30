from fastapi import FastAPI

from faststream.kafka.fastapi import KafkaRouter

router = KafkaRouter("localhost:9092")

app = FastAPI(lifespan=router.lifespan_context)


@router.get("/")
async def hello_http():
    await router.broker.publish("Hello, Kafka!", "test")
    return "Hello, HTTP!"


app.include_router(router)

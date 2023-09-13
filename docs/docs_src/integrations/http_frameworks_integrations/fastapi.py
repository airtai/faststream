from contextlib import asynccontextmanager

from fastapi import FastAPI

from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")

app = FastAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.start()
    yield
    await broker.close()


@broker.subscriber("test")
async def base_handler(body):
    print(body)


@app.get("/")
def read_root():
    return {"Hello": "World"}

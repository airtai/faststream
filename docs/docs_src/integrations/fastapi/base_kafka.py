from fastapi import Depends, FastAPI
from pydantic import BaseModel

from faststream.kafka.fastapi import KafkaRouter

router = KafkaRouter("localhost:9092")


class Incoming(BaseModel):
    m: dict


def call():
    return True


@router.subscriber("test")
@router.publisher("response")
async def hello(m: Incoming, d=Depends(call)):
    return {"response": "Hello, world!"}


@router.get("/")
async def hello_http():
    return "Hello, http!"


app = FastAPI(lifespan=router.lifespan_context)
app.include_router(router)

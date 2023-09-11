from fastapi import Depends, FastAPI
from pydantic import BaseModel

from faststream.rabbit.fastapi import RabbitRouter

router = RabbitRouter("amqp://guest:guest@localhost:5672/")


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

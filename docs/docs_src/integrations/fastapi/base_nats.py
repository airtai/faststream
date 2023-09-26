from fastapi import Depends, FastAPI
from pydantic import BaseModel

from faststream.nats.fastapi import NatsRouter

router = NatsRouter("nats://localhost:4222")


class Incoming(BaseModel):
    m: dict


def call():
    return True


@router.subscriber("test")
@router.publisher("response")
async def hello(m: Incoming, d=Depends(call)):
    return {"response": "Hello, NATS!"}


@router.get("/")
async def hello_http():
    return "Hello, http!"


app = FastAPI(lifespan=router.lifespan_context)
app.include_router(router)

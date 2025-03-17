from fastapi import Depends, FastAPI
from pydantic import BaseModel

from faststream.nats.fastapi import NatsRouter, Logger

router = NatsRouter("nats://localhost:4222")

class Incoming(BaseModel):
    m: dict

def call():
    return True

@router.subscriber("test")
@router.publisher("response")
async def hello(m: Incoming, logger: Logger, d=Depends(call)):
    logger.info("%s", m)
    return {"response": "Hello, NATS!"}

@router.get("/")
async def hello_http():
    return "Hello, HTTP!"

app = FastAPI()
app.include_router(router)

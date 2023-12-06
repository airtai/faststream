from fastapi import Depends, FastAPI
from pydantic import BaseModel

from faststream.redis.fastapi import RedisRouter

router = RedisRouter("redis://localhost:6379")


class Incoming(BaseModel):
    m: dict


def call():
    return True


@router.subscriber("test")
@router.publisher("response")
async def hello(m: Incoming, d=Depends(call)):
    return {"response": "Hello, Redis!"}


@router.get("/")
async def hello_http():
    return "Hello, HTTP!"


app = FastAPI(lifespan=router.lifespan_context)
app.include_router(router)

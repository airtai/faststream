from fastapi import FastAPI
from faststream.redis.fastapi import RedisRouter

one_router = RedisRouter()
another_router = RedisRouter()

...

app = FastAPI()
app.include_router(one_router)
app.include_router(another_router)

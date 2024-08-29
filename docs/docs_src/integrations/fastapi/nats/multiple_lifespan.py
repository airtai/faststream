from fastapi import FastAPI
from faststream.nats.fastapi import NatsRouter

one_router = NatsRouter()
another_router = NatsRouter()

...

app = FastAPI()
app.include_router(one_router)
app.include_router(another_router)

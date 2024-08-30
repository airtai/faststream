from fastapi import FastAPI
from faststream.rabbit.fastapi import RabbitRouter

one_router = RabbitRouter()
another_router = RabbitRouter()

...

app = FastAPI()
app.include_router(one_router)
app.include_router(another_router)

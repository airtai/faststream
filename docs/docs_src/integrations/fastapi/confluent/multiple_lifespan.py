from fastapi import FastAPI
from faststream.confluent.fastapi import KafkaRouter

one_router = KafkaRouter()
another_router = KafkaRouter()

...

app = FastAPI()
app.include_router(one_router)
app.include_router(another_router)

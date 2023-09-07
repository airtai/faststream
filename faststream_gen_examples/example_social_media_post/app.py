from pydantic import BaseModel, Field, NonNegativeInt

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class Post(BaseModel):
    user_id: NonNegativeInt = Field(..., examples=[1], description="Int data example")
    text: str = Field(..., examples=["Just another day"], description="text example")
    number_of_likes: NonNegativeInt = Field(
        ..., examples=[1], description="Int data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.publisher("just_text")
@broker.subscriber("popular_post")
async def on_popular_post(msg: Post, logger: Logger) -> str:
    logger.info(msg)
    return msg.text


to_popular_post = broker.publisher("popular_post")


@broker.subscriber("new_post")
async def on_new_post(msg: Post, logger: Logger) -> None:
    logger.info(msg)

    if msg.number_of_likes > 10:
        await to_popular_post.publish(msg)

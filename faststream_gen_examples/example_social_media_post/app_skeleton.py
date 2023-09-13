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
    """
    Processes a message from the 'popular_post' topic.
    Publishes the text attribute of the post to the 'just_text' topic

    Instructions:
    1. Consume a message from 'popular_post' topic.
    2. Publishes the text attribute of the post to the 'just_text' topic

    """
    raise NotImplementedError()


to_popular_post = broker.publisher("popular_post")


@broker.subscriber("new_post")
async def on_new_post(msg: Post, logger: Logger) -> None:
    """
    Processes a message from the 'new_post' topic.
    Upon reception, the function should check if the number_of_likes attribute is grater then 10. If yes, retrieve the current message to the 'popular_post' topic.

    Instructions:
    1. Consume a message from 'new_post' topic.
    2. Check if the number_of_likes attribute is grater then 10.
    3. If 2. is True, retrieve the current message to the 'popular_post' topic.

    """
    raise NotImplementedError()

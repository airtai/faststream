from datetime import datetime

from pydantic import BaseModel, Field, NonNegativeInt

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class ProductReview(BaseModel):
    product_id: NonNegativeInt = Field(
        ..., examples=[1], description="Int data example"
    )
    customer_id: NonNegativeInt = Field(
        ..., examples=[1], description="Int data example"
    )
    review_grade: NonNegativeInt = Field(
        ..., examples=[1], description="Int data example"
    )
    timestamp: datetime = Field(
        ...,
        examples=["2020-04-23 10:20:30.400000"],
        description="The timestamp of the record",
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

to_customer_service = broker.publisher("customer_service")


@broker.subscriber("product_reviews")
async def on_product_reviews(msg: ProductReview, logger: Logger) -> None:
    logger.info(msg)

    if msg.review_grade < 5:
        await to_customer_service.publish(msg)

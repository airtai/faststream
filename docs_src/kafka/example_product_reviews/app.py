"""
Create a FastStream application using the localhost broker. 
The application should consume from the 'product_reviews' topic which includes JSON encoded objects with attributes: product_id, customer_id and review_grade. 
If the review_grade attribute is smaller then 5, send an alert message to the 'customer_service' topic. No authentication is needed for this function.
"""

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


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

to_customer_service = broker.publisher("customer_service")

@broker.subscriber("product_reviews")
async def on_product_reviews(msg: ProductReview, logger: Logger) -> None:
    logger.info(msg)

    if msg.review_grade < 5:
        await to_customer_service.publish(msg)

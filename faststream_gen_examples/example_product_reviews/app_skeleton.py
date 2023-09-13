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
    """
    Consumes a message from the 'product_reviews' topic.
    Upon reception, the function should verify if the review_grade attribute is smaller then 5. If yes, publish alert message to the 'customer_service' topic.

    Instructions:
    1. Consume a message from 'product_reviews' topic.
    2. Create a new message object (do not directly modify the original).
    3. Check if the review_grade attribute is smaller then 5.
    4. If 3. is True, publish alert message to the 'customer_service' topic.

    """
    raise NotImplementedError()

import os
import ssl

from pydantic import BaseModel, Field

from faststream import FastStream, Logger
from faststream.broker.security import SASLScram512
from faststream.kafka import KafkaBroker


class Student(BaseModel):
    name: str = Field(..., examples=["Student Studentis"], description="Name example")
    age: int = Field(
        ...,
        examples=[
            20,
        ],
        description="Student age",
    )


ssl_context = ssl.create_default_context()
security = SASLScram512(
    ssl_context=ssl_context,
    username=os.environ["USERNAME"],
    password=os.environ["PASSWORD"],
)

broker = KafkaBroker("localhost:9092", security=security)
app = FastStream(broker)

to_class = broker.publisher("class")


@broker.subscriber("student_application")
async def on_application(msg: Student, logger: Logger) -> None:
    await to_class.publish(msg)

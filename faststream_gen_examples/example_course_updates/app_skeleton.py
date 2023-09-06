from typing import Optional

from pydantic import BaseModel, Field

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class CourseUpdates(BaseModel):
    course_name: str = Field(..., examples=["Biology"], description="Course example")
    new_content: Optional[str] = Field(
        default=None, examples=["New content"], description="Content example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.publisher("notify_updates")
@broker.subscriber("course_updates")
async def on_course_update(msg: CourseUpdates, logger: Logger) -> CourseUpdates:
    """
    Processes a message from the 'course_updates' topic, If new_content attribute is set, then constructs a new message appending 'Updated: ' before the course_name attribute.
    Finally, publishes the message to the 'notify_updates' topic.

    Instructions:
    1. Consume a message from 'course_updates' topic.
    2. Create a new message object (do not directly modify the original).
    3. Processes a message from the 'course_updates' topic, If new_content attribute is set, then constructs a new message appending 'Updated: ' before the course_name attribute.
    4. Publish the modified message to 'notify_updates' topic.

    """
    raise NotImplementedError()

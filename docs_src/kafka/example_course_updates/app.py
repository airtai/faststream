"""
Develop a FastStream application using localhost broker for testing, staging.example.ai for staging and prod.example.ai for production.
It should consume messages from 'course_updates' topic where the message is a JSON encoded object including two attributes: course_name and new_content. 
If new_content attribute is set, then construct a new message appending 'Updated: ' before the course_name attribute. 
Finally, publish this message to the 'notify_updates' topic. The application should use SASL_SSL with SCRAM-SHA-512 for authentication.
"""

from pydantic import BaseModel, Field

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker
from typing import Optional


class CourseUpdates(BaseModel):
    course_name: str = Field(
        ..., examples=["Biology"], description="Course example"
    )
    new_content: Optional[str] = Field(
        default=None, examples=["New content"], description="Content example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.publisher("notify_update")
@broker.subscriber("course_updates")
async def on_course_update(msg: CourseUpdates, logger: Logger) -> CourseUpdates:
    logger.info(msg)

    if msg.new_content:
        logger.info(f"Course has new content {msg.new_content=}")
        msg = CourseUpdates(course_name=("Updated: " + msg.course_name), new_content=msg.new_content)
    return msg

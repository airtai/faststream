from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class CourseUpdates(BaseModel):
    course_name: str = Field(..., examples=["Biology"], description="Course example")
    new_content: Optional[str] = Field(
        default=None, examples=["New content"], description="Content example"
    )
    timestamp: datetime = Field(
        ...,
        examples=["2020-04-23 10:20:30.400000"],
        description="The timestamp of the record",
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.publisher("notify_updates")
@broker.subscriber("course_updates")
async def on_course_update(msg: CourseUpdates, logger: Logger) -> CourseUpdates:
    logger.info(msg)

    if msg.new_content:
        logger.info(f"Course has new content {msg.new_content=}")
        msg = CourseUpdates(
            course_name=("Updated: " + msg.course_name),
            new_content=msg.new_content,
            timestamp=datetime.now(),
        )
    return msg

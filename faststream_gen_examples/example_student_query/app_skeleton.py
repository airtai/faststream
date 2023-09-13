from pydantic import BaseModel, Field, NonNegativeInt

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class StudentQuery(BaseModel):
    student_id: NonNegativeInt = Field(
        ..., examples=[1], description="Int data example"
    )
    department: str = Field(
        ..., examples=["axademic_department"], description="Department example"
    )
    query: str = Field(
        ..., examples=["Please help me with..."], description="Query example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

to_finance_department = broker.publisher("finance_department")
to_academic_department = broker.publisher("academic_department")
to_admissions_department = broker.publisher("admissions_department")
to_unclassified_query = broker.publisher("unclassified_query")


@broker.subscriber("student_query")
async def on_student_query(msg: StudentQuery, logger: Logger) -> None:
    """
    Processes a message from the 'student_query'.
    Each query should then be forwarded to the corresponding department based on the department attribute.
    The relevant department topics could be 'finance_department', 'academic_department', or 'admissions_department'.
    If department is not one of these topics, forward the message to the 'unclassified_query' topic.

    Instructions:
    1. Consume a message from 'student_query' topic.
    2. Check the department attribute - The relevant department topics could be 'finance_department', 'academic_department', or 'admissions_department'.
    3. If departman is one of the relevant departments, forward the message to that topic. Otherwise forward the message to the 'unclassified_query' topic.

    """
    raise NotImplementedError()

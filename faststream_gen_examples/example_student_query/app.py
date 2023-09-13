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
    logger.info(msg)

    if msg.department == "finance_department":
        await to_finance_department.publish(msg)
    elif msg.department == "academic_department":
        await to_academic_department.publish(msg)
    elif msg.department == "admissions_department":
        await to_admissions_department.publish(msg)
    else:
        await to_unclassified_query.publish(msg)

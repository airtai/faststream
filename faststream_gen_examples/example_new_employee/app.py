from pydantic import BaseModel, Field

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class Employee(BaseModel):
    name: str = Field(..., examples=["Mickey"], description="name example")
    surname: str = Field(..., examples=["Mouse"], description="surname example")
    email: str = Field(
        ..., examples=["mikey.mouse@mail.ai"], description="email example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

to_notify_accounting = broker.publisher("notify_accounting")
to_notify_all_employees = broker.publisher("notify_all_employees")


@broker.subscriber("new_employee")
async def on_new_employee(msg: Employee, logger: Logger) -> None:
    logger.info(msg)

    await to_notify_accounting.publish(
        f"Please prepare all the paper work for: {msg.name} {msg.surname}"
    )
    await to_notify_all_employees.publish(
        f"Please welcome our new colleague: {msg.name} {msg.surname}"
    )

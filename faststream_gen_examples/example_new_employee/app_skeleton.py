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
    """
    Processes a message from the 'new_employee' topic.
    Upon reception, the function should publish messages to two topics:
    1. Send message to the 'notify_accounting' with content 'Please prepare all the paper work for:' and add at the end of the message employee name and surname
    2. Send message to the 'notify_all_employees' with content 'Please welcome our new colleague:' and add at the end of the message employee name and surname

    Instructions:
    1. Consume a message from 'new_employee' topic.
    2. Send message to the 'notify_accounting' with content 'Please prepare all the paper work for:' and add at the end of the message employee name and surname
    3. Send message to the 'notify_all_employees' with content 'Please welcome our new colleague:' and add at the end of the message employee name and surname
    """
    raise NotImplementedError()

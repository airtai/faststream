from pydantic import BaseModel, Field, NonNegativeInt

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class Pet(BaseModel):
    pet_id: NonNegativeInt = Field(..., examples=[1], description="Int data example")
    species: str = Field(..., examples=["dog"], description="Pet example")
    age: NonNegativeInt = Field(..., examples=[1], description="Int data example")


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.publisher("notify_adopters")
@broker.subscriber("new_pet")
async def on_new_pet(msg: Pet, logger: Logger) -> Pet:
    """
    Processes a message from the 'new_pet' topic and send the new pet's information to the 'notify_adopters' topic.

    Instructions:
    1. Consume a message from 'new_pet' topic.
    2. Send the new pet's information to the 'notify_adopters' topic.

    """
    raise NotImplementedError()

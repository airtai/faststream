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
    logger.info(msg)

    return msg

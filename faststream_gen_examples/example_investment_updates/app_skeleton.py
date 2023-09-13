from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class Investment(BaseModel):
    investor_id: NonNegativeInt = Field(
        ..., examples=[1], description="Int data example"
    )
    investment_amount: NonNegativeFloat = Field(
        ..., examples=[100.5], description="Float data example"
    )
    portfolio_value: NonNegativeFloat = Field(
        ..., examples=[1000.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

to_risk_management = broker.publisher("risk_management")


@broker.subscriber("investment_updates")
async def on_investment_updates(msg: Investment, logger: Logger) -> None:
    """
    Processes a message from the 'investment_updates' topic.
    Upon reception, the function should verify if the investment_amount exceeds a predetermined threshold (default treshold is 1000).
    If yes, forward the message to the 'risk_management' topic.

    Instructions:
    1. Consume a message from 'investment_updates' topic.
    2. Check if the investment_amount exceeds a predetermined threshold (default treshold is 1000).
    3. If 2. is True, forward the message to the 'risk_management' topic.

    """
    raise NotImplementedError()

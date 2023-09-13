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
    logger.info(msg)

    default_trashold = 1000

    if msg.investment_amount > default_trashold:
        await to_risk_management.publish(msg)

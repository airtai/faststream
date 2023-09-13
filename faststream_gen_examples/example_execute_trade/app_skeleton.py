from pydantic import BaseModel, Field, NonNegativeInt

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class Trade(BaseModel):
    trader_id: NonNegativeInt = Field(..., examples=[1], description="Int data example")
    stock_symbol: str = Field(..., examples=["WS"], description="Stock example")
    action: str = Field(..., examples=["Sell!!!"], description="Action example")


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

to_order_executed = broker.publisher("order_executed")


@broker.subscriber("execute_trade")
async def on_execute_trade(msg: Trade, logger: Logger) -> None:
    """
    Processes a message from the 'execute_trade' topic.
    Upon reception, the function should verify if the action attribute contains 'Sell'. If yes, retrieve the current price and append this detail to the message and publish the updated message to the 'order_executed' topic.

    Instructions:
    1. Consume a message from 'execute_trade' topic.
    2. Create a new message object (do not directly modify the original).
    3. Check if the action attribute contains 'Sell'.
    4. If 3. is True, retrieve the current price and append this detail to the message and publish the updated message to the 'order_executed' topic.

    """
    raise NotImplementedError()

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
    logger.info(msg)

    if "Sell" in msg.action:
        # price = retrieve_the_current_price(msg)
        # Currently using random price
        price = 5
        await to_order_executed.publish(
            Trade(
                trader_id=msg.trader_id,
                stock_symbol=msg.stock_symbol,
                action=(msg.action + f" Price = {price}"),
            )
        )

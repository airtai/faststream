import pytest

from faststream.kafka import TestKafkaBroker

from .app import Trade, broker, on_execute_trade


@broker.subscriber("order_executed")
async def on_order_executed(msg: Trade) -> None:
    pass


@pytest.mark.asyncio
async def test_app_without_sell_action():
    async with TestKafkaBroker(broker):
        await broker.publish(
            Trade(trader_id=1, stock_symbol="WS", action="Nothing"), "execute_trade"
        )
        on_execute_trade.mock.assert_called_with(
            dict(Trade(trader_id=1, stock_symbol="WS", action="Nothing"))
        )
        on_order_executed.mock.assert_not_called()


@pytest.mark.asyncio
async def test_app_with_sell_action():
    async with TestKafkaBroker(broker):
        await broker.publish(
            Trade(trader_id=1, stock_symbol="WS", action="Sell!"), "execute_trade"
        )
        on_execute_trade.mock.assert_called_with(
            dict(Trade(trader_id=1, stock_symbol="WS", action="Sell!"))
        )
        on_order_executed.mock.assert_called_with(
            dict(Trade(trader_id=1, stock_symbol="WS", action="Sell! Price = 5"))
        )

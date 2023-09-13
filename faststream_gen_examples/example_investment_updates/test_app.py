import pytest

from faststream.kafka import TestKafkaBroker

from .app import Investment, broker, on_investment_updates


@broker.subscriber("risk_management")
async def on_risk_management(msg: Investment) -> None:
    pass


@pytest.mark.asyncio
async def test_invest_smaller_amount_than_threshold():
    async with TestKafkaBroker(broker):
        await broker.publish(
            Investment(investor_id=1, investment_amount=100, portfolio_value=1000),
            "investment_updates",
        )
        on_investment_updates.mock.assert_called_with(
            dict(Investment(investor_id=1, investment_amount=100, portfolio_value=1000))
        )
        on_risk_management.mock.assert_not_called()


@pytest.mark.asyncio
async def test_invest_grater_amount_than_threshold():
    async with TestKafkaBroker(broker):
        await broker.publish(
            Investment(investor_id=1, investment_amount=1500, portfolio_value=1000),
            "investment_updates",
        )
        on_investment_updates.mock.assert_called_with(
            dict(
                Investment(investor_id=1, investment_amount=1500, portfolio_value=1000)
            )
        )
        on_risk_management.mock.assert_called_with(
            dict(
                Investment(investor_id=1, investment_amount=1500, portfolio_value=1000)
            )
        )

import pytest

from faststream.kafka import TestKafkaBroker

from .app import broker


@broker.subscriber("output_1")
async def on_output_1(msg: str):
    pass


@broker.subscriber("output_2")
async def on_output_2(msg: str):
    pass


@broker.subscriber("output_3")
async def on_output_3(msg: str):
    pass


@pytest.mark.asyncio
async def test_app():
    async with TestKafkaBroker(broker):
        await broker.publish("input string", "input")
        on_output_1.mock.assert_called_once_with("input string")
        on_output_2.mock.assert_called_once_with("input string")
        on_output_3.mock.assert_called_once_with("input string")

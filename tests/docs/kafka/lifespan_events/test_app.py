import pytest

from docs_src.kafka.lifespan_events.app import (
    app,
    broker,
    on_input_data_1,
    on_input_data_2,
    predictions,
)
from faststream import Logger, TestApp
from faststream.kafka import TestKafkaBroker


# when the following block is uncomment, the test passes
# TODO: remove after https://github.com/airtai/fastkafka/pull/533 merged
@broker.subscriber("predictions_topic")
async def on_output_data(msg: float, logger: Logger) -> None:
    logger.info(f"on_output_data({msg=})")


@pytest.mark.asyncio
async def test_lifespan_with_publisher_decorator():
    async with TestKafkaBroker(broker):
        async with TestApp(app):
            await broker.publish(2, "input_data_1")
            on_input_data_1.mock.assert_called_once_with(2)
            predictions.mock.assert_called_once_with(4)


@pytest.mark.asyncio
async def test_lifespan_with_await_inside_subscriber():
    async with TestKafkaBroker(broker):
        async with TestApp(app):
            await broker.publish(2, "input_data_2")
            on_input_data_2.mock.assert_called_once_with(2)
            predictions.mock.assert_called_once_with(4)

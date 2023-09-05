
import pytest

from faststream.kafka import TestKafkaBroker
from faststream import TestApp as T

from .app import broker, app, on_input_data_1, on_input_data_2, predictions

# when the following block is uncomment, the test passes
@broker.subscriber("predictions_topic")
async def on_output_data(msg: float):
    pass


@pytest.mark.asyncio
async def test_lifespan_with_publisher_decorator():
    async with TestKafkaBroker(broker):
        async with T(app):           
            await broker.publish(2, "input_data_1")
            on_input_data_1.mock.assert_called_once_with(2)
            predictions.mock.assert_called_once_with(4)
        

@pytest.mark.asyncio
async def test_lifespan_with_await_inside_subscriber():
    async with TestKafkaBroker(broker):
        async with T(app):
            await broker.publish(2, "input_data_2")
            on_input_data_2.mock.assert_called_once_with(2)
            predictions.mock.assert_called_once_with(4)

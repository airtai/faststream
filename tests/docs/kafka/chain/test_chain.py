import pytest

from docs.docs_src.kafka.chain.chain import (
    Data,
    broker,
    on_input_data,
    on_intermediate,
    on_output_data,
)
from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
async def test_end_to_end():
    async with TestKafkaBroker(broker) as tester:
        await tester.publish(Data(data=0.2), "input_data")
        on_input_data.mock.assert_called_with(dict(Data(data=0.2)))
        on_intermediate.mock.assert_called_with(dict(Data(data=1.2)))
        on_output_data.mock.assert_called_once_with({"data": 2.4})

import pytest

from docs_src.kafka.publish_with_partition_key.app import (
    Data,
    broker,
    on_input_data,
    to_output_data,
)
from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
# TODO: remove skip after https://github.com/airtai/fastkafka/pull/548 merged
@pytest.mark.skip("not supported yet")
async def test_base_app():
    async with TestKafkaBroker(broker):
        await broker.publish(Data(data=0.2), "input_data")

        on_input_data.mock.assert_called_once_with(dict(Data(data=0.2)))
        to_output_data.mock.assert_called_once_with(dict(Data(data=1.2)))

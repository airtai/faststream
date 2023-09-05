import pytest

from faststream.kafka import TestKafkaBroker

from .app import Data, broker, handle


@pytest.mark.asyncio
async def test_custom_parser():
    async with TestKafkaBroker(broker):
        msg = Data(data=0.5)

        # await broker.publish(msg, "input_data")
        await broker.publish(msg.model_dump_json().encode("utf-8"), "input_data")

        handle.mock.assert_called_once_with(Data(data=0.5))
        # handle.mock.assert_called_once_with(dict(Data(data=0.5)))

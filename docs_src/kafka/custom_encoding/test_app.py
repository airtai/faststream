import pytest

from faststream.kafka import TestKafkaBroker

from .app import Data, broker, handle


@pytest.mark.asyncio
async def test_custom_parser():
    async with TestKafkaBroker(broker):
        msg = Data(data=0.5)

        # await broker.publish(msg, "input_data")
        if hasattr(msg, "model_dump_json"):
            raw_msg = msg.model_dump_json().encode("utf-8")
        else:
            raw_msg = msg.json().encode("utf-8")

        await broker.publish(raw_msg, "input_data", headers={"Content-Type": "application/json"})

        handle.mock.assert_called_once_with(Data(data=0.5))
        # handle.mock.assert_called_once_with(dict(Data(data=0.5)))

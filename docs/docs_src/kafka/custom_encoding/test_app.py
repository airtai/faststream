import pytest

from faststream.kafka import TestKafkaBroker

from .app import Data, broker, handle


@pytest.mark.asyncio
async def test_custom_parser():
    async with TestKafkaBroker(broker):
        msg = Data(data=0.5)

        if hasattr(msg, "model_dump_json"):
            raw_msg = msg.model_dump_json().encode("utf-8")
        else:
            raw_msg = msg.json().encode("utf-8")

        await broker.publish(
            raw_msg, "input_data", headers={"content-type": "application/json"}
        )

        handle.mock.assert_called_once_with(msg)

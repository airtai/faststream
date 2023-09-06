import pytest

from docs.docs_src.kafka.custom_encoding.app import Data, broker, handle
from faststream._compat import model_to_json
from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
async def test_custom_parser():
    async with TestKafkaBroker(broker):
        msg = Data(data=0.5)

        await broker.publish(
            model_to_json(msg).encode("utf-8"),
            "input_data",
            headers={"Content-Type": "application/json"},
        )

        handle.mock.assert_called_once_with(msg)

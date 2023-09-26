import pytest

from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
async def test_index_dep():
    from docs.docs_src.index.dependencies import base_handler, broker

    data = {
        "user": "John",
        "user_id": 1,
    }

    async with TestKafkaBroker(broker) as br:
        await br.publish(data, "in-test")

        base_handler.mock.assert_called_once_with(data)

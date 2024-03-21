import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio()
async def test_global_kafka():
    from docs.docs_src.getting_started.dependencies.global_kafka import (
        app,
        broker,
        handle,
    )

    async with TestKafkaBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with(
            {
                "name": "John",
                "user_id": 1,
            }
        )

        with pytest.raises(ValueError):  # noqa: PT011
            await broker.publish({"name": "Ted", "user_id": 1}, "test-topic")

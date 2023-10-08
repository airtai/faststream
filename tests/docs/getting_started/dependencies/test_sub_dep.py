import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
async def test_sub_dep_kafka():
    from docs.docs_src.getting_started.dependencies.sub_dep_kafka import (
        app,
        broker,
        handle,
    )

    async with TestKafkaBroker(broker, connect_only=True):
        async with TestApp(app):
            handle.mock.assert_called_once_with(
                {
                    "name": "John",
                    "user_id": 1,
                }
            )

            with pytest.raises(AssertionError):
                await broker.publish({"name": "Ted", "user_id": 1}, "test-topic")

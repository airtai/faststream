import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
async def test_basic_kafka():
    from docs.docs_src.getting_started.dependencies.class_kafka import (
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

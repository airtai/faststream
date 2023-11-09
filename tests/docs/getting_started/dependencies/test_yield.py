import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
async def test_yield_kafka():
    from docs.docs_src.getting_started.dependencies.yield_kafka import (
        app,
        broker,
        handle,
    )

    async with TestKafkaBroker(broker), TestApp(app):
        handle.mock.assert_called_once_with("")

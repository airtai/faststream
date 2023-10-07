import pytest
from fastapi.testclient import TestClient

from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
async def test_fastapi_raw_integration():
    from docs.docs_src.integrations.http_frameworks_integrations.fastapi import (
        app,
        base_handler,
        broker,
    )

    async with TestKafkaBroker(broker, connect_only=True):
        with TestClient(app):
            await broker.publish("", "test")

            base_handler.mock.assert_called_once_with("")

import pytest
from fastapi.testclient import TestClient

from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio()
async def test_fastapi_raw_integration():
    from docs.docs_src.integrations.http_frameworks_integrations.fastapi import (
        app,
        base_handler,
        broker,
    )

    async with TestKafkaBroker(broker):
        with TestClient(app) as client:
            assert client.get("/").json() == {"Hello": "World"}

            await broker.publish("", "test")

            base_handler.mock.assert_called_once_with("")

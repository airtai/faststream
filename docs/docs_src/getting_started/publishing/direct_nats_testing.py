import pytest

from faststream.nats import TestNatsBroker

from .direct_nats import broker, publisher


@pytest.mark.asyncio
async def test_handle():
    async with TestNatsBroker(broker) as br:
        await br.publish("", topic="test-subject")

        publisher.mock.assert_called_once_with("Hi!")

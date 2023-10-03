from .pydantic_nats import broker

import pytest
import pydantic
from faststream.nats import TestNatsBroker


@pytest.mark.asyncio
async def test_correct():
    async with TestNatsBroker(broker) as br:
        await br.publish({
            "user": "John",
            "user_id": 1,
        }, "in-subject")

@pytest.mark.asyncio
async def test_invalid():
    async with TestNatsBroker(broker) as br:
        with pytest.raises(pydantic.ValidationError):
            await br.publish("wrong message", "in-subject")

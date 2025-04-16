from .pydantic import broker

import pytest
from fast_depends.exceptions import ValidationError
from faststream.confluent import TestKafkaBroker


@pytest.mark.asyncio
async def test_correct():
    async with TestKafkaBroker(broker) as br:
        await br.publish({
            "user": "John",
            "user_id": 1,
        }, "in-topic")

@pytest.mark.asyncio
async def test_invalid():
    async with TestKafkaBroker(broker) as br:
        with pytest.raises(ValidationError):
            await br.publish("wrong message", "in-topic")

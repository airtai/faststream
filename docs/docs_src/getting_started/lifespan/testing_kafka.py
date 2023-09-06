from faststream import TestApp
from faststream.kafka import TestKafkaBroker
import pytest

from .all_hooks_kafka import app


@pytest.mark.asyncio
async def test_lifespan():
    async with TestKafkaBroker(app.broker):
        async def TestApp(app):
            # test smth
            pass

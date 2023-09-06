import pytest

from faststream.kafka import TestKafkaBroker

from .all_hooks_kafka import app


@pytest.mark.asyncio
async def test_lifespan():
    async with TestKafkaBroker(app.broker):

        async def TestApp(app):
            # test smth
            pass

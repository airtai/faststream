import asyncio
from datetime import datetime

import pytest

from faststream import TestApp
from faststream.kafka import TestKafkaBroker

from .app import app, broker


@broker.subscriber("current_time")
async def on_current_time(msg: datetime):
    pass


@pytest.mark.asyncio
async def test_message_was_published():
    async with TestKafkaBroker(broker):
        async with TestApp(app):
            # todo: replace me better call (event based)
            await asyncio.sleep(1)
            on_current_time.mock.assert_called()

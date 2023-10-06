import pytest

from faststream import TestApp


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_declare():
    from docs.docs_src.rabbit.declare import app, broker

    async with TestApp(app):
        assert len(broker.declarer.exchanges) == 1
        assert len(broker.declarer.queues) == 2  # with `reply-to`

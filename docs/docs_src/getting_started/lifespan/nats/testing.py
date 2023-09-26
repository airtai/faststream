import pytest

from faststream import FastStream, TestApp
from faststream.nats import NatsBroker, TestNatsBroker

app = FastStream(NatsBroker())


@app.after_startup
async def handle():
    print("Calls in tests too!")


@pytest.mark.asyncio
async def test_lifespan():
    async with TestNatsBroker(app.broker):
        async with TestApp(app):
            # test something
            pass

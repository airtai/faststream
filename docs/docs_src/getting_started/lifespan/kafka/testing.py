import pytest

from faststream import FastStream, TestApp
from faststream.kafka import KafkaBroker, TestKafkaBroker

app = FastStream(KafkaBroker())


@app.after_startup
async def handle():
    print("Calls in tests too!")


@pytest.mark.asyncio
async def test_lifespan():
    async with TestKafkaBroker(app.broker):
        async with TestApp(app):
            # test something
            pass

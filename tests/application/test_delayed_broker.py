import pytest

from faststream._internal.application import StartAbleApplication
from faststream.rabbit import RabbitBroker


def test_set_broker() -> None:
    app = StartAbleApplication()

    assert app.broker is None

    broker = RabbitBroker()
    app.set_broker(broker)

    assert app.broker is broker


@pytest.mark.asyncio()
async def test_start_not_setup_broker() -> None:
    app = StartAbleApplication()

    with pytest.raises(AssertionError, match="You should setup a broker"):
        await app._start_broker()

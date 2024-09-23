import pytest

from tests.marks import require_aiopika


@pytest.mark.asyncio
@require_aiopika
async def test_example1():
    from examples.e12_custom_context import app1, broker1, handle1
    from faststream.rabbit import TestApp, TestRabbitBroker

    async with TestRabbitBroker(broker1), TestApp(app1):
        await handle1.wait_call(3)

        handle1.mock.assert_called_with("message")


@pytest.mark.asyncio
@require_aiopika
async def test_example2():
    from examples.e12_custom_context import app2, broker2, handle2
    from faststream.rabbit import TestApp, TestRabbitBroker

    async with TestRabbitBroker(broker2), TestApp(app2):
        await handle2.wait_call(3)

        handle2.mock.assert_called_with("message")

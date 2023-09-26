import pytest

from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test():
    from docs.docs_src.getting_started.context.nested import broker, handler

    async with TestRabbitBroker(broker) as br:
        await br.publish("Hi!", "test")

        handler.mock.assert_called_once_with("Hi!")

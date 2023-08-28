from unittest.mock import AsyncMock

import pytest

from faststream.broker.push_back_watcher import (
    CounterWatcher,
    EndlessWatcher,
    WatcherContext,
)
from faststream.exceptions import SkipMessage
from tests.tools.marks import needs_py38


@pytest.fixture
@needs_py38
def message():
    return AsyncMock(message_id=1)


@pytest.mark.asyncio
@needs_py38
async def test_push_back_correct(async_mock: AsyncMock, message):
    watcher = CounterWatcher(3)

    context = WatcherContext(
        watcher,
        message,
    )

    async with context:
        await async_mock()

    async_mock.assert_awaited_once()
    message.ack.assert_awaited_once()
    assert not watcher.memory.get(message.message_id)


@pytest.mark.asyncio
@needs_py38
async def test_push_back_endless_correct(async_mock: AsyncMock, message):
    watcher = EndlessWatcher()

    context = WatcherContext(
        watcher,
        message,
    )

    async with context:
        await async_mock()

    async_mock.assert_awaited_once()
    message.ack.assert_awaited_once()


@pytest.mark.asyncio
@needs_py38
async def test_push_back_watcher(async_mock: AsyncMock, message):
    watcher = CounterWatcher(3)

    context = WatcherContext(
        watcher,
        message,
    )

    async_mock.side_effect = ValueError("Ooops!")

    while not message.reject.called:
        with pytest.raises(ValueError):
            async with context:
                await async_mock()

    assert not message.ack.await_count
    assert message.nack.await_count == 3
    message.reject.assert_awaited_once()


@pytest.mark.asyncio
@needs_py38
async def test_push_endless_back_watcher(async_mock: AsyncMock, message):
    watcher = EndlessWatcher()

    context = WatcherContext(
        watcher,
        message,
    )

    async_mock.side_effect = ValueError("Ooops!")

    while message.nack.await_count < 10:
        with pytest.raises(ValueError):
            async with context:
                await async_mock()

    assert not message.ack.called
    assert not message.reject.called
    assert message.nack.await_count == 10


@pytest.mark.asyncio
@needs_py38
async def test_ignore_skip(async_mock: AsyncMock, message):
    watcher = CounterWatcher(3)

    context = WatcherContext(
        watcher,
        message,
    )

    async_mock.side_effect = SkipMessage()

    with pytest.raises(SkipMessage):
        async with context:
            await async_mock()

    assert not message.nack.called
    assert not message.reject.called
    assert not message.ack.called

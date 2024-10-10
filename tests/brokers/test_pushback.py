from typing import NoReturn
from unittest.mock import AsyncMock

import pytest

from faststream._internal.subscriber.acknowledgement_watcher import (
    CounterWatcher,
    EndlessWatcher,
    WatcherContext,
)
from faststream.exceptions import NackMessage, SkipMessage


@pytest.fixture()
def message():
    return AsyncMock(message_id=1)


@pytest.mark.asyncio()
async def test_push_back_correct(async_mock: AsyncMock, message) -> None:
    watcher = CounterWatcher(3)

    context = WatcherContext(
        message=message,
        watcher=watcher,
    )

    async with context:
        await async_mock()

    async_mock.assert_awaited_once()
    message.ack.assert_awaited_once()
    assert not watcher.memory.get(message.message_id)


@pytest.mark.asyncio()
async def test_push_back_endless_correct(async_mock: AsyncMock, message) -> None:
    watcher = EndlessWatcher()

    context = WatcherContext(
        message=message,
        watcher=watcher,
    )

    async with context:
        await async_mock()

    async_mock.assert_awaited_once()
    message.ack.assert_awaited_once()


@pytest.mark.asyncio()
async def test_push_back_watcher(async_mock: AsyncMock, message) -> None:
    watcher = CounterWatcher(3)

    context = WatcherContext(
        message=message,
        watcher=watcher,
    )

    async_mock.side_effect = ValueError("Ooops!")

    while not message.reject.called:
        with pytest.raises(ValueError):  # noqa: PT011
            async with context:
                await async_mock()

    assert not message.ack.await_count
    assert message.nack.await_count == 3
    message.reject.assert_awaited_once()


@pytest.mark.asyncio()
async def test_push_endless_back_watcher(async_mock: AsyncMock, message) -> None:
    watcher = EndlessWatcher()

    context = WatcherContext(
        message=message,
        watcher=watcher,
    )

    async_mock.side_effect = ValueError("Ooops!")

    while message.nack.await_count < 10:
        with pytest.raises(ValueError):  # noqa: PT011
            async with context:
                await async_mock()

    assert not message.ack.called
    assert not message.reject.called
    assert message.nack.await_count == 10


@pytest.mark.asyncio()
async def test_ignore_skip(async_mock: AsyncMock, message) -> NoReturn:
    watcher = CounterWatcher(3)

    context = WatcherContext(
        message=message,
        watcher=watcher,
    )

    async with context:
        raise SkipMessage

    assert not message.nack.called
    assert not message.reject.called
    assert not message.ack.called


@pytest.mark.asyncio()
async def test_additional_params_with_handler_exception(
    async_mock: AsyncMock, message
) -> NoReturn:
    watcher = EndlessWatcher()

    context = WatcherContext(
        message=message,
        watcher=watcher,
    )

    async with context:
        raise NackMessage(delay=5)

    message.nack.assert_called_with(delay=5)

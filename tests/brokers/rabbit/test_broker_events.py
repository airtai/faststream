import asyncio
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from faststream.rabbit import RabbitBroker
from tests.marks import require_aiopika

if TYPE_CHECKING:
    from aio_pika.abc import AbstractRobustConnection


@pytest.mark.parametrize("callback_type", (MagicMock, AsyncMock))
@pytest.mark.connected()
@pytest.mark.asyncio()
@pytest.mark.rabbit()
@require_aiopika
async def test_close_callback_survives_broker_restart(
    settings: Any,
    callback_type: type[MagicMock],
) -> None:
    on_close = callback_type()
    on_reconnected = callback_type()
    broker = RabbitBroker(settings.url, on_close=on_close, on_reconnected=on_reconnected)

    for _ in range(2):
        async with broker:
            connection = await broker.connect()
            assert await broker.connect() is connection
            on_close.assert_not_called()
            on_reconnected.assert_not_called()

        on_close.assert_called_once()
        assert on_close.call_args.args[0] is connection
        if isinstance(on_close, AsyncMock):
            on_close.assert_awaited_once_with(*on_close.call_args.args)
        on_reconnected.assert_not_called()
        on_close.reset_mock()


@pytest.mark.parametrize("callback_type", (MagicMock, AsyncMock))
@pytest.mark.connected()
@pytest.mark.asyncio()
@pytest.mark.rabbit()
@require_aiopika
async def test_reconnected_callback_after_automatic_recovery(
    settings: Any,
    callback_type: type[MagicMock],
) -> None:
    recovered: asyncio.Queue[AbstractRobustConnection | None] = asyncio.Queue()
    on_close = MagicMock()
    callback = callback_type(side_effect=recovered.put_nowait)
    broker = RabbitBroker(
        settings.url,
        reconnect_interval=0.01,
        on_close=on_close,
        on_reconnected=callback,
    )

    async with broker:
        connection = await broker.connect()
        assert connection.transport is not None
        await connection.transport.connection.close()
        assert await asyncio.wait_for(recovered.get(), timeout=5) is connection
        if isinstance(callback, AsyncMock):
            callback.assert_awaited_once_with(connection)
        else:
            callback.assert_called_once_with(connection)
        on_close.assert_called_once()
        assert on_close.call_args.args[0] is connection
        assert await broker.ping(timeout=1)

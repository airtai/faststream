import logging
import os
import signal
import sys
from unittest.mock import Mock, patch

import anyio
import pytest

from faststream import FastStream, TestApp
from faststream.log import logger
from faststream.rabbit import RabbitBroker
from faststream.utils import Context


def test_init(app: FastStream, context: Context, broker: RabbitBroker):
    assert app.broker is broker
    assert context.app is app
    assert app.logger is logger


def test_init_without_broker(app_without_broker: FastStream):
    assert app_without_broker.broker is None


def test_init_without_logger(app_without_logger: FastStream):
    assert app_without_logger.logger is None


def test_set_broker(broker: RabbitBroker, app_without_broker: FastStream):
    assert app_without_broker.broker is None
    app_without_broker.set_broker(broker)
    assert app_without_broker.broker is broker


def test_log(app: FastStream, app_without_logger: FastStream):
    app._log(logging.INFO, "test")
    app_without_logger._log(logging.INFO, "test")


@pytest.mark.asyncio
async def test_startup_calls_lifespans(mock: Mock, app_without_broker: FastStream):
    def call1():
        mock.call_start1()
        assert not mock.call_start2.called

    def call2():
        mock.call_start2()
        assert mock.call_start1.call_count == 1

    app_without_broker.on_startup(call1)
    app_without_broker.on_startup(call2)

    await app_without_broker._startup()

    mock.call_start1.assert_called_once()
    mock.call_start2.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_calls_lifespans(mock: Mock, app_without_broker: FastStream):
    def call1():
        mock.call_stop1()
        assert not mock.call_stop2.called

    def call2():
        mock.call_stop2()
        assert mock.call_stop1.call_count == 1

    app_without_broker.on_shutdown(call1)
    app_without_broker.on_shutdown(call2)

    await app_without_broker._shutdown()

    mock.call_stop1.assert_called_once()
    mock.call_stop2.assert_called_once()


@pytest.mark.asyncio
async def test_startup_lifespan_before_broker_started(async_mock, app: FastStream):
    @app.on_startup
    async def call():
        await async_mock.before()
        assert not async_mock.broker_start.called

    @app.after_startup
    async def call_after():
        await async_mock.after()
        async_mock.before.assert_awaited_once()
        async_mock.broker_start.assert_called_once()

    with patch.object(app.broker, "start", async_mock.broker_start):
        await app._startup()

    async_mock.broker_start.assert_called_once()
    async_mock.after.assert_awaited_once()
    async_mock.before.assert_awaited_once()


@pytest.mark.asyncio
async def test_shutdown_lifespan_after_broker_stopped(
    mock, async_mock, app: FastStream
):
    @app.after_shutdown
    async def call():
        await async_mock.after()
        async_mock.broker_stop.assert_called_once()

    @app.on_shutdown
    async def call_before():
        await async_mock.before()
        assert not async_mock.broker_stop.called

    with patch.object(app.broker, "close", async_mock.broker_stop):
        await app._shutdown()

    async_mock.broker_stop.assert_called_once()
    async_mock.after.assert_awaited_once()
    async_mock.before.assert_awaited_once()


@pytest.mark.asyncio
async def test_running(async_mock, app: FastStream):
    app._init_async_cycle()
    app._stop_event.set()

    with patch.object(app.broker, "start", async_mock.broker_run):
        with patch.object(app.broker, "close", async_mock.broker_stopped):
            await app.run()

    async_mock.broker_run.assert_called_once()
    async_mock.broker_stopped.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
async def test_stop_with_sigint(async_mock, app: FastStream):
    app._init_async_cycle()

    with patch.object(app.broker, "start", async_mock.broker_run_sigint):
        with patch.object(app.broker, "close", async_mock.broker_stopped_sigint):
            async with anyio.create_task_group() as tg:
                tg.start_soon(app.run)
                tg.start_soon(_kill, signal.SIGINT)

    async_mock.broker_run_sigint.assert_called_once()
    async_mock.broker_stopped_sigint.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
async def test_stop_with_sigterm(async_mock, app: FastStream):
    app._init_async_cycle()

    with patch.object(app.broker, "start", async_mock.broker_run_sigterm):
        with patch.object(app.broker, "close", async_mock.broker_stopped_sigterm):
            async with anyio.create_task_group() as tg:
                tg.start_soon(app.run)
                tg.start_soon(_kill, signal.SIGTERM)

    async_mock.broker_run_sigterm.assert_called_once()
    async_mock.broker_stopped_sigterm.assert_called_once()


@pytest.mark.asyncio
async def test_test_app(mock: Mock):
    app = FastStream()

    app.on_startup(mock.on)
    app.on_shutdown(mock.off)

    async with TestApp(app):
        pass

    mock.on.assert_called_once()
    mock.off.assert_called_once()


@pytest.mark.asyncio
async def test_test_app_with_excp(mock: Mock):
    app = FastStream()

    app.on_startup(mock.on)
    app.on_shutdown(mock.off)

    with pytest.raises(ValueError):
        async with TestApp(app):
            raise ValueError()

    mock.on.assert_called_once()
    mock.off.assert_called_once()


def test_sync_test_app(mock: Mock):
    app = FastStream()

    app.on_startup(mock.on)
    app.on_shutdown(mock.off)

    with TestApp(app):
        pass

    mock.on.assert_called_once()
    mock.off.assert_called_once()


def test_sync_test_app_with_excp(mock: Mock):
    app = FastStream()

    app.on_startup(mock.on)
    app.on_shutdown(mock.off)

    with pytest.raises(ValueError):
        with TestApp(app):
            raise ValueError()

    mock.on.assert_called_once()
    mock.off.assert_called_once()


async def _kill(sig):
    os.kill(os.getpid(), sig)

from unittest.mock import AsyncMock, patch

import pytest

from faststream import FastStream
from faststream.constants import AppState


@pytest.mark.asyncio
async def test_state_running(app: FastStream):
    with patch(
        "faststream._internal.application.Application.start", new_callable=AsyncMock
    ):
        await app._startup()
        assert app.state == AppState.STATE_RUNNING


@pytest.mark.asyncio
async def test_state_stopped(app: FastStream):
    with (
        patch(
            "faststream._internal.application.Application.start", new_callable=AsyncMock
        ),
        patch(
            "faststream._internal.application.Application.stop", new_callable=AsyncMock
        ),
    ):
        await app._startup()
        await app._shutdown()
        assert app.state == AppState.STATE_STOPPED

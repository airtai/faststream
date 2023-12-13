import ssl
from asyncio import sleep
from contextlib import contextmanager
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.exceptions import AuthenticationError


@contextmanager
def patch_asyncio_open_connection() -> Tuple[MagicMock, MagicMock]:
    try:
        reader = MagicMock()
        reader.readline = AsyncMock(return_value=b":1\r\n")
        reader.read = AsyncMock(return_value=b"")

        writer = MagicMock()
        writer.drain = AsyncMock()
        writer.wait_closed = AsyncMock()

        open_connection = AsyncMock(return_value=(reader, writer))

        with patch("asyncio.open_connection", new=open_connection):
            yield open_connection
    finally:
        pass


@pytest.mark.asyncio
@pytest.mark.redis
async def test_base_security():
    with patch_asyncio_open_connection() as connection:
        from docs.docs_src.redis.security.basic import broker as basic_broker

        async with basic_broker:
            await basic_broker._connection.ping()

        await sleep(1)

        assert type(connection.call_args.kwargs["ssl"]) == ssl.SSLContext


@pytest.mark.asyncio
@pytest.mark.redis
async def test_plaintext_security():
    with patch_asyncio_open_connection() as connection:
        from docs.docs_src.redis.security.plaintext import broker as basic_broker

        with pytest.raises(AuthenticationError):
            async with basic_broker:
                await basic_broker._connection.ping()

        await sleep(1)

        assert type(connection.call_args.kwargs["ssl"]) == ssl.SSLContext

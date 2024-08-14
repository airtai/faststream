from contextlib import contextmanager
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.exceptions import AuthenticationError

from faststream.app import FastStream
from faststream.specification.asyncapi.generate import get_app_schema


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
        from docs.docs_src.redis.security.basic import broker

        async with broker:
            await broker.ping(3.0)

        assert connection.call_args.kwargs["ssl"]

        schema = get_app_schema(FastStream(broker)).to_jsonable()
        assert schema == {
            "asyncapi": "2.6.0",
            "channels": {},
            "components": {"messages": {}, "schemas": {}, "securitySchemes": {}},
            "defaultContentType": "application/json",
            "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
            "servers": {
                "development": {
                    "protocol": "redis",
                    "protocolVersion": "custom",
                    "security": [],
                    "url": "redis://localhost:6379",
                }
            },
        }


@pytest.mark.asyncio
@pytest.mark.redis
async def test_plaintext_security():
    with patch_asyncio_open_connection() as connection:
        from docs.docs_src.redis.security.plaintext import broker

        with pytest.raises(AuthenticationError):
            async with broker:
                await broker._connection.ping()

        assert connection.call_args.kwargs["ssl"]

        schema = get_app_schema(FastStream(broker)).to_jsonable()
        assert schema == {
            "asyncapi": "2.6.0",
            "channels": {},
            "components": {
                "messages": {},
                "schemas": {},
                "securitySchemes": {"user-password": {"type": "userPassword"}},
            },
            "defaultContentType": "application/json",
            "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
            "servers": {
                "development": {
                    "protocol": "redis",
                    "protocolVersion": "custom",
                    "security": [{"user-password": []}],
                    "url": "redis://localhost:6379",
                }
            },
        }

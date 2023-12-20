from contextlib import contextmanager
from unittest.mock import patch

import aio_pika
import pytest
from aiormq.exceptions import AMQPConnectionError

from faststream.app import FastStream
from faststream.asyncapi.generate import get_app_schema
from tests.tools import spy_decorator


@contextmanager
def patch_asyncio_open_connection():
    try:
        with patch(
            "aio_pika.connect_robust",
            spy_decorator(aio_pika.connect_robust),
        ) as m:
            yield m
    finally:
        pass


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_base_security():
    with patch_asyncio_open_connection() as connection:
        from docs.docs_src.rabbit.security.basic import broker

        with pytest.raises(AMQPConnectionError):
            async with broker:
                pass

        assert connection.mock.call_args.kwargs["ssl_context"]

        schema = get_app_schema(FastStream(broker)).to_jsonable()
        assert schema == {
            "asyncapi": "2.6.0",
            "channels": {},
            "components": {"messages": {}, "schemas": {}, "securitySchemes": {}},
            "defaultContentType": "application/json",
            "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
            "servers": {
                "development": {
                    "protocol": "amqps",
                    "protocolVersion": "0.9.1",
                    "security": [],
                    "url": "amqps://guest:guest@localhost:5672/",  # pragma: allowlist secret
                }
            },
        }


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_plaintext_security():
    with patch_asyncio_open_connection() as connection:
        from docs.docs_src.rabbit.security.plaintext import broker

        with pytest.raises(AMQPConnectionError):
            async with broker:
                pass

        assert connection.mock.call_args.kwargs["ssl_context"]

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
                    "protocol": "amqps",
                    "protocolVersion": "0.9.1",
                    "security": [{"user-password": []}],
                    "url": "amqps://admin:password@localhost:5672/",  # pragma: allowlist secret
                }
            },
        }

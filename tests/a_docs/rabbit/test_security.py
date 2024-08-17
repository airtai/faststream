import pytest
from aiormq.exceptions import AMQPConnectionError

from faststream.app import FastStream
from faststream.specification.asyncapi.generate import get_app_schema


@pytest.mark.asyncio
@pytest.mark.rabbit
async def test_base_security():
    from docs.docs_src.rabbit.security.basic import broker

    with pytest.raises(AMQPConnectionError):
        async with broker:
            pass

    schema = get_app_schema(FastStream(broker), version=AsyncAPIVersion.v2_6).to_jsonable()
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
    from docs.docs_src.rabbit.security.plaintext import broker

    with pytest.raises(AMQPConnectionError):
        async with broker:
            pass

    schema = get_app_schema(FastStream(broker), version=AsyncAPIVersion.v2_6).to_jsonable()
    assert (
        schema
        == {
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
    )

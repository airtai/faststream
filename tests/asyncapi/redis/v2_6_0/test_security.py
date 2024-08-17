import ssl

from faststream.app import FastStream
from faststream.specification.asyncapi.generate import get_app_schema
from faststream.redis import RedisBroker
from faststream.security import (
    BaseSecurity,
    SASLPlaintext,
)
from faststream.specification.asyncapi.version import AsyncAPIVersion


def test_base_security_schema():
    ssl_context = ssl.create_default_context()
    security = BaseSecurity(ssl_context=ssl_context)

    broker = RedisBroker("rediss://localhost:6379/", security=security)

    assert (
        broker.url == "rediss://localhost:6379/"  # pragma: allowlist secret
    )  # pragma: allowlist secret

    schema = get_app_schema(FastStream(broker), version=AsyncAPIVersion.v2_6).to_jsonable()

    assert schema == {
        "asyncapi": "2.6.0",
        "channels": {},
        "components": {"messages": {}, "schemas": {}, "securitySchemes": {}},
        "defaultContentType": "application/json",
        "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
        "servers": {
            "development": {
                "protocol": "rediss",
                "protocolVersion": "custom",
                "security": [],
                "url": "rediss://localhost:6379/",
            }
        },
    }


def test_plaintext_security_schema():
    ssl_context = ssl.create_default_context()

    security = SASLPlaintext(
        ssl_context=ssl_context,
        username="admin",
        password="password",  # pragma: allowlist secret
    )

    broker = RedisBroker("redis://localhost:6379/", security=security)

    assert (
        broker.url == "redis://localhost:6379/"  # pragma: allowlist secret
    )  # pragma: allowlist secret

    schema = get_app_schema(FastStream(broker), version=AsyncAPIVersion.v2_6).to_jsonable()

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
                "url": "redis://localhost:6379/",
            }
        },
    }


def test_plaintext_security_schema_without_ssl():
    security = SASLPlaintext(
        username="admin",
        password="password",  # pragma: allowlist secret
    )

    broker = RedisBroker("redis://localhost:6379/", security=security)

    assert (
        broker.url == "redis://localhost:6379/"  # pragma: allowlist secret
    )  # pragma: allowlist secret

    schema = get_app_schema(FastStream(broker), version=AsyncAPIVersion.v2_6).to_jsonable()

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
                "url": "redis://localhost:6379/",
            }
        },
    }

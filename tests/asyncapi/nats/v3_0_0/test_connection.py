from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.broker.specification.tag import Tag
from faststream.asyncapi.version import AsyncAPIVersion
from faststream.nats import NatsBroker


def test_base():
    schema = get_app_schema(
        FastStream(
            NatsBroker(
                "nats:9092",
                protocol="plaintext",
                protocol_version="0.9.0",
                description="Test description",
                tags=(Tag(name="some-tag", description="experimental"),),
            ),
            asyncapi_version=AsyncAPIVersion.v3_0,
        )
    ).to_jsonable()

    assert schema == {
        "asyncapi": "3.0.0",
        "channels": {},
        "operations": {},
        "components": {"messages": {}, "schemas": {}},
        "defaultContentType": "application/json",
        "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
        "servers": {
            "development": {
                "description": "Test description",
                "protocol": "plaintext",
                "protocolVersion": "0.9.0",
                "tags": [{"description": "experimental", "name": "some-tag"}],
                "host": "nats:9092",
                "pathname": "",
            }
        },
    }, schema


def test_multi():
    schema = get_app_schema(
        FastStream(
            NatsBroker(
                ["nats:9092", "nats:9093"]
            ),
            asyncapi_version=AsyncAPIVersion.v3_0,
        )
    ).to_jsonable()

    assert schema == {
        "asyncapi": "3.0.0",
        "channels": {},
        "operations": {},
        "components": {"messages": {}, "schemas": {}},
        "defaultContentType": "application/json",
        "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
        "servers": {
            "Server1": {
                "protocol": "nats",
                "protocolVersion": "custom",
                "host": "nats:9092",
                "pathname": "",
            },
            "Server2": {
                "protocol": "nats",
                "protocolVersion": "custom",
                "host": "nats:9093",
                "pathname": "",
            },
        },
    }


def test_custom():
    schema = get_app_schema(
        FastStream(
            NatsBroker(
                ["nats:9092", "nats:9093"],
                asyncapi_url=["nats:9094", "nats:9095"],
            ),
            asyncapi_version=AsyncAPIVersion.v3_0,
        )
    ).to_jsonable()

    assert schema == {
        "asyncapi": "3.0.0",
        "channels": {},
        "operations": {},
        "components": {"messages": {}, "schemas": {}},
        "defaultContentType": "application/json",
        "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
        "servers": {
            "Server1": {
                "protocol": "nats",
                "protocolVersion": "custom",
                "host": "nats:9094",
                "pathname": "",
            },
            "Server2": {
                "protocol": "nats",
                "protocolVersion": "custom",
                "host": "nats:9095",
                "pathname": "",
            },
        },
    }

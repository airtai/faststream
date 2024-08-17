from faststream import FastStream
from faststream.nats import NatsBroker
from faststream.specification.asyncapi.generate import get_app_schema
from faststream.specification.asyncapi.version import AsyncAPIVersion
from faststream.specification.schema.tag import Tag


def test_base():
    schema = get_app_schema(
        FastStream(
            NatsBroker(
                "nats:9092",
                protocol="plaintext",
                protocol_version="0.9.0",
                description="Test description",
                tags=(Tag(name="some-tag", description="experimental"),),
            )
        ),
        version=AsyncAPIVersion.v2_6,
    ).to_jsonable()

    assert schema == {
        "asyncapi": "2.6.0",
        "channels": {},
        "components": {"messages": {}, "schemas": {}},
        "defaultContentType": "application/json",
        "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
        "servers": {
            "development": {
                "description": "Test description",
                "protocol": "plaintext",
                "protocolVersion": "0.9.0",
                "tags": [{"description": "experimental", "name": "some-tag"}],
                "url": "nats:9092",
            }
        },
    }, schema


def test_multi():
    schema = get_app_schema(
        FastStream(NatsBroker(["nats:9092", "nats:9093"])),
        version=AsyncAPIVersion.v2_6,
    ).to_jsonable()

    assert schema == {
        "asyncapi": "2.6.0",
        "channels": {},
        "components": {"messages": {}, "schemas": {}},
        "defaultContentType": "application/json",
        "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
        "servers": {
            "Server1": {
                "protocol": "nats",
                "protocolVersion": "custom",
                "url": "nats:9092",
            },
            "Server2": {
                "protocol": "nats",
                "protocolVersion": "custom",
                "url": "nats:9093",
            },
        },
    }


def test_custom():
    schema = get_app_schema(
        FastStream(
            NatsBroker(
                ["nats:9092", "nats:9093"], specification_url=["nats:9094", "nats:9095"]
            )
        ),
        version=AsyncAPIVersion.v2_6,
    ).to_jsonable()

    assert schema == {
        "asyncapi": "2.6.0",
        "channels": {},
        "components": {"messages": {}, "schemas": {}},
        "defaultContentType": "application/json",
        "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
        "servers": {
            "Server1": {
                "protocol": "nats",
                "protocolVersion": "custom",
                "url": "nats:9094",
            },
            "Server2": {
                "protocol": "nats",
                "protocolVersion": "custom",
                "url": "nats:9095",
            },
        },
    }

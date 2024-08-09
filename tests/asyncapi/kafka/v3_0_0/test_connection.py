from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.broker.specification.tag import Tag
from faststream.asyncapi.version import AsyncAPIVersion
from faststream.kafka import KafkaBroker


def test_base():
    schema = get_app_schema(
        FastStream(
            KafkaBroker(
                "kafka:9092",
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
                "host": "kafka:9092",
                "pathname": "",
            }
        },
    }


def test_multi():
    schema = get_app_schema(
        FastStream(
            KafkaBroker(["kafka:9092", "kafka:9093"]),
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
                "protocol": "kafka",
                "protocolVersion": "auto",
                "host": "kafka:9092",
                "pathname": "",
            },
            "Server2": {
                "protocol": "kafka",
                "protocolVersion": "auto",
                "host": "kafka:9093",
                "pathname": "",
            },
        },
    }


def test_custom():
    schema = get_app_schema(
        FastStream(
            KafkaBroker(
                ["kafka:9092", "kafka:9093"],
                asyncapi_url=["kafka:9094", "kafka:9095"],
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
                "protocol": "kafka",
                "protocolVersion": "auto",
                "host": "kafka:9094",
                "pathname": "",
            },
            "Server2": {
                "protocol": "kafka",
                "protocolVersion": "auto",
                "host": "kafka:9095",
                "pathname": "",
            },
        },
    }

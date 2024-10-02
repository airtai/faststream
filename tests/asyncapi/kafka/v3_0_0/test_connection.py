from faststream.kafka import KafkaBroker
from faststream.specification.asyncapi import AsyncAPI
from faststream.specification.schema.tag import Tag


def test_base():
    schema = AsyncAPI(
        KafkaBroker(
            "kafka:9092",
            protocol="plaintext",
            protocol_version="0.9.0",
            description="Test description",
            tags=(Tag(name="some-tag", description="experimental"),),
        ),
        schema_version="3.0.0",
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
            },
        },
    }


def test_multi():
    schema = AsyncAPI(
        KafkaBroker(["kafka:9092", "kafka:9093"]),
        schema_version="3.0.0",
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
    schema = AsyncAPI(
        KafkaBroker(
            ["kafka:9092", "kafka:9093"],
            specification_url=["kafka:9094", "kafka:9095"],
        ),
        schema_version="3.0.0",
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

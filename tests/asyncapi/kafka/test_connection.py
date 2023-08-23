from propan import PropanApp
from propan.asyncapi.generate import get_app_schema
from propan.asyncapi.schema import Tag
from propan.kafka import KafkaBroker


def test_base():
    schema = get_app_schema(
        PropanApp(
            KafkaBroker(
                "kafka:9092",
                protocol="plaintext",
                protocol_version="0.9.0",
                description="Test description",
                tags=(Tag(name="some-tag", description="experimental"),),
            )
        )
    ).to_jsonable()

    assert schema == {
        "asyncapi": "2.6.0",
        "channels": {},
        "components": {"messages": {}, "schemas": {}},
        "defaultContentType": "application/json",
        "info": {"description": "", "title": "Propan", "version": "0.1.0"},
        "servers": {
            "development": {
                "description": "Test description",
                "protocol": "plaintext",
                "protocolVersion": "0.9.0",
                "tags": [{"description": "experimental", "name": "some-tag"}],
                "url": "kafka:9092",
            }
        },
    }


def test_multi():
    schema = get_app_schema(
        PropanApp(KafkaBroker(["kafka:9092", "kafka:9093"]))
    ).to_jsonable()

    assert schema == {
        "asyncapi": "2.6.0",
        "channels": {},
        "components": {"messages": {}, "schemas": {}},
        "defaultContentType": "application/json",
        "info": {"description": "", "title": "Propan", "version": "0.1.0"},
        "servers": {
            "Server1": {
                "protocol": "kafka",
                "protocolVersion": "auto",
                "url": "kafka:9092",
            },
            "Server2": {
                "protocol": "kafka",
                "protocolVersion": "auto",
                "url": "kafka:9093",
            },
        },
    }

from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.asyncapi.schema import Tag
from faststream.rabbit import RabbitBroker


def test_base():
    schema = get_app_schema(
        FastStream(
            RabbitBroker(
                "localhost",
                protocol="amqps",
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
        "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
        "servers": {
            "development": {
                "description": "Test description",
                "protocol": "amqps",
                "protocolVersion": "0.9.0",
                "tags": [{"description": "experimental", "name": "some-tag"}],
                "url": "localhost",
            }
        },
    }

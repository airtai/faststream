from propan import PropanApp
from propan.asyncapi.generate import get_app_schema
from propan.asyncapi.schema import Tag
from propan.rabbit import RabbitBroker


def test_base():
    schema = get_app_schema(
        PropanApp(
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
        "info": {"description": "", "title": "Propan", "version": "0.1.0"},
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

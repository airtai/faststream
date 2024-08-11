from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.specification.tag import Tag
from faststream.asyncapi.version import AsyncAPIVersion
from faststream.rabbit import RabbitBroker


def test_base():
    schema = get_app_schema(
        FastStream(
            RabbitBroker(
                "amqps://localhost",
                port=5673,
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
                "protocol": "amqps",
                "protocolVersion": "0.9.0",
                "tags": [{"description": "experimental", "name": "some-tag"}],
                "host": "guest:guest@localhost:5673",  # pragma: allowlist secret
                "pathname": "/",
            }
        },
    }


def test_kwargs():
    broker = RabbitBroker(
        "amqp://guest:guest@localhost:5672/?heartbeat=300",  # pragma: allowlist secret
        host="127.0.0.1",
    )

    assert (
            broker.url
            == "amqp://guest:guest@127.0.0.1:5672/?heartbeat=300"  # pragma: allowlist secret
    )


def test_custom():
    broker = RabbitBroker(
        "amqps://localhost",
        asyncapi_url="amqp://guest:guest@127.0.0.1:5672/vh",  # pragma: allowlist secret
    )

    broker.publisher("test")
    schema = get_app_schema(FastStream(broker, asyncapi_version=AsyncAPIVersion.v3_0)).to_jsonable()

    assert (
            schema
            == {
                "asyncapi": "3.0.0",
                "channels": {
                    "test:_:Publisher": {
                        'address': 'test:_:Publisher',
                        "bindings": {
                            "amqp": {
                                "bindingVersion": "0.2.0",
                                "exchange": {"type": "default", "vhost": "/vh"},
                                "is": "routingKey",
                                "queue": {
                                    "autoDelete": False,
                                    "durable": False,
                                    "exclusive": False,
                                    "name": "test",
                                    "vhost": "/vh",
                                },
                            }
                        },
                        "servers": [
                            {
                                '$ref': '#/servers/development',
                            }
                        ],
                        'messages': {
                            'Message': {
                                '$ref': '#/components/messages/test:_:Publisher:Message',
                            },
                        }
                    }
                },
                'operations': {
                    'test:_:Publisher': {
                        'action': 'send',
                        'bindings': {
                            'amqp': {
                                'ack': True,
                                'bindingVersion': '0.2.0',
                                'cc': 'test',
                                'deliveryMode': 1,
                                'mandatory': True,
                            },
                        },
                        'channel': {
                            '$ref': '#/channels/test:_:Publisher',
                        },
                        'messages': [
                            {
                                '$ref': '#/channels/test:_:Publisher/messages/Message',
                            },
                        ],
                    },
                },
                "components": {
                    "messages": {
                        "test:_:Publisher:Message": {
                            "correlationId": {
                                "location": "$message.header#/correlation_id"
                            },
                            "payload": {
                                '$ref': '#/components/schemas/test:_:Publisher:Message:Payload'
                            },
                            "title": "test:_:Publisher:Message",
                        }
                    },
                    "schemas": {'test:_:Publisher:Message:Payload': {}},
                },
                "defaultContentType": "application/json",
                "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
                "servers": {
                    "development": {
                        "protocol": "amqp",
                        "protocolVersion": "0.9.1",
                        "host": "guest:guest@127.0.0.1:5672",  # pragma: allowlist secret
                        "pathname": "/vh",  # pragma: allowlist secret
                    }
                },
            }
    )

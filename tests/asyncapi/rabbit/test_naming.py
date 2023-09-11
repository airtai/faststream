from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.rabbit import RabbitBroker
from tests.asyncapi.base.naming import NamingTestCase


class TestNaming(NamingTestCase):
    broker_class = RabbitBroker

    def test_base(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle():
            ...

        schema = get_app_schema(FastStream(broker)).to_jsonable()

        assert schema == {
            "asyncapi": "2.6.0",
            "channels": {
                "HandleTest": {
                    "bindings": {
                        "amqp": {
                            "bindingVersion": "0.2.0",
                            "exchange": {"type": "default", "vhost": "/"},
                            "is": "routingKey",
                            "queue": {
                                "autoDelete": False,
                                "durable": False,
                                "exclusive": False,
                                "name": "test",
                                "vhost": "/",
                            },
                        }
                    },
                    "servers": ["development"],
                    "subscribe": {
                        "bindings": {
                            "amqp": {
                                "ack": True,
                                "bindingVersion": "0.2.0",
                                "cc": "test",
                            }
                        },
                        "message": {"$ref": "#/components/messages/HandleTestMessage"},
                    },
                }
            },
            "components": {
                "messages": {
                    "HandleTestMessage": {
                        "correlationId": {
                            "location": "$message.header#/correlation_id"
                        },
                        "payload": {"$ref": "#/components/schemas/EmptyPayload"},
                        "title": "HandleTestMessage",
                    }
                },
                "schemas": {"EmptyPayload": {"title": "EmptyPayload", "type": "null"}},
            },
            "defaultContentType": "application/json",
            "info": {"description": "", "title": "FastStream", "version": "0.1.0"},
            "servers": {
                "development": {
                    "protocol": "amqp",
                    "protocolVersion": "0.9.1",
                    "url": "amqp://guest:guest@localhost:5672/",  # pragma: allowlist secret
                }
            },
        }

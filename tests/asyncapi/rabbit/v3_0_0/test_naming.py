from typing import Type

from faststream import FastStream
from faststream.rabbit import RabbitBroker
from faststream.specification.asyncapi.generate import get_app_schema
from tests.asyncapi.base.v3_0_0.naming import NamingTestCase


class TestNaming(NamingTestCase):
    broker_class: Type[RabbitBroker] = RabbitBroker

    def test_subscriber_with_exchange(self):
        broker = self.broker_class()

        @broker.subscriber("test", "exchange")
        async def handle(): ...

        schema = get_app_schema(FastStream(broker), version="3.0.0",).to_jsonable()

        assert list(schema["channels"].keys()) == ["test:exchange:Handle"]

        assert list(schema["components"]["messages"].keys()) == [
            "test:exchange:Handle:Message"
        ]

    def test_publisher_with_exchange(self):
        broker = self.broker_class()

        @broker.publisher("test", "exchange")
        async def handle(): ...

        schema = get_app_schema(FastStream(broker), version="3.0.0",).to_jsonable()

        assert list(schema["channels"].keys()) == ["test:exchange:Publisher"]

        assert list(schema["components"]["messages"].keys()) == [
            "test:exchange:Publisher:Message"
        ]

    def test_base(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(): ...

        schema = get_app_schema(FastStream(broker), version="3.0.0",).to_jsonable()

        assert (
                schema
                == {
                    "asyncapi": "3.0.0",
                    "defaultContentType": "application/json",
                    "info": {"title": "FastStream", "version": "0.1.0", "description": ""},
                    "servers": {
                        "development": {
                            "host": "guest:guest@localhost:5672",  # pragma: allowlist secret
                            "pathname": "/",
                            "protocol": "amqp",
                            "protocolVersion": "0.9.1",
                        }
                    },
                    "channels": {
                        "test:_:Handle": {
                            "address": "test:_:Handle",
                            "servers": [
                                {
                                    "$ref": "#/servers/development",
                                }
                            ],
                            "bindings": {
                                "amqp": {
                                    "is": "routingKey",
                                    "bindingVersion": "0.2.0",
                                    "queue": {
                                        "name": "test",
                                        "durable": False,
                                        "exclusive": False,
                                        "autoDelete": False,
                                        "vhost": "/",
                                    },
                                    "exchange": {"type": "default", "vhost": "/"},
                                }
                            },
                            "messages": {
                                "SubscribeMessage": {
                                    "$ref": "#/components/messages/test:_:Handle:SubscribeMessage"
                                }
                            },
                        }
                    },
                    "operations": {
                        "test:_:HandleSubscribe": {
                            "action": "receive",
                            "bindings": {
                                "amqp": {
                                    "ack": True,
                                    "bindingVersion": "0.2.0",
                                    "cc": "test",
                                },
                            },
                            "channel": {
                                "$ref": "#/channels/test:_:Handle",
                            },
                            "messages": [
                                {
                                    "$ref": "#/channels/test:_:Handle/messages/SubscribeMessage",
                                },
                            ],
                        },
                    },
                    "components": {
                        "messages": {
                            "test:_:Handle:Message": {
                                "title": "test:_:Handle:Message",
                                "correlationId": {
                                    "location": "$message.header#/correlation_id"
                                },
                                "payload": {"$ref": "#/components/schemas/EmptyPayload"},
                            }
                        },
                        "schemas": {
                            "EmptyPayload": {"title": "EmptyPayload", "type": "null"}
                        },
                    },
                }
        )

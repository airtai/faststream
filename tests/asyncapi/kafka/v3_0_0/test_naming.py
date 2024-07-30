from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.asyncapi.version import AsyncAPIVersion
from faststream.kafka import KafkaBroker
from tests.asyncapi.base.v3_0_0.naming import NamingTestCase


class TestNaming(NamingTestCase):
    broker_class = KafkaBroker

    def test_base(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(): ...

        schema = get_app_schema(FastStream(broker, asyncapi_version=AsyncAPIVersion.v3_0)).to_jsonable()

        assert schema == {
            "asyncapi": "3.0.0",
            "defaultContentType": "application/json",
            "info": {"title": "FastStream", "version": "0.1.0", "description": ""},
            "servers": {
                "development": {
                    "host": "localhost",
                    "pathname": "",
                    "protocol": "kafka",
                    "protocolVersion": "auto",
                }
            },
            "channels": {
                "test:Handle": {
                    "address": "test:Handle",
                    "servers": [
                        {
                            "$ref": "#/servers/development",
                        }
                    ],
                    "bindings": {"kafka": {"topic": "test", "bindingVersion": "0.4.0"}},
                    "messages": {
                        "SubscribeMessage": {
                            "$ref": "#/components/messages/test:Handle:SubscribeMessage",
                        },
                    },
                }
            },
            "operations": {
                "test:HandleSubscribe": {
                    "action": "receive",
                    "channel": {
                        "$ref": "#/channels/test:Handle",
                    },
                    "messages": [
                        {
                            "$ref": "#/channels/test:Handle/messages/SubscribeMessage",
                        }
                    ],
                }
            },
            "components": {
                "messages": {
                    "test:Handle:Message": {
                        "title": "test:Handle:Message",
                        "correlationId": {
                            "location": "$message.header#/correlation_id"
                        },
                        "payload": {"$ref": "#/components/schemas/EmptyPayload"},
                    }
                },
                "schemas": {"EmptyPayload": {"title": "EmptyPayload", "type": "null"}},
            },
        }

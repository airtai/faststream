from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.kafka import KafkaBroker
from tests.asyncapi.base.naming import NamingTestCase


class TestNaming(NamingTestCase):
    broker_class = KafkaBroker

    def test_base(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(): ...

        schema = get_app_schema(FastStream(broker)).to_jsonable()

        assert schema == {
            "asyncapi": "2.6.0",
            "defaultContentType": "application/json",
            "info": {"title": "FastStream", "version": "0.1.0", "description": ""},
            "servers": {
                "development": {
                    "url": "localhost",
                    "protocol": "kafka",
                    "protocolVersion": "auto",
                }
            },
            "channels": {
                "test:Handle": {
                    "servers": ["development"],
                    "bindings": {"kafka": {"topic": "test", "bindingVersion": "0.4.0"}},
                    "subscribe": {
                        "message": {"$ref": "#/components/messages/test:Handle:Message"}
                    },
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

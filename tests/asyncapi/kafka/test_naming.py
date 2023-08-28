from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.kafka import KafkaBroker
from tests.asyncapi.base.naming import NamingTestCase


class TestNaming(NamingTestCase):
    broker_class = KafkaBroker

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
                    "bindings": {"kafka": {"bindingVersion": "0.4.0", "topic": "test"}},
                    "servers": ["development"],
                    "subscribe": {
                        "message": {"$ref": "#/components/messages/HandleTestMessage"}
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
                    "protocol": "kafka",
                    "protocolVersion": "auto",
                    "url": "localhost",
                }
            },
        }

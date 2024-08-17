from faststream import FastStream
from faststream.redis import RedisBroker, RedisPublisher, RedisRoute, RedisRouter
from faststream.specification.asyncapi.generate import get_app_schema
from faststream.specification.asyncapi.version import AsyncAPIVersion
from tests.asyncapi.base.v2_6_0.arguments import ArgumentsTestcase
from tests.asyncapi.base.v2_6_0.publisher import PublisherTestcase
from tests.asyncapi.base.v3_0_0.router import RouterTestcase


class TestRouter(RouterTestcase):
    broker_class = RedisBroker
    router_class = RedisRouter
    route_class = RedisRoute
    publisher_class = RedisPublisher

    def test_prefix(self):
        broker = self.broker_class()

        router = self.router_class(prefix="test_")

        @router.subscriber("test")
        async def handle(msg): ...

        broker.include_router(router)

        schema = get_app_schema(FastStream(broker), version=AsyncAPIVersion.v3_0,).to_jsonable()

        assert schema == {
            "info": {
                "title": "FastStream",
                "version": "0.1.0",
                "description": ""
            },
            "asyncapi": "3.0.0",
            "defaultContentType": "application/json",
            "servers": {
                "development": {
                    "host": "localhost:6379",
                    "pathname": "",
                    "protocol": "redis",
                    "protocolVersion": "custom"
                }
            },
            "channels": {
                "test_test:Handle": {
                    "address": "test_test:Handle",
                    "servers": [
                        {
                            "$ref": "#/servers/development"
                        }
                    ],
                    "messages": {
                        "SubscribeMessage": {
                            "$ref": "#/components/messages/test_test:Handle:SubscribeMessage"
                        }
                    },
                    "bindings": {
                        "redis": {
                            "channel": "test_test",
                            "method": "subscribe",
                            "bindingVersion": "custom"
                        }
                    }
                }
            },
            "operations": {
                "test_test:HandleSubscribe": {
                    "action": "receive",
                    "messages": [
                        {
                            "$ref": "#/channels/test_test:Handle/messages/SubscribeMessage"
                        }
                    ],
                    "channel": {
                        "$ref": "#/channels/test_test:Handle"
                    }
                }
            },
            "components": {
                "messages": {
                    "test_test:Handle:Message": {
                        "title": "test_test:Handle:Message",
                        "correlationId": {
                            "location": "$message.header#/correlation_id"
                        },
                        "payload": {
                            "$ref": "#/components/schemas/Handle:Message:Payload"
                        }
                    }
                },
                "schemas": {
                    "Handle:Message:Payload": {
                        "title": "Handle:Message:Payload"
                    }
                }
            }
        }


class TestRouterArguments(ArgumentsTestcase):
    broker_class = RedisRouter

    def build_app(self, router):
        broker = RedisBroker()
        broker.include_router(router)
        return FastStream(broker)


class TestRouterPublisher(PublisherTestcase):
    broker_class = RedisRouter

    def build_app(self, router):
        broker = RedisBroker()
        broker.include_router(router)
        return FastStream(broker)

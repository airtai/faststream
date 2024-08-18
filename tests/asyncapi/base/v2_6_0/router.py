from typing import Type

from dirty_equals import IsStr

from faststream import FastStream
from faststream.broker.core.usecase import BrokerUsecase
from faststream.broker.router import ArgsContainer, BrokerRouter, SubscriberRoute
from faststream.specification.asyncapi.generate import get_app_schema


class RouterTestcase:
    broker_class: Type[BrokerUsecase]
    router_class: Type[BrokerRouter]
    publisher_class: Type[ArgsContainer]
    route_class: Type[SubscriberRoute]

    def test_delay_subscriber(self):
        broker = self.broker_class()

        async def handle(msg): ...

        router = self.router_class(
            handlers=(self.route_class(handle, "test"),),
        )

        broker.include_router(router)

        schema = get_app_schema(FastStream(broker), version="2.6.0").to_jsonable()

        payload = schema["components"]["schemas"]
        key = list(payload.keys())[0]  # noqa: RUF015
        assert payload[key]["title"] == key == "Handle:Message:Payload"

    def test_delay_publisher(self):
        broker = self.broker_class()

        async def handle(msg): ...

        router = self.router_class(
            handlers=(
                self.route_class(
                    handle,
                    "test",
                    publishers=(self.publisher_class("test2", schema=int),),
                ),
            ),
        )

        broker.include_router(router)

        schema = get_app_schema(FastStream(broker))
        schemas = schema.components.schemas
        del schemas["Handle:Message:Payload"]

        for i, j in schemas.items():
            assert (
                i == j["title"] == IsStr(regex=r"test2[\w:]*:Publisher:Message:Payload")
            )
            assert j["type"] == "integer"

    def test_not_include(self):
        broker = self.broker_class()
        router = self.router_class(include_in_schema=False)

        @router.subscriber("test")
        @router.publisher("test")
        async def handle(msg): ...

        broker.include_router(router)

        schema = get_app_schema(FastStream(broker))
        assert schema.channels == {}, schema.channels

    def test_not_include_in_method(self):
        broker = self.broker_class()
        router = self.router_class()

        @router.subscriber("test")
        @router.publisher("test")
        async def handle(msg): ...

        broker.include_router(router, include_in_schema=False)

        schema = get_app_schema(FastStream(broker))
        assert schema.channels == {}, schema.channels

    def test_respect_subrouter(self):
        broker = self.broker_class()
        router = self.router_class()
        router2 = self.router_class(include_in_schema=False)

        @router2.subscriber("test")
        @router2.publisher("test")
        async def handle(msg): ...

        router.include_router(router2)
        broker.include_router(router)

        schema = get_app_schema(FastStream(broker))

        assert schema.channels == {}, schema.channels

    def test_not_include_subrouter(self):
        broker = self.broker_class()
        router = self.router_class(include_in_schema=False)
        router2 = self.router_class()

        @router2.subscriber("test")
        @router2.publisher("test")
        async def handle(msg): ...

        router.include_router(router2)
        broker.include_router(router)

        schema = get_app_schema(FastStream(broker))

        assert schema.channels == {}

    def test_not_include_subrouter_by_method(self):
        broker = self.broker_class()
        router = self.router_class()
        router2 = self.router_class()

        @router2.subscriber("test")
        @router2.publisher("test")
        async def handle(msg): ...

        router.include_router(router2, include_in_schema=False)
        broker.include_router(router)

        schema = get_app_schema(FastStream(broker))

        assert schema.channels == {}

    def test_all_nested_routers_by_method(self):
        broker = self.broker_class()
        router = self.router_class()
        router2 = self.router_class()

        @router2.subscriber("test")
        @router2.publisher("test")
        async def handle(msg): ...

        router.include_router(router2)
        broker.include_router(router, include_in_schema=False)

        schema = get_app_schema(FastStream(broker))

        assert schema.channels == {}

    def test_include_subrouter(self):
        broker = self.broker_class()
        router = self.router_class()
        router2 = self.router_class()

        @router2.subscriber("test")
        @router2.publisher("test")
        async def handle(msg): ...

        router.include_router(router2)
        broker.include_router(router)

        schema = get_app_schema(FastStream(broker))

        assert len(schema.channels) == 2

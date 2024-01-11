from typing import Type

from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.broker.core.broker import BrokerUsecase
from faststream.broker.router import BrokerRoute, BrokerRouter


class RouterTestcase:  # noqa: D101
    broker_class: Type[BrokerUsecase]
    router_class: Type[BrokerRouter]
    route_class: Type[BrokerRoute]

    def test_delay(self):
        broker = self.broker_class()

        async def handle(msg):
            ...

        router = self.router_class(
            handlers=(self.route_class(handle, "test"),),
        )

        broker.include_router(router)

        schema = get_app_schema(FastStream(broker)).to_jsonable()

        payload = schema["components"]["schemas"]
        key = list(payload.keys())[0]  # noqa: RUF015
        assert payload[key]["title"] == key == "Handle:Message:Payload"

    def test_not_include(self):
        broker = self.broker_class()
        router = self.router_class(include_in_schema=False)

        @router.subscriber("test")
        @router.publisher("test")
        async def handle(msg):
            ...

        broker.include_router(router)

        schema = get_app_schema(FastStream(broker))

        assert schema.channels == {}

    def test_respect_subrouter(self):
        broker = self.broker_class()
        router = self.router_class()
        router2 = self.router_class(include_in_schema=False)

        @router2.subscriber("test")
        @router2.publisher("test")
        async def handle(msg):
            ...

        router.include_router(router2)
        broker.include_router(router)

        schema = get_app_schema(FastStream(broker))

        assert schema.channels == {}

    def test_not_include_subrouter(self):
        broker = self.broker_class()
        router = self.router_class(include_in_schema=False)
        router2 = self.router_class()

        @router2.subscriber("test")
        @router2.publisher("test")
        async def handle(msg):
            ...

        router.include_router(router2)
        broker.include_router(router)

        schema = get_app_schema(FastStream(broker))

        assert schema.channels == {}

    def test_include_subrouter(self):
        broker = self.broker_class()
        router = self.router_class()
        router2 = self.router_class()

        @router2.subscriber("test")
        @router2.publisher("test")
        async def handle(msg):
            ...

        router.include_router(router2)
        broker.include_router(router)

        schema = get_app_schema(FastStream(broker))

        assert len(schema.channels) == 2

from typing import Type

from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.broker.core.abc import BrokerUsecase
from faststream.broker.router import BrokerRoute, BrokerRouter


class RouterTestcase:
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
        key = list(payload.keys())[0]
        assert payload[key]["title"] == key == "Handle:Message:Payload"

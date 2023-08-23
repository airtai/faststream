from typing import Type

from propan import PropanApp
from propan.asyncapi.generate import get_app_schema
from propan.broker.core.abc import BrokerUsecase
from propan.broker.router import BrokerRoute, BrokerRouter


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

        schema = get_app_schema(PropanApp(broker)).to_jsonable()

        payload = schema["components"]["schemas"]

        assert payload == {"HandleTestMsgPayload": {"title": "HandleTestMsgPayload"}}

from faststream.nats import NatsBroker
from faststream.specification.asyncapi import AsyncAPI
from tests.asyncapi.base.v2_6_0.arguments import ArgumentsTestcase


class TestArguments(ArgumentsTestcase):
    broker_class = NatsBroker

    def test_subscriber_bindings(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(msg): ...

        schema = AsyncAPI(self.build_app(broker), schema_version="2.6.0").jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert schema["channels"][key]["bindings"] == {
            "nats": {"bindingVersion": "custom", "subject": "test"}
        }

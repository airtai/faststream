from faststream.specification.asyncapi.generate import get_app_schema
from faststream.nats import NatsBroker
from tests.asyncapi.base.v3_0_0.publisher import PublisherTestcase


class TestArguments(PublisherTestcase):
    broker_factory = NatsBroker

    def test_publisher_bindings(self):
        broker = self.broker_factory()

        @broker.publisher("test")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert schema["channels"][key]["bindings"] == {
            "nats": {"bindingVersion": "custom", "subject": "test"}
        }, schema["channels"][key]["bindings"]

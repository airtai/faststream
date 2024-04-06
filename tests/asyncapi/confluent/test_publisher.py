from faststream.asyncapi.generate import get_app_schema
from faststream.confluent import KafkaBroker
from tests.asyncapi.base.publisher import PublisherTestcase


class TestArguments(PublisherTestcase):
    broker_class = KafkaBroker

    def test_publisher_bindings(self):
        broker = self.broker_class()

        @broker.publisher("test")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert schema["channels"][key]["bindings"] == {
            "kafka": {"bindingVersion": "0.4.0", "topic": "test"}
        }

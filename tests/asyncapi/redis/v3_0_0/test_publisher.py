from faststream.redis import RedisBroker
from faststream.specification.asyncapi.generate import get_app_schema
from tests.asyncapi.base.v3_0_0.publisher import PublisherTestcase


class TestArguments(PublisherTestcase):
    broker_factory = RedisBroker

    def test_channel_publisher(self):
        broker = self.broker_factory()

        @broker.publisher("test")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert schema["channels"][key]["bindings"] == {
            "redis": {
                "bindingVersion": "custom",
                "channel": "test",
                "method": "publish",
            }
        }

    def test_list_publisher(self):
        broker = self.broker_factory()

        @broker.publisher(list="test")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert schema["channels"][key]["bindings"] == {
            "redis": {"bindingVersion": "custom", "channel": "test", "method": "rpush"}
        }

    def test_stream_publisher(self):
        broker = self.broker_factory()

        @broker.publisher(stream="test")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert schema["channels"][key]["bindings"] == {
            "redis": {"bindingVersion": "custom", "channel": "test", "method": "xadd"}
        }

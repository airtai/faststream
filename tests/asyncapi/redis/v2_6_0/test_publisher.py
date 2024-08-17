from faststream.redis import RedisBroker
from faststream.specification.asyncapi.generate import get_app_schema
from faststream.specification.asyncapi.version import AsyncAPIVersion
from tests.asyncapi.base.v2_6_0.publisher import PublisherTestcase


class TestArguments(PublisherTestcase):
    broker_class = RedisBroker

    def test_channel_publisher(self):
        broker = self.broker_class()

        @broker.publisher("test")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker), version=AsyncAPIVersion.v2_6).to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert schema["channels"][key]["bindings"] == {
            "redis": {
                "bindingVersion": "custom",
                "channel": "test",
                "method": "publish",
            }
        }

    def test_list_publisher(self):
        broker = self.broker_class()

        @broker.publisher(list="test")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker), version=AsyncAPIVersion.v2_6).to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert schema["channels"][key]["bindings"] == {
            "redis": {"bindingVersion": "custom", "channel": "test", "method": "rpush"}
        }

    def test_stream_publisher(self):
        broker = self.broker_class()

        @broker.publisher(stream="test")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker), version=AsyncAPIVersion.v2_6).to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert schema["channels"][key]["bindings"] == {
            "redis": {"bindingVersion": "custom", "channel": "test", "method": "xadd"}
        }

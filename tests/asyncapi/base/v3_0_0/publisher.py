from typing import Type, Callable, Union

import pydantic

from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.asyncapi.version import AsyncAPIVersion
from faststream.broker.core.usecase import BrokerUsecase
from faststream.broker.fastapi import StreamRouter


class PublisherTestcase:
    broker_factory: Callable[[], Union[BrokerUsecase, StreamRouter]]

    def build_app(self, broker):
        """Patch it to test FastAPI scheme generation too."""
        return FastStream(broker, asyncapi_version=AsyncAPIVersion.v3_0)

    def test_publisher_with_description(self):
        broker = self.broker_factory()

        @broker.publisher("test", description="test description")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015
        assert schema["channels"][key]["description"] == "test description"

    def test_basic_publisher(self):
        broker = self.broker_factory()

        @broker.publisher("test")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015
        assert schema["channels"][key].get("description") is None
        assert schema["operations"][key] is not None

        payload = schema["components"]["schemas"]
        for v in payload.values():
            assert v == {}

    def test_none_publisher(self):
        broker = self.broker_factory()

        @broker.publisher("test")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]
        for v in payload.values():
            assert v == {}

    def test_typed_publisher(self):
        broker = self.broker_factory()

        @broker.publisher("test")
        async def handle(msg) -> int: ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]
        for v in payload.values():
            assert v["type"] == "integer"

    def test_pydantic_model_publisher(self):
        class User(pydantic.BaseModel):
            name: str = ""
            id: int

        broker = self.broker_factory()

        @broker.publisher("test")
        async def handle(msg) -> User: ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert v == {
                "properties": {
                    "id": {"title": "Id", "type": "integer"},
                    "name": {"default": "", "title": "Name", "type": "string"},
                },
                "required": ["id"],
                "title": key,
                "type": "object",
            }

    def test_delayed(self):
        broker = self.broker_factory()

        pub = broker.publisher("test")

        @pub
        async def handle(msg) -> int: ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]
        for v in payload.values():
            assert v["type"] == "integer"

    def test_with_schema(self):
        broker = self.broker_factory()

        broker.publisher("test", title="Custom", schema=int)

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]
        for v in payload.values():
            assert v["type"] == "integer"

    def test_not_include(self):
        broker = self.broker_factory()

        @broker.publisher("test", include_in_schema=False)
        @broker.subscriber("in-test", include_in_schema=False)
        async def handler(msg: str):
            pass

        schema = get_app_schema(self.build_app(broker))

        assert schema.channels == {}, schema.channels

from typing import Type

import pydantic

from faststream._internal.broker.broker import BrokerUsecase
from faststream.specification.asyncapi import AsyncAPI


class PublisherTestcase:
    broker_class: Type[BrokerUsecase]

    def build_app(self, broker):
        """Patch it to test FastAPI scheme generation too."""
        return broker

    def test_publisher_with_description(self):
        broker = self.broker_class()

        @broker.publisher("test", description="test description")
        async def handle(msg): ...

        schema = AsyncAPI(self.build_app(broker), schema_version="2.6.0").jsonable()

        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015
        assert schema["channels"][key]["description"] == "test description"

    def test_basic_publisher(self):
        broker = self.broker_class()

        @broker.publisher("test")
        async def handle(msg): ...

        schema = AsyncAPI(self.build_app(broker), schema_version="2.6.0").jsonable()

        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015
        assert schema["channels"][key].get("description") is None
        assert schema["channels"][key].get("publish") is not None

        payload = schema["components"]["schemas"]
        for v in payload.values():
            assert v == {}

    def test_none_publisher(self):
        broker = self.broker_class()

        @broker.publisher("test")
        async def handle(msg): ...

        schema = AsyncAPI(self.build_app(broker), schema_version="2.6.0").jsonable()

        payload = schema["components"]["schemas"]
        for v in payload.values():
            assert v == {}

    def test_typed_publisher(self):
        broker = self.broker_class()

        @broker.publisher("test")
        async def handle(msg) -> int: ...

        schema = AsyncAPI(self.build_app(broker), schema_version="2.6.0").jsonable()

        payload = schema["components"]["schemas"]
        for v in payload.values():
            assert v["type"] == "integer"

    def test_pydantic_model_publisher(self):
        class User(pydantic.BaseModel):
            name: str = ""
            id: int

        broker = self.broker_class()

        @broker.publisher("test")
        async def handle(msg) -> User: ...

        schema = AsyncAPI(self.build_app(broker), schema_version="2.6.0").jsonable()

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
        broker = self.broker_class()

        pub = broker.publisher("test")

        @pub
        async def handle(msg) -> int: ...

        schema = AsyncAPI(self.build_app(broker), schema_version="2.6.0").jsonable()

        payload = schema["components"]["schemas"]
        for v in payload.values():
            assert v["type"] == "integer"

    def test_with_schema(self):
        broker = self.broker_class()

        broker.publisher("test", title="Custom", schema=int)

        schema = AsyncAPI(self.build_app(broker), schema_version="2.6.0").jsonable()

        payload = schema["components"]["schemas"]
        for v in payload.values():
            assert v["type"] == "integer"

    def test_not_include(self):
        broker = self.broker_class()

        @broker.publisher("test", include_in_schema=False)
        @broker.subscriber("in-test", include_in_schema=False)
        async def handler(msg: str):
            pass

        schema = AsyncAPI(self.build_app(broker))

        assert schema.jsonable()["channels"] == {}, schema.jsonable()["channels"]

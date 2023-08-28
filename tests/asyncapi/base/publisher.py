from typing import Type

import pydantic
from dirty_equals import IsStr

from faststream import FastStream
from faststream.asyncapi.generate import get_app_schema
from faststream.broker.core.abc import BrokerUsecase


class PublisherTestcase:
    broker_class: Type[BrokerUsecase]

    def build_app(self, broker):
        """Patch it to test FastAPI scheme generation too"""
        return FastStream(broker)

    def test_publisher_with_name(self):
        broker = self.broker_class()

        @broker.publisher("test", title="custom_name", description="test description")
        async def handle(msg):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        key = tuple(schema["channels"].keys())[0]

        assert key == "custom_name"
        assert schema["channels"][key]["description"] == "test description"

    def test_basic_publisher(self):
        broker = self.broker_class()

        @broker.publisher("test")
        async def handle(msg):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        key = tuple(schema["channels"].keys())[0]
        assert schema["channels"][key].get("description") is None

        payload = schema["components"]["schemas"]
        for key, v in payload.items():
            assert key == IsStr(regex=r"\w*Payload")
            assert v == {}

    def test_none_publisher(self):
        broker = self.broker_class()

        @broker.publisher("test")
        async def handle(msg):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]
        for key, v in payload.items():
            assert key == IsStr(regex=r"\w*Payload")
            assert v == {}

    def test_typed_publisher(self):
        broker = self.broker_class()

        @broker.publisher("test")
        async def handle(msg) -> int:
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]
        for key, v in payload.items():
            assert key == IsStr(regex=r"HandleResponse\w*Payload")
            assert v == {"title": "HandleResponsePayload", "type": "integer"}

    def test_pydantic_model_publisher(self):
        class User(pydantic.BaseModel):
            name: str = ""
            id: int

        broker = self.broker_class()

        @broker.publisher("test")
        async def handle(msg) -> User:
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == "User"
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
        async def handle(msg) -> int:
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]
        for key, v in payload.items():
            assert key == IsStr(regex=r"HandleResponse\w*Payload")
            assert v == {"title": "HandleResponsePayload", "type": "integer"}

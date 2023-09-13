from typing import Optional, Type

import pydantic
from dirty_equals import IsDict, IsStr

from faststream import FastStream
from faststream._compat import PYDANTIC_V2
from faststream.asyncapi.generate import get_app_schema
from faststream.broker.core.abc import BrokerUsecase


class FastAPICompatible:
    broker_class: Type[BrokerUsecase]

    def build_app(self, broker):
        """Patch it to test FastAPI scheme generation too"""
        return FastStream(broker)

    def test_custom_naming(self):
        broker = self.broker_class()

        @broker.subscriber("test", title="custom_name", description="test description")
        async def handle(msg):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()
        key = tuple(schema["channels"].keys())[0]

        assert key == "custom_name"
        assert schema["channels"][key]["description"] == "test description"

    def test_docstring_description(self):
        broker = self.broker_class()

        @broker.subscriber("test", title="custom_name")
        async def handle(msg):
            """test description"""

        schema = get_app_schema(self.build_app(broker)).to_jsonable()
        key = tuple(schema["channels"].keys())[0]

        assert key == "custom_name"
        assert schema["channels"][key]["description"] == "test description"

    def test_no_type(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(msg):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == IsStr(regex=r"Handle\w*Payload")
            assert v == {"title": key}

    def test_simple_type(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(msg: int):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]
        assert tuple(schema["channels"].values())[0].get("description") is None

        for key, v in payload.items():
            assert key == IsStr(regex=r"Handle\w*Payload")
            assert v == {"title": key, "type": "integer"}

    def test_simple_optional_type(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(msg: Optional[int]):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == IsStr(regex=r"Handle\w*Payload")
            assert v == IsDict(
                {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "title": key,
                }
            ) | IsDict(
                {  # TODO: remove when deprecating PydanticV1
                    "title": "HandleTestMsgPayload",
                    "type": "integer",
                }
            )

    def test_simple_type_with_default(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(msg: int = 1):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == IsStr(regex=r"Handle\w*Payload")
            assert v == {
                "default": 1,
                "title": key,
                "type": "integer",
            }

    def test_multi_args_no_type(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(msg, another):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == IsStr(regex=r"Handle\w*Payload")
            assert v == {
                "properties": {
                    "another": {"title": "Another"},
                    "msg": {"title": "Msg"},
                },
                "required": ["msg", "another"],
                "title": key,
                "type": "object",
            }

    def test_multi_args_with_type(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(msg: str, another: int):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == IsStr(regex=r"Handle\w*Payload")
            assert v == {
                "properties": {
                    "another": {"title": "Another", "type": "integer"},
                    "msg": {"title": "Msg", "type": "string"},
                },
                "required": ["msg", "another"],
                "title": key,
                "type": "object",
            }

    def test_multi_args_with_default(self):
        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(msg: str, another: Optional[int] = None):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == IsStr(regex=r"Handle\w*Payload")

            assert v == {
                "properties": {
                    "another": IsDict(
                        {
                            "anyOf": [{"type": "integer"}, {"type": "null"}],
                            "default": None,
                            "title": "Another",
                        }
                    )
                    | IsDict(
                        {  # TODO: remove when deprecating PydanticV1
                            "title": "Another",
                            "type": "integer",
                        }
                    ),
                    "msg": {"title": "Msg", "type": "string"},
                },
                "required": ["msg"],
                "title": key,
                "type": "object",
            }

    def test_pydantic_model(self):
        class User(pydantic.BaseModel):
            name: str = ""
            id: int

        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(user: User):
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

    def test_pydantic_model_mixed_regular(self):
        class User(pydantic.BaseModel):
            name: str = ""
            id: int

        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(user: User, description: str = ""):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == IsStr(regex=r"Handle\w*Payload")
            assert v == {
                "$defs": {
                    "User": {
                        "properties": {
                            "id": {"title": "Id", "type": "integer"},
                            "name": {
                                "default": "",
                                "title": "Name",
                                "type": "string",
                            },
                        },
                        "required": ["id"],
                        "title": "User",
                        "type": "object",
                    }
                },
                "properties": {
                    "description": {
                        "default": "",
                        "title": "Description",
                        "type": "string",
                    },
                    "user": {"$ref": "#/$defs/User"},
                },
                "required": ["user"],
                "title": key,
                "type": "object",
            } or v == {  # TODO: remove when deprecating PydanticV1
                "definitions": {
                    "User": {
                        "properties": {
                            "id": {"title": "Id", "type": "integer"},
                            "name": {"default": "", "title": "Name", "type": "string"},
                        },
                        "required": ["id"],
                        "title": "User",
                        "type": "object",
                    }
                },
                "properties": {
                    "description": {
                        "default": "",
                        "title": "Description",
                        "type": "string",
                    },
                    "user": {"$ref": "#/definitions/User"},
                },
                "required": ["user"],
                "title": key,
                "type": "object",
            }

    def test_pydantic_model_with_example(self):
        class User(pydantic.BaseModel):
            name: str = ""
            id: int

            if PYDANTIC_V2:
                model_config = {
                    "json_schema_extra": {"examples": [{"name": "john", "id": 1}]}
                }

            else:

                class Config:
                    schema_extra = {"examples": [{"name": "john", "id": 1}]}

        broker = self.broker_class()

        @broker.subscriber("test")
        async def handle(user: User):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == "User"
            assert v == {
                "examples": [{"id": 1, "name": "john"}],
                "properties": {
                    "id": {"title": "Id", "type": "integer"},
                    "name": {"default": "", "title": "Name", "type": "string"},
                },
                "required": ["id"],
                "title": "User",
                "type": "object",
            }

    def test_with_filter(self):
        class User(pydantic.BaseModel):
            name: str = ""
            id: int

        broker = self.broker_class()

        @broker.subscriber(  # pragma: no branch
            "test",
            filter=lambda m: m.content_type == "application/json",
        )
        async def handle(id: int):
            ...

        @broker.subscriber("test")
        async def handle_default(msg):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == IsStr(regex=r"Handle\w*Payload")
            assert v == {
                "oneOf": {
                    "HandleTestIdPayload": {
                        "title": "HandleTestIdPayload",
                        "type": "integer",
                    },
                    "HandleTestMsgPayload": {"title": "HandleTestMsgPayload"},
                }
            }


class ArgumentsTestcase(FastAPICompatible):
    def test_pydantic_field(self):
        broker = self.broker_class()

        @broker.subscriber("msg")
        async def msg(
            msg: pydantic.PositiveInt = pydantic.Field(
                1,
                description="some field",
                title="Perfect",
                examples=[1],
            ),
        ):
            ...

        schema = get_app_schema(self.build_app(broker)).to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == "Perfect"

            assert v == {
                "default": 1,
                "description": "some field",
                "examples": [1],
                "exclusiveMinimum": 0,
                "title": "Perfect",
                "type": "integer",
            }

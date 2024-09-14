from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union

import pydantic
from dirty_equals import IsDict, IsPartialDict, IsStr
from fast_depends import Depends
from fastapi import Depends as APIDepends
from typing_extensions import Annotated, Literal

from faststream import Context, FastStream
from faststream._internal._compat import PYDANTIC_V2
from faststream._internal.broker.broker import BrokerUsecase
from faststream._internal.fastapi import StreamRouter
from faststream.specification.asyncapi.generate import get_app_schema
from tests.marks import pydantic_v2


class FastAPICompatible:
    broker_factory: Union[BrokerUsecase, StreamRouter]
    dependency_builder = staticmethod(APIDepends)

    def build_app(self, broker):
        """Patch it to test FastAPI scheme generation too."""
        return FastStream(broker)

    def test_custom_naming(self):
        broker = self.broker_factory()

        @broker.subscriber("test", title="custom_name", description="test description")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert key == "custom_name"
        assert schema["channels"][key]["description"] == "test description"

    def test_slash_in_title(self):
        broker = self.broker_factory()

        @broker.subscriber("test", title="/")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        assert tuple(schema["channels"].keys())[0] == "."
        assert schema["channels"]["."]["address"] == "/"

        assert tuple(schema["operations"].keys())[0] == ".Subscribe"

        assert tuple(schema["components"]["messages"].keys())[0] == ".:SubscribeMessage"
        assert schema["components"]["messages"][".:SubscribeMessage"]["title"] == "/:SubscribeMessage"
        assert tuple(schema["components"]["schemas"].keys())[0] == ".:Message:Payload"
        assert schema["components"]["schemas"][".:Message:Payload"]["title"] == "/:Message:Payload"

    def test_docstring_description(self):
        broker = self.broker_factory()

        @broker.subscriber("test", title="custom_name")
        async def handle(msg):
            """Test description."""

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()
        key = tuple(schema["channels"].keys())[0]  # noqa: RUF015

        assert key == "custom_name"
        assert schema["channels"][key]["description"] == "Test description.", schema[
            "channels"
        ][key]["description"]

    def test_empty(self):
        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == "EmptyPayload"
            assert v == {
                "title": key,
                "type": "null",
            }

    def test_no_type(self):
        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(msg): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == "Handle:Message:Payload"
            assert v == {"title": key}

    def test_simple_type(self):
        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(msg: int): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        payload = schema["components"]["schemas"]
        assert next(iter(schema["channels"].values())).get("description") is None

        for key, v in payload.items():
            assert key == "Handle:Message:Payload"
            assert v == {"title": key, "type": "integer"}

    def test_simple_optional_type(self):
        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(msg: Optional[int]): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == "Handle:Message:Payload"
            assert v == IsDict(
                {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "title": key,
                }
            ) | IsDict(
                {  # TODO: remove when deprecating PydanticV1
                    "title": key,
                    "type": "integer",
                }
            ), v

    def test_simple_type_with_default(self):
        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(msg: int = 1): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == "Handle:Message:Payload"
            assert v == {
                "default": 1,
                "title": key,
                "type": "integer",
            }

    def test_multi_args_no_type(self):
        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(msg, another): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == "Handle:Message:Payload"
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
        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(msg: str, another: int): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == "Handle:Message:Payload"
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
        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(msg: str, another: Optional[int] = None): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == "Handle:Message:Payload"

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

    def test_dataclass(self):
        @dataclass
        class User:
            id: int
            name: str = ""

        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(user: User): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

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

    def test_pydantic_model(self):
        class User(pydantic.BaseModel):
            name: str = ""
            id: int

        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(user: User): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

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

    def test_pydantic_model_with_enum(self):
        class Status(str, Enum):
            registered = "registered"
            banned = "banned"

        class User(pydantic.BaseModel):
            name: str = ""
            id: int
            status: Status

        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(user: User): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        payload = schema["components"]["schemas"]

        assert payload == {
            "Status": IsPartialDict(
                {
                    "enum": ["registered", "banned"],
                    "title": "Status",
                    "type": "string",
                }
            ),
            "User": {
                "properties": {
                    "id": {"title": "Id", "type": "integer"},
                    "name": {"default": "", "title": "Name", "type": "string"},
                    "status": {"$ref": "#/components/schemas/Status"},
                },
                "required": ["id", "status"],
                "title": "User",
                "type": "object",
            },
        }, payload

    def test_pydantic_model_mixed_regular(self):
        class Email(pydantic.BaseModel):
            addr: str

        class User(pydantic.BaseModel):
            name: str = ""
            id: int
            email: Email

        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(user: User, description: str = ""): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        payload = schema["components"]["schemas"]

        assert payload == {
            "Email": {
                "title": "Email",
                "type": "object",
                "properties": {"addr": {"title": "Addr", "type": "string"}},
                "required": ["addr"],
            },
            "User": {
                "title": "User",
                "type": "object",
                "properties": {
                    "name": {"title": "Name", "default": "", "type": "string"},
                    "id": {"title": "Id", "type": "integer"},
                    "email": {"$ref": "#/components/schemas/Email"},
                },
                "required": ["id", "email"],
            },
            "Handle:Message:Payload": {
                "title": "Handle:Message:Payload",
                "type": "object",
                "properties": {
                    "user": {"$ref": "#/components/schemas/User"},
                    "description": {
                        "title": "Description",
                        "default": "",
                        "type": "string",
                    },
                },
                "required": ["user"],
            },
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
                    schema_extra = {"examples": [{"name": "john", "id": 1}]}  # noqa: RUF012

        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(user: User): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

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

        broker = self.broker_factory()

        sub = broker.subscriber("test")

        @sub(  # pragma: no branch
            filter=lambda m: m.content_type == "application/json",
        )
        async def handle(id: int): ...

        @sub
        async def handle_default(msg): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        assert (
            len(
                next(iter(schema["components"]["messages"].values()))["payload"][
                    "oneOf"
                ]
            )
            == 2
        )

        payload = schema["components"]["schemas"]

        assert "Handle:Message:Payload" in list(payload.keys())
        assert "HandleDefault:Message:Payload" in list(payload.keys())

    def test_ignores_depends(self):
        broker = self.broker_factory()

        def dep(name: str = ""):
            return name

        def dep2(name2: str):
            return name2

        dependencies = (self.dependency_builder(dep2),)
        message = self.dependency_builder(dep)

        @broker.subscriber("test", dependencies=dependencies)
        async def handle(id: int, message=message): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert key == "Handle:Message:Payload"
            assert v == {
                "properties": {
                    "id": {"title": "Id", "type": "integer"},
                    "name": {"default": "", "title": "Name", "type": "string"},
                    "name2": {"title": "Name2", "type": "string"},
                },
                "required": ["id", "name2"],
                "title": key,
                "type": "object",
            }, v

    @pydantic_v2
    def test_descriminator(self):
        class Sub2(pydantic.BaseModel):
            type: Literal["sub2"]

        class Sub(pydantic.BaseModel):
            type: Literal["sub"]

        descriminator = Annotated[
            Union[Sub2, Sub], pydantic.Field(discriminator="type")
        ]

        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(user: descriminator): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()
        key = next(iter(schema["components"]["messages"].keys()))
        assert key == IsStr(regex=r"test[\w:]*:Handle:SubscribeMessage")

        assert schema["components"] == {
            "messages": {
                key: {
                    "title": key,
                    "correlationId": {"location": "$message.header#/correlation_id"},
                    "payload": {"$ref": "#/components/schemas/Handle:Message:Payload"},
                }
            },
            "schemas": {
                "Sub": {
                    "properties": {
                        "type": IsPartialDict({"const": "sub", "title": "Type"})
                    },
                    "required": ["type"],
                    "title": "Sub",
                    "type": "object",
                },
                "Sub2": {
                    "properties": {
                        "type": IsPartialDict({"const": "sub2", "title": "Type"})
                    },
                    "required": ["type"],
                    "title": "Sub2",
                    "type": "object",
                },
                "Handle:Message:Payload": {
                    "discriminator": "type",
                    "oneOf": [
                        {"$ref": "#/components/schemas/Sub2"},
                        {"$ref": "#/components/schemas/Sub"},
                    ],
                    "title": "Handle:Message:Payload",
                },
            },
        }, schema["components"]

    @pydantic_v2
    def test_nested_descriminator(self):
        class Sub2(pydantic.BaseModel):
            type: Literal["sub2"]

        class Sub(pydantic.BaseModel):
            type: Literal["sub"]

        class Model(pydantic.BaseModel):
            msg: Union[Sub2, Sub] = pydantic.Field(..., discriminator="type")

        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(user: Model): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        key = next(iter(schema["components"]["messages"].keys()))
        assert key == IsStr(regex=r"test[\w:]*:Handle:SubscribeMessage")
        assert schema["components"] == {
            "messages": {
                key: {
                    "title": key,
                    "correlationId": {"location": "$message.header#/correlation_id"},
                    "payload": {"$ref": "#/components/schemas/Model"},
                }
            },
            "schemas": {
                "Sub": {
                    "properties": {
                        "type": IsPartialDict({"const": "sub", "title": "Type"})
                    },
                    "required": ["type"],
                    "title": "Sub",
                    "type": "object",
                },
                "Sub2": {
                    "properties": {
                        "type": IsPartialDict({"const": "sub2", "title": "Type"})
                    },
                    "required": ["type"],
                    "title": "Sub2",
                    "type": "object",
                },
                "Model": {
                    "properties": {
                        "msg": {
                            "discriminator": "type",
                            "oneOf": [
                                {"$ref": "#/components/schemas/Sub2"},
                                {"$ref": "#/components/schemas/Sub"},
                            ],
                            "title": "Msg",
                        }
                    },
                    "required": ["msg"],
                    "title": "Model",
                    "type": "object",
                },
            },
        }, schema["components"]


class ArgumentsTestcase(FastAPICompatible):
    dependency_builder = staticmethod(Depends)

    def test_pydantic_field(self):
        broker = self.broker_factory()

        @broker.subscriber("msg")
        async def msg(
            msg: pydantic.PositiveInt = pydantic.Field(
                1,
                description="some field",
                title="Perfect",
                examples=[1],
            ),
        ): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

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

    def test_ignores_custom_field(self):
        broker = self.broker_factory()

        @broker.subscriber("test")
        async def handle(id: int, user: Optional[str] = None, message=Context()): ...

        schema = get_app_schema(self.build_app(broker), version="3.0.0").to_jsonable()

        payload = schema["components"]["schemas"]

        for key, v in payload.items():
            assert v == IsDict(
                {
                    "properties": {
                        "id": {"title": "Id", "type": "integer"},
                        "user": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                            "default": None,
                            "title": "User",
                        },
                    },
                    "required": ["id"],
                    "title": key,
                    "type": "object",
                }
            ) | IsDict(  # TODO: remove when deprecating PydanticV1
                {
                    "properties": {
                        "id": {"title": "Id", "type": "integer"},
                        "user": {"title": "User", "type": "string"},
                    },
                    "required": ["id"],
                    "title": "Handle:Message:Payload",
                    "type": "object",
                }
            )

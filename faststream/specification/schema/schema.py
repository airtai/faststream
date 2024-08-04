from typing import Any

from pydantic import BaseModel

from faststream._compat import model_to_json, model_to_jsonable
from faststream.specification.asyncapi.base.schema import BaseInfo
from faststream.specification.schema.channel import Channel
from faststream.specification.schema.components import Components
from faststream.specification.schema.docs import ExternalDocs, ExternalDocsDict
from faststream.specification.schema.info import Info
from faststream.specification.schema.servers import Server
from faststream.specification.schema.tag import Tag
from faststream._compat import model_to_json, model_to_jsonable


class BaseSchema(BaseModel):
    """A class to represent a schema.

    Attributes:
        info : information about the schema

    Methods:
        to_jsonable() -> Any: Convert the schema to a JSON-serializable object.
        to_json() -> str: Convert the schema to a JSON string.
        to_yaml() -> str: Convert the schema to a YAML string.

    """

    info: BaseInfo

    def to_jsonable(self) -> Any:
        """Convert the schema to a JSON-serializable object."""
        return model_to_jsonable(
            self,
            by_alias=True,
            exclude_none=True,
        )

    def to_json(self) -> str:
        """Convert the schema to a JSON string."""
        return model_to_json(
            self,
            by_alias=True,
            exclude_none=True,
        )

    def to_yaml(self) -> str:
        """Convert the schema to a YAML string."""
        from io import StringIO

        import yaml

        io = StringIO(initial_value="", newline="\n")
        yaml.dump(self.to_jsonable(), io, sort_keys=False)
        return io.getvalue()

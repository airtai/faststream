from typing import Any, Protocol, runtime_checkable

from faststream.specification.asyncapi.base.schema import BaseSchema


@runtime_checkable
class AsyncAPIProto(Protocol):
    def json(self) -> str:
        ...

    def jsonable(self) -> Any:
        ...

    def yaml(self) -> str:
        ...

    def schema(self) -> BaseSchema:
        ...

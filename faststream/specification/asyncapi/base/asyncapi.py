from abc import abstractmethod
from typing import Any, Protocol

from faststream.specification.asyncapi.base.schema import BaseSchema


class AsyncAPIProto(Protocol):
    def json(self) -> str:
        ...

    def jsonable(self) -> Any:
        ...

    def yaml(self) -> str:
        ...

    def schema(self) -> BaseSchema:
        ...

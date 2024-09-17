from abc import abstractmethod
from typing import Any, Protocol


class AsyncAPIProto(Protocol):
    @abstractmethod
    def json(self) -> str:
        ...

    @abstractmethod
    def jsonable(self) -> Any:
        ...

    @abstractmethod
    def yaml(self) -> str:
        ...

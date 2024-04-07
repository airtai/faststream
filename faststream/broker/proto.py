from abc import abstractmethod
from typing import Hashable, Protocol


class SetupAble(Protocol):
    @abstractmethod
    def setup(self) -> None: ...


class EndpointProto(SetupAble, Hashable, Protocol):
    @abstractmethod
    def add_prefix(self, prefix: str) -> None: ...

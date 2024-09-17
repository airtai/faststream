from abc import abstractmethod
from typing import Protocol, Any, Optional, Union, Sequence

from faststream._internal.basic_types import AnyHttpUrl, AnyDict
from faststream._internal.broker.broker import BrokerUsecase
from faststream.specification.schema.contact import Contact, ContactDict
from faststream.specification.schema.docs import ExternalDocs, ExternalDocsDict
from faststream.specification.schema.license import LicenseDict, License
from faststream.specification.schema.tag import Tag


class AsyncAPI(Protocol):
    @abstractmethod
    def json(self) -> str:
        ...

    @abstractmethod
    def jsonable(self) -> Any:
        ...

    @abstractmethod
    def yaml(self) -> str:
        ...

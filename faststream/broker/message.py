from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar, Union
from uuid import uuid4

from faststream.types import AnyDict, DecodedMessage

Msg = TypeVar("Msg")


@dataclass
class ABCStreamMessage(Generic[Msg]):
    raw_message: Msg

    body: Union[bytes, Any]
    decoded_body: Optional[DecodedMessage] = None

    content_type: Optional[str] = None
    reply_to: str = ""
    headers: AnyDict = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid4()))  # pragma: no cover
    correlation_id: str = field(
        default_factory=lambda: str(uuid4())
    )  # pragma: no cover

    processed: bool = False


class SyncStreamMessage(ABCStreamMessage[Msg]):
    @abstractmethod
    def ack(self, **kwargs: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def nack(self, **kwargs: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def reject(self, **kwargs: Any) -> None:
        raise NotImplementedError()


class StreamMessage(ABCStreamMessage[Msg]):
    @abstractmethod
    async def ack(self, **kwargs: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def nack(self, **kwargs: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def reject(self, **kwargs: Any) -> None:
        raise NotImplementedError()

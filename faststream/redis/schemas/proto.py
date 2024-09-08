from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Union

from faststream.exceptions import SetupError
from faststream.specification.proto import SpecificationProto

if TYPE_CHECKING:
    from faststream.redis.schemas import ListSub, PubSub, StreamSub
    from faststream.specification.schema.bindings import redis


class RedisAsyncAPIProtocol(SpecificationProto):
    @property
    @abstractmethod
    def channel_binding(self) -> "redis.ChannelBinding": ...

    @abstractmethod
    def get_payloads(self) -> Any: ...


def validate_options(
    *,
    channel: Union["PubSub", str, None],
    list: Union["ListSub", str, None],
    stream: Union["StreamSub", str, None],
) -> None:
    if all((channel, list)):
        raise SetupError("You can't use `PubSub` and `ListSub` both")
    elif all((channel, stream)):
        raise SetupError("You can't use `PubSub` and `StreamSub` both")
    elif all((list, stream)):
        raise SetupError("You can't use `ListSub` and `StreamSub` both")

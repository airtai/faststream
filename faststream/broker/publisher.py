from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, List, Optional
from unittest.mock import MagicMock

from faststream.asyncapi.base import AsyncAPIOperation
from faststream.broker.types import MsgType, P_HandlerParams, T_HandlerReturn
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.types import SendableMessage


@dataclass
class BasePublisher(AsyncAPIOperation, Generic[MsgType]):
    title: Optional[str] = field(default=None)
    _description: Optional[str] = field(default=None)
    _fake_handler: bool = field(default=False)

    calls: List[Callable[..., Any]] = field(
        init=False, default_factory=list, repr=False
    )
    mock: MagicMock = field(init=False, default_factory=MagicMock, repr=False)

    @property
    def description(self) -> Optional[str]:
        return self._description

    def __call__(
        self,
        func: Callable[P_HandlerParams, T_HandlerReturn],
    ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
        handler_call: HandlerCallWrapper[
            MsgType, P_HandlerParams, T_HandlerReturn
        ] = HandlerCallWrapper(func)
        handler_call._publishers.append(self)
        self.calls.append(handler_call._original_call)
        return handler_call

    @abstractmethod
    async def publish(
        self,
        message: SendableMessage,
        correlation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[SendableMessage]:
        raise NotImplementedError()

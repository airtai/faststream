from typing import (
    Callable,
    Iterable,
    Optional,
    Protocol,
    Union,
    overload,
)

from fast_depends.dependencies import Depends

from faststream.broker.message import StreamMessage
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    MsgType,
    P_HandlerParams,
    SubscriberMiddleware,
    T_HandlerReturn,
)
from faststream.broker.wrapper.call import HandlerCallWrapper


class WrapperProto(Protocol[MsgType]):
    """Annotation class to represent @subscriber return type."""

    @overload
    def __call__(
        self,
        func: None = None,
        *,
        filter: Optional["Filter[StreamMessage[MsgType]]"] = None,
        parser: Optional["CustomParser[MsgType]"] = None,
        decoder: Optional["CustomDecoder[StreamMessage[MsgType]]"] = None,
        middlewares: Iterable["SubscriberMiddleware"] = (),
        dependencies: Iterable["Depends"] = (),
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
    ]:
        ...

    @overload
    def __call__(
        self,
        func: Callable[P_HandlerParams, T_HandlerReturn],
        *,
        filter: Optional[Filter[StreamMessage[MsgType]]] = None,
        parser: Optional[CustomParser[MsgType]] = None,
        decoder: Optional[CustomDecoder[StreamMessage[MsgType]]] = None,
        middlewares: Iterable[SubscriberMiddleware] = (),
        dependencies: Iterable[Depends] = (),
    ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
        ...

    def __call__(
        self,
        func: Optional[Callable[P_HandlerParams, T_HandlerReturn]] = None,
        *,
        filter: Optional[Filter[StreamMessage[MsgType]]] = None,
        parser: Optional[CustomParser[MsgType]] = None,
        decoder: Optional[CustomDecoder[StreamMessage[MsgType]]] = None,
        middlewares: Iterable[SubscriberMiddleware] = (),
        dependencies: Iterable[Depends] = (),
    ) -> Union[
        HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
        Callable[
            [Callable[P_HandlerParams, T_HandlerReturn]],
            HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
        ],
    ]:
        ...

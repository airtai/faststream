from collections.abc import Iterable, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Protocol,
    Union,
    overload,
)

from faststream._internal.types import (
    CustomCallable,
    Filter,
    MsgType,
    P_HandlerParams,
    SubscriberMiddleware,
    T_HandlerReturn,
)

if TYPE_CHECKING:
    from fast_depends.dependencies import Dependant

    from .call import HandlerCallWrapper


class WrapperProto(Protocol[MsgType]):
    """Annotation class to represent @subscriber return type."""

    @overload
    def __call__(
        self,
        func: None = None,
        *,
        filter: Optional["Filter[Any]"] = None,
        parser: Optional["CustomCallable"] = None,
        decoder: Optional["CustomCallable"] = None,
        middlewares: Sequence["SubscriberMiddleware[Any]"] = (),
        dependencies: Iterable["Dependant"] = (),
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]",
    ]: ...

    @overload
    def __call__(
        self,
        func: Union[
            Callable[P_HandlerParams, T_HandlerReturn],
            "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]",
        ],
        *,
        filter: Optional["Filter[Any]"] = None,
        parser: Optional["CustomCallable"] = None,
        decoder: Optional["CustomCallable"] = None,
        middlewares: Sequence["SubscriberMiddleware[Any]"] = (),
        dependencies: Iterable["Dependant"] = (),
    ) -> "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]": ...

    def __call__(
        self,
        func: Union[
            Callable[P_HandlerParams, T_HandlerReturn],
            "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]",
            None,
        ] = None,
        *,
        filter: Optional["Filter[Any]"] = None,
        parser: Optional["CustomCallable"] = None,
        decoder: Optional["CustomCallable"] = None,
        middlewares: Sequence["SubscriberMiddleware[Any]"] = (),
        dependencies: Iterable["Dependant"] = (),
    ) -> Union[
        "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]",
        Callable[
            [Callable[P_HandlerParams, T_HandlerReturn]],
            "HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]",
        ],
    ]: ...

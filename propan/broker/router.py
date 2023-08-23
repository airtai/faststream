from abc import abstractmethod
from typing import Any, Callable, Dict, Generic, List, Sequence, Tuple

from propan.broker.publisher import BasePublisher
from propan.broker.types import MsgType, P_HandlerParams, T_HandlerReturn
from propan.broker.wrapper import HandlerCallWrapper
from propan.types import AnyDict, SendableMessage


class BrokerRoute(Generic[MsgType, T_HandlerReturn]):
    call: Callable[..., T_HandlerReturn]
    args: Tuple[Any, ...]
    kwargs: AnyDict

    def __init__(
        self,
        call: Callable[..., T_HandlerReturn],
        *args: Any,
        **kwargs: Any,
    ):
        self.call = call
        self.args = args
        self.kwargs = kwargs


class BrokerRouter(Generic[MsgType]):
    prefix: str
    _handlers: List[BrokerRoute[MsgType, Any]]
    _publishers: Dict[Any, BrokerRoute[MsgType, Any]]

    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[BrokerRoute[MsgType, SendableMessage]] = (),
    ):
        self.prefix = prefix
        self._handlers = list(handlers)
        self._publishers = {}

    @abstractmethod
    def subscriber(
        self,
        subj: str,
        *args: Any,
        **kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
    ]:
        raise NotImplementedError()

    def _wrap_subscriber(
        self, *args: Any, **kwargs: Any
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
    ]:
        def router_subscriber_wrapper(
            func: Callable[P_HandlerParams, T_HandlerReturn]
        ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
            wrapped_func: HandlerCallWrapper[
                MsgType, P_HandlerParams, T_HandlerReturn
            ] = HandlerCallWrapper(func)
            route: BrokerRoute[MsgType, T_HandlerReturn] = BrokerRoute(
                wrapped_func,
                *args,
                **kwargs,
            )
            self._handlers.append(route)
            return wrapped_func

        return router_subscriber_wrapper

    @abstractmethod
    def publisher(
        self,
        subj: str,
        *args: Any,
        **kwargs: Any,
    ) -> BasePublisher[MsgType]:
        raise NotImplementedError()

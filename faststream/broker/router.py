from abc import abstractmethod
from typing import (
    Any,
    AsyncContextManager,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

from fast_depends.dependencies import Depends

from faststream.broker.message import StreamMessage
from faststream.broker.publisher import BasePublisher
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.types import AnyDict, SendableMessage

PublisherKeyType = TypeVar("PublisherKeyType")


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


class BrokerRouter(Generic[PublisherKeyType, MsgType]):
    prefix: str
    _handlers: List[BrokerRoute[MsgType, Any]]
    _publishers: Dict[PublisherKeyType, BasePublisher[MsgType]]

    @staticmethod
    @abstractmethod
    def _get_publisher_key(publisher: BasePublisher[MsgType]) -> PublisherKeyType:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def _update_publisher_prefix(
        prefix: str,
        publisher: BasePublisher[MsgType],
    ) -> BasePublisher[MsgType]:
        raise NotImplementedError()

    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[BrokerRoute[MsgType, SendableMessage]] = (),
        dependencies: Sequence[Depends] = (),
        middlewares: Optional[
            Sequence[
                Callable[
                    [StreamMessage[MsgType]],
                    AsyncContextManager[None],
                ]
            ]
        ] = None,
        parser: Optional[CustomParser[MsgType]] = None,
        decoder: Optional[CustomDecoder[MsgType]] = None,
    ):
        self.prefix = prefix
        self._handlers = list(handlers)
        self._publishers = {}
        self._dependencies = dependencies
        self._middlewares = middlewares
        self._parser = parser
        self._decoder = decoder

    @abstractmethod
    def subscriber(
        self,
        subj: str,
        *args: Any,
        dependencies: Sequence[Depends] = (),
        middlewares: Optional[
            Sequence[
                Callable[
                    [StreamMessage[MsgType]],
                    AsyncContextManager[None],
                ]
            ]
        ] = None,
        parser: Optional[CustomParser[MsgType]] = None,
        decoder: Optional[CustomDecoder[MsgType]] = None,
        **kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
    ]:
        raise NotImplementedError()

    def _wrap_subscriber(
        self,
        *args: Any,
        dependencies: Sequence[Depends] = (),
        middlewares: Optional[
            Sequence[
                Callable[
                    [StreamMessage[MsgType]],
                    AsyncContextManager[None],
                ]
            ]
        ] = None,
        parser: Optional[CustomParser[MsgType]] = None,
        decoder: Optional[CustomDecoder[MsgType]] = None,
        **kwargs: Any,
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
                dependencies=(*self._dependencies, *dependencies),
                middlewares=(*(self._middlewares or ()), *(middlewares or ())) or None,
                parser=parser or self._parser,
                decoder=decoder or self._decoder,
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

    def include_router(self, router: "BrokerRouter[PublisherKeyType, MsgType]") -> None:
        for h in router._handlers:
            self.subscriber(*h.args, **h.kwargs)(h.call)

        for p in router._publishers.values():
            p = self._update_publisher_prefix(self.prefix, p)
            key = self._get_publisher_key(p)
            self._publishers[key] = self._publishers.get(key, p)

    def include_routers(
        self, *routers: "BrokerRouter[PublisherKeyType, MsgType]"
    ) -> None:
        for r in routers:
            self.include_router(r)

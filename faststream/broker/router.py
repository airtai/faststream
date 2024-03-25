from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
)

from fast_depends.dependencies import Depends

from faststream.broker.core.broker import default_filter
from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.core.publisher import BasePublisher
from faststream.broker.types import (
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.types import AnyDict

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from faststream.broker.core.handler_wrapper_mixin import (
        WrapExtraKwargs,
        WrapperProtocol,
    )
    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        BrokerMiddleware,
        CustomDecoder,
        CustomParser,
        Filter,
        SubscriberMiddleware,
    )


class BrokerRoute:
    """A generic class to represent a broker route.

    Attributes:
        call : callable object representing the route
        args : tuple of arguments for the route
        kwargs : dictionary of keyword arguments for the route

    Args:
        call : callable object representing the route
        *args : variable length arguments for the route
        **kwargs : variable length keyword arguments for the route
    """

    call: Callable[..., Any]
    args: Tuple[Any, ...]
    kwargs: AnyDict

    def __init__(
        self,
        call: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize a callable object with arguments and keyword arguments.

        Args:
            call: A callable object.
            *args: Positional arguments to be passed to the callable object.
            **kwargs: Keyword arguments to be passed to the callable object.
        """
        self.call = call
        self.args = args
        self.kwargs = kwargs


class BrokerRouter(Generic[MsgType]):
    """A generic class representing a broker router.

    Attributes:
        prefix : prefix for the router
        _handlers : list of broker routes
        _publishers : dictionary of publishers

    Methods:
        _update_publisher_prefix : abstract method to update the publisher prefix
        __init__ : constructor method
        subscriber : abstract method to define a subscriber
        _wrap_subscriber : method to wrap a subscriber function
        publisher : abstract method to define a publisher
        include_router : method to include a router
        include_routers : method to include multiple routers
    """

    prefix: str
    _handlers: List[BrokerRoute]
    _publishers: Mapping[int, BasePublisher[MsgType]]

    @staticmethod
    @abstractmethod
    def _update_publisher_prefix(
        prefix: str,
        publisher: BasePublisher[MsgType],
    ) -> BasePublisher[MsgType]:
        """Updates the publisher prefix.

        Args:
            prefix: The new prefix to be set.
            publisher: The publisher to update.

        Returns:
            The updated publisher.

        Raises:
            NotImplementedError: If the function is not implemented.
        """
        raise NotImplementedError()

    def __init__(
        self,
        prefix: str = "",
        handlers: Iterable[BrokerRoute] = (),
        dependencies: Iterable[Depends] = (),
        middlewares: Iterable["BrokerMiddleware[MsgType]"] = (),
        parser: Optional["CustomParser[MsgType]"] = None,
        decoder: Optional["CustomDecoder[StreamMessage[MsgType]]"] = None,
        include_in_schema: Optional[bool] = None,
    ) -> None:
        self.prefix = prefix
        self.include_in_schema = include_in_schema
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
        *,
        filter: "Filter[StreamMessage[MsgType]]" = default_filter,
        decoder: Optional["CustomDecoder[StreamMessage[MsgType]]"] = None,
        parser: Optional["CustomParser[MsgType]"] = None,
        dependencies: Iterable["Depends"] = (),
        middlewares: Iterable["SubscriberMiddleware"] = (),
        raw: bool = False,
        no_ack: bool = False,
        retry: Union[bool, int] = False,
        **kwargs: "Unpack[WrapExtraKwargs]"
    ) -> "WrapperProtocol[MsgType]":
        """A function to subscribe to a subject.

        Args:
            subj : subject to subscribe to
            *args : additional arguments
            dependencies : sequence of dependencies
            middlewares : optional sequence of middlewares
            parser : optional custom parser
            decoder : optional custom decoder
            include_in_schema : whether to include the object in the schema
            **kwargs : additional keyword arguments

        Returns:
            A callable handler function

        Raises:
            NotImplementedError: If the function is not implemented
        """
        raise NotImplementedError()

    def _wrap_subscriber(
        self,
        *args: Any,
        dependencies: Iterable[Depends] = (),
        middlewares: Iterable["SubscriberMiddleware"] = (),
        parser: Optional["CustomParser[MsgType]"] = None,
        decoder: Optional["CustomDecoder[StreamMessage[MsgType]]"] = None,
        include_in_schema: bool = True,
        **kwargs: Any,
    ) -> "WrapperProtocol[MsgType]":
        """This is a function named `_wrap_subscriber` that returns a callable object. It is used as a decorator for another function.

        Args:
            *args: Variable length arguments
            dependencies: Sequence of dependencies
            middlewares: Optional sequence of middlewares
            parser: Optional custom parser
            decoder: Optional custom decoder
            include_in_schema: Whether to include the object in the schema
            **kwargs: Variable length keyword arguments

        Returns:
            A callable object that wraps the decorated function
        """

        def router_subscriber_wrapper(
            func: Callable[P_HandlerParams, T_HandlerReturn],
        ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
            """Wraps a function with a router subscriber.

            Args:
                func: The function to be wrapped.

            Returns:
                The wrapped function.
            """
            wrapped_func = HandlerCallWrapper[
                MsgType, P_HandlerParams, T_HandlerReturn
            ](func)
            route = BrokerRoute(
                wrapped_func,
                *args,
                dependencies=(*self._dependencies, *dependencies),
                middlewares=(*self._middlewares, *middlewares),
                parser=parser or self._parser,
                decoder=decoder or self._decoder,
                include_in_schema=self.solve_include_in_schema(include_in_schema),
                **kwargs,
            )
            self._handlers.append(route)
            return wrapped_func

        return router_subscriber_wrapper

    def solve_include_in_schema(self, include_in_schema: bool) -> bool:
        if self.include_in_schema is None or self.include_in_schema:
            return include_in_schema
        else:
            return self.include_in_schema

    @abstractmethod
    def publisher(self) -> BasePublisher[MsgType]:
        raise NotImplementedError()

    def include_router(self, router: "BrokerRouter[Any]") -> None:
        """Includes a router in the current object."""
        for h in router._handlers:
            self.subscriber(*h.args, **h.kwargs)(h.call)

        for p in router._publishers.values():
            p = self._update_publisher_prefix(self.prefix, p)

            if (key := hash(p)) not in self._publishers:
                p.include_in_schema = self.solve_include_in_schema(p.include_in_schema)
                p.middlewares = (
                    *(m(None).publish_scope for m in self._middlewares),
                    *p.middlewares,
                )

                self._publishers = {
                    **self._publishers,
                    key: p
                }

    def include_routers(
        self,
        *routers: "BrokerRouter[MsgType]",
    ) -> None:
        """Includes routers in the object.

        Args:
            *routers: Variable length argument list of routers to include.

        Returns:
            None
        """
        for r in routers:
            self.include_router(r)

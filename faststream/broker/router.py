from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Optional,
)

from faststream.broker.core.abc import ABCBroker
from faststream.broker.types import MsgType

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends

    from faststream.broker.types import (
        BrokerMiddleware,
        CustomCallable,
    )
    from faststream.types import AnyDict


class ArgsContainer:
    """Class to store any arguments."""

    args: Iterable[Any]
    kwargs: "AnyDict"

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs


class SubscriberRoute(ArgsContainer):
    """A generic class to represent a broker route."""

    call: Callable[..., Any]
    publishers: Iterable[Any]

    def __init__(
        self,
        call: Callable[..., Any],
        *args: Any,
        publishers: Iterable[ArgsContainer] = (),
        **kwargs: Any,
    ) -> None:
        """Initialize a callable object with arguments and keyword arguments."""
        self.call = call
        self.publishers = publishers

        super().__init__(*args, **kwargs)


class BrokerRouter(ABCBroker[MsgType]):
    """A generic class representing a broker router."""

    def __init__(
        self,
        *,
        handlers: Iterable[SubscriberRoute],
        # base options
        prefix: str,
        dependencies: Iterable["Depends"],
        middlewares: Iterable["BrokerMiddleware[MsgType]"],
        parser: Optional["CustomCallable"],
        decoder: Optional["CustomCallable"],
        include_in_schema: Optional[bool],
    ) -> None:
        super().__init__(
            prefix=prefix,
            dependencies=dependencies,
            middlewares=middlewares,
            parser=parser,
            decoder=decoder,
            include_in_schema=include_in_schema,
        )

        for h in handlers:
            call = h.call

            for p in h.publishers:
                call = self.publisher(*p.args, **p.kwargs)(call)

            self.subscriber(*h.args, **h.kwargs)(call)

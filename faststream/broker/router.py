from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Optional,
)

from fast_depends.dependencies import Depends

from faststream.broker.core.abc import ABCBroker
from faststream.broker.types import (
    MsgType,
)
from faststream.types import AnyDict

if TYPE_CHECKING:
    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        BrokerMiddleware,
        CustomDecoder,
        CustomParser,
    )


class SubscriberRoute:
    """A generic class to represent a broker route."""

    call: Callable[..., Any]
    args: Iterable[Any]
    kwargs: AnyDict

    def __init__(
        self,
        call: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize a callable object with arguments and keyword arguments."""
        self.call = call
        self.args = args
        self.kwargs = kwargs


class BrokerRouter(ABCBroker[MsgType]):
    """A generic class representing a broker router."""

    def __init__(
        self,
        *,
        handlers: Iterable[SubscriberRoute],
        # base options
        prefix: str,
        dependencies: Iterable[Depends],
        middlewares: Iterable["BrokerMiddleware[MsgType]"],
        parser: Optional["CustomParser[MsgType]"],
        decoder: Optional["CustomDecoder[StreamMessage[MsgType]]"],
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
            self.subscriber(*h.args, **h.kwargs)(h.call)

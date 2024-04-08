from contextlib import AsyncExitStack
from itertools import chain
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Iterable, Optional

from faststream.broker.publisher.proto import BasePublisherProto

if TYPE_CHECKING:
    from faststream.broker.types import PublisherMiddleware
    from faststream.types import AnyDict, SendableMessage


class FakePublisher(BasePublisherProto):
    """Publisher Interface implementation to use as RPC or REPLY TO publisher."""

    def __init__(
        self,
        method: Callable[..., Awaitable["SendableMessage"]],
        *,
        publish_kwargs: "AnyDict",
        middlewares: Iterable["PublisherMiddleware"] = (),
    ) -> None:
        """Initialize an object."""
        self.method = method
        self.publish_kwargs = publish_kwargs
        self.middlewares = middlewares

    async def publish(
        self,
        message: "SendableMessage",
        *,
        correlation_id: Optional[str] = None,
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
        **kwargs: Any,
    ) -> Any:
        """Publish a message."""
        publish_kwargs = {
            "correlation_id": correlation_id,
            **self.publish_kwargs,
            **kwargs,
        }

        async with AsyncExitStack() as stack:
            for m in chain(_extra_middlewares, self.middlewares):
                message = await stack.enter_async_context(m(message, **publish_kwargs))

            return await self.method(message, **publish_kwargs)

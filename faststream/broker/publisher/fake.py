from functools import partial
from itertools import chain
from typing import TYPE_CHECKING, Any, Optional, Sequence

from faststream.broker.publisher.proto import BasePublisherProto

if TYPE_CHECKING:
    from faststream.broker.types import PublisherMiddleware
    from faststream.types import AnyDict, AsyncFunc, SendableMessage


class FakePublisher(BasePublisherProto):
    """Publisher Interface implementation to use as RPC or REPLY TO publisher."""

    def __init__(
        self,
        method: "AsyncFunc",
        *,
        publish_kwargs: "AnyDict",
        middlewares: Sequence["PublisherMiddleware"] = (),
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
        _extra_middlewares: Sequence["PublisherMiddleware"] = (),
        **kwargs: Any,
    ) -> Any:
        """Publish a message."""
        publish_kwargs = {
            "correlation_id": correlation_id,
            **self.publish_kwargs,
            **kwargs,
        }

        call: AsyncFunc = self.method
        for m in chain(_extra_middlewares, self.middlewares):
            call = partial(m, call)

        return await call(message, **publish_kwargs)

    async def request(
        self,
        message: "SendableMessage",
        /,
        *,
        correlation_id: Optional[str] = None,
        _extra_middlewares: Sequence["PublisherMiddleware"] = (),
    ) -> Any:
        raise NotImplementedError(
            "`FakePublisher` can be used only to publish "
            "a response for `reply-to` or `RPC` messages."
        )

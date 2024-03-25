from contextlib import AsyncExitStack
from itertools import chain
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Union

from nats.aio.msg import Msg
from typing_extensions import Annotated, Doc, override

from faststream.broker.core.publisher import BasePublisher
from faststream.exceptions import NOT_CONNECTED_YET

if TYPE_CHECKING:
    from faststream.broker.types import PublisherMiddleware
    from faststream.nats.producer import NatsFastProducer, NatsJSFastProducer
    from faststream.nats.schemas import JStream
    from faststream.types import AnyDict, DecodedMessage, SendableMessage


class LogicPublisher(BasePublisher[Msg]):
    """A class to represent a NATS publisher."""

    _producer: Union["NatsFastProducer", "NatsJSFastProducer", None]

    def __init__(
        self,
        *,
        subject: str,
        reply_to: str,
        headers: Optional[Dict[str, str]],
        stream: Optional["JStream"],
        timeout: Optional[float],
        # Regular publisher options
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI options
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        """Initialize NATS publisher object."""
        super().__init__(
            middlewares=middlewares,
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.subject = subject
        self.stream = stream
        self.timeout = timeout
        self.headers = headers
        self.reply_to = reply_to

        self._producer = None

    def __hash__(self) -> int:
        return hash(self.subject)

    @override
    async def publish(  # type: ignore[override]
        self,
        message: Annotated[
            "SendableMessage",
            Doc(
                "Message body to send. "
                "Can be any encodable object (native python types or `pydantic.BaseModel`)."
            ),
        ],
        subject: Annotated[
            str,
            Doc("NATS subject to send message."),
        ] = "",
        headers: Annotated[
            Optional[Dict[str, str]],
            Doc(
                "Message headers to store metainformation. "
                "**content-type** and **correlation_id** will be setted automatically by framework anyway."
            ),
        ] = None,
        reply_to: Annotated[
            str,
            Doc("NATS subject name to send response."),
        ] = "",
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages."
            ),
        ] = None,
        stream: Annotated[
            Optional[str],
            Doc(
                "This option validates that the target subject is in presented stream. "
                "Can be ommited without any effect."
            ),
        ] = None,
        timeout: Annotated[
            Optional[float],
            Doc("Timeout to send message to NATS."),
        ] = None,
        *,
        rpc: Annotated[
            bool,
            Doc("Whether to wait for reply in blocking mode."),
        ] = False,
        rpc_timeout: Annotated[
            Optional[float],
            Doc("RPC reply waiting time."),
        ] = 30.0,
        raise_timeout: Annotated[
            bool,
            Doc(
                "Whetever to raise `TimeoutError` or return `None` at **rpc_timeout**. "
                "RPC request returns `None` at timeout by default."
            ),
        ] = False,
        # publisher specific
        extra_middlewares: Annotated[
            Iterable["PublisherMiddleware"],
            Doc("Extra middlewares to wrap publishing process."),
        ] = (),
    ) -> Optional["DecodedMessage"]:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        kwargs: "AnyDict" = {
            "subject": subject or self.subject,
            "headers": headers or self.headers,
            "reply_to": reply_to or self.reply_to,
            "correlation_id": correlation_id,
            # specific args
            "rpc": rpc,
            "rpc_timeout": rpc_timeout,
            "raise_timeout": raise_timeout,
        }

        if (stream := stream or getattr(self.stream, "name", None)):
            kwargs.update({
                "stream": stream,
                "timeout": timeout or self.timeout
            })

        async with AsyncExitStack() as stack:
            for m in chain(extra_middlewares, self.middlewares):
                message = await stack.enter_async_context(
                    m(message, **kwargs)
                )

            return await self._producer.publish(
                message,
                **kwargs
            )

        return None

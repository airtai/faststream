from contextlib import AsyncExitStack
from functools import cached_property
from itertools import chain
from typing import TYPE_CHECKING, Any, Iterable, Optional, Sequence, cast

from typing_extensions import Annotated, Doc, override

from faststream.broker.core.publisher import BasePublisher
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.redis.producer import RedisFastProducer
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub
from faststream.types import AnyDict, DecodedMessage, SendableMessage

if TYPE_CHECKING:
    from faststream.broker.types import PublisherMiddleware


class LogicPublisher(BasePublisher["AnyDict"]):
    """A class to represent a Redis publisher."""

    _producer: Optional[RedisFastProducer]

    def __init__(
        self,
        *,
        channel: Optional[PubSub],
        list: Optional[ListSub],
        stream: Optional[StreamSub],
        reply_to: str,
        headers: Optional[AnyDict],
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

        self.channel = channel
        self.list = list
        self.stream = stream
        self.reply_to = reply_to
        self.headers = headers

        self._producer = None

    @override
    async def publish(  # type: ignore[override]
        self,
        message: Annotated[
            "SendableMessage",
            Doc("Message body to send."),
        ] = None,
        channel: Annotated[
            Optional[str],
            Doc("Redis PubSub object name to send message."),
        ] = None,
        reply_to: Annotated[
            Optional[str],
            Doc("Reply message destination PubSub object name."),
        ] = None,
        headers: Annotated[
            Optional["AnyDict"],
            Doc("Message headers to store metainformation."),
        ] = None,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages."
            ),
        ] = None,
        *,
        list: Annotated[
            Optional[str],
            Doc("Redis List object name to send message."),
        ] = None,
        stream: Annotated[
            Optional[str],
            Doc("Redis Stream object name to send message."),
        ] = None,
        maxlen: Annotated[
            Optional[int],
            Doc(
                "Redis Stream maxlen publish option. "
                "Remove eldest message if maxlen exceeded."
            ),
        ] = None,
        # rpc args
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
    ) -> Optional[DecodedMessage]:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        middlewares = chain(extra_middlewares, self.middlewares)

        if (list_sub := ListSub.validate(list or self.list)) is not None:
            if list_sub.batch:
                msgs = cast(Sequence[SendableMessage], message)

                async with AsyncExitStack() as stack:
                    wrapped_messages = [
                        await stack.enter_async_context(
                            middleware(None).publish_scope(msg, list=list_sub)
                        )
                        for msg in msgs
                        for middleware in middlewares
                    ] or msgs

                    return await self._producer.publish_batch(
                        *wrapped_messages,
                        list=list_sub.name,  # type: ignore[union-attr]
                    )

            else:
                kwargs = {
                    "channel": None,
                    "list": list_sub.name,
                    "stream": None,
                    "maxlen": None,
                }

        elif (channel_sub := PubSub.validate(channel or self.channel)) is not None:
            kwargs = {
                "channel": channel_sub.name,
                "list": None,
                "stream": None,
                "maxlen": None,
            }

        elif (stream_sub := StreamSub.validate(stream or self.stream)) is not None:
            kwargs = {
                "channel": None,
                "list": None,
                "stream": stream_sub.name,
                "maxlen": maxlen or stream_sub.maxlen,
            }

        else:
            raise ValueError(INCORRECT_SETUP_MSG)

        kwargs.update({
            "reply_to": reply_to or self.reply_to,
            "headers": headers or self.headers,
            "correlation_id": correlation_id,
            # specific args
            "rpc": rpc,
            "rpc_timeout": rpc_timeout,
            "raise_timeout": raise_timeout,
        })

        async with AsyncExitStack() as stack:
            for m in middlewares:
                message = await stack.enter_async_context(
                    m(message, **kwargs)
                )

            return await self._producer.publish(message=message, **kwargs)

    @cached_property
    def channel_name(self) -> str:
        any_of = self.channel or self.list or self.stream
        assert any_of, INCORRECT_SETUP_MSG  # nosec B101
        return any_of.name

    def __hash__(self) -> int:
        return hash(self.channel_name)

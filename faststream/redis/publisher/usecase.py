from abc import abstractmethod
from collections.abc import Awaitable, Iterable
from copy import deepcopy
from functools import partial
from itertools import chain
from typing import TYPE_CHECKING, Annotated, Any, Callable, Optional

from typing_extensions import Doc, override

from faststream._internal.context.repository import context
from faststream._internal.publisher.usecase import PublisherUsecase
from faststream._internal.subscriber.utils import process_msg
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.message import gen_cor_id
from faststream.redis.message import UnifyRedisDict
from faststream.redis.schemas import ListSub, PubSub, StreamSub

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict, SendableMessage
    from faststream._internal.types import BrokerMiddleware, PublisherMiddleware
    from faststream.redis.message import RedisMessage
    from faststream.redis.publisher.producer import RedisFastProducer


class LogicPublisher(PublisherUsecase[UnifyRedisDict]):
    """A class to represent a Redis publisher."""

    _producer: Optional["RedisFastProducer"]

    def __init__(
        self,
        *,
        reply_to: str,
        headers: Optional["AnyDict"],
        # Publisher args
        broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"],
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            # AsyncAPI args
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.reply_to = reply_to
        self.headers = headers

        self._producer = None

    @abstractmethod
    def subscriber_property(self, *, name_only: bool) -> "AnyDict":
        raise NotImplementedError


class ChannelPublisher(LogicPublisher):
    def __init__(
        self,
        *,
        channel: "PubSub",
        reply_to: str,
        headers: Optional["AnyDict"],
        # Regular publisher options
        broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"],
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI options
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            reply_to=reply_to,
            headers=headers,
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.channel = channel

    @override
    def subscriber_property(self, *, name_only: bool) -> "AnyDict":
        return {
            "channel": self.channel.name if name_only else self.channel,
            "list": None,
            "stream": None,
        }

    def add_prefix(self, prefix: str) -> None:
        channel = deepcopy(self.channel)
        channel.name = f"{prefix}{channel.name}"
        self.channel = channel

    @override
    async def publish(
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
            str,
            Doc("Reply message destination PubSub object name."),
        ] = "",
        headers: Annotated[
            Optional["AnyDict"],
            Doc("Message headers to store metainformation."),
        ] = None,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        **kwargs: Any,  # option to suppress maxlen
    ) -> None:
        return await self._publish(
            message,
            channel=channel,
            reply_to=reply_to,
            headers=headers,
            correlation_id=correlation_id,
            _extra_middlewares=(),
            **kwargs,
        )

    @override
    async def _publish(
        self,
        message: "SendableMessage" = None,
        channel: Optional[str] = None,
        reply_to: str = "",
        headers: Optional["AnyDict"] = None,
        correlation_id: Optional[str] = None,
        # publisher specific
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
        **kwargs: Any,  # option to suppress maxlen
    ) -> None:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        channel_sub = PubSub.validate(channel or self.channel)
        reply_to = reply_to or self.reply_to
        headers = headers or self.headers
        correlation_id = correlation_id or gen_cor_id()

        call: Callable[..., Awaitable[None]] = self._producer.publish

        for m in chain(
            (
                _extra_middlewares
                or (
                    m(None, context=context).publish_scope
                    for m in self._broker_middlewares
                )
            ),
            self._middlewares,
        ):
            call = partial(m, call)

        await call(
            message,
            channel=channel_sub.name,
            # basic args
            reply_to=reply_to,
            headers=headers,
            correlation_id=correlation_id,
        )

    @override
    async def request(
        self,
        message: Annotated[
            "SendableMessage",
            Doc("Message body to send."),
        ] = None,
        channel: Annotated[
            Optional[str],
            Doc("Redis PubSub object name to send message."),
        ] = None,
        *,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        headers: Annotated[
            Optional["AnyDict"],
            Doc("Message headers to store metainformation."),
        ] = None,
        timeout: Annotated[
            Optional[float],
            Doc("RPC reply waiting time."),
        ] = 30.0,
        # publisher specific
        _extra_middlewares: Annotated[
            Iterable["PublisherMiddleware"],
            Doc("Extra middlewares to wrap publishing process."),
        ] = (),
    ) -> "RedisMessage":
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        kwargs = {
            "channel": PubSub.validate(channel or self.channel).name,
            # basic args
            "headers": headers or self.headers,
            "correlation_id": correlation_id or gen_cor_id(),
            "timeout": timeout,
        }
        request: Callable[..., Awaitable[Any]] = self._producer.request

        for pub_m in chain(
            (
                _extra_middlewares
                or (
                    m(None, context=context).publish_scope
                    for m in self._broker_middlewares
                )
            ),
            self._middlewares,
        ):
            request = partial(pub_m, request)

        published_msg = await request(
            message,
            **kwargs,
        )

        msg: RedisMessage = await process_msg(
            msg=published_msg,
            middlewares=self._broker_middlewares,
            parser=self._producer._parser,
            decoder=self._producer._decoder,
        )
        return msg


class ListPublisher(LogicPublisher):
    def __init__(
        self,
        *,
        list: "ListSub",
        reply_to: str,
        headers: Optional["AnyDict"],
        # Regular publisher options
        broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"],
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI options
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            reply_to=reply_to,
            headers=headers,
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.list = list

    @override
    def subscriber_property(self, *, name_only: bool) -> "AnyDict":
        return {
            "channel": None,
            "list": self.list.name if name_only else self.list,
            "stream": None,
        }

    def add_prefix(self, prefix: str) -> None:
        list_sub = deepcopy(self.list)
        list_sub.name = f"{prefix}{list_sub.name}"
        self.list = list_sub

    @override
    async def publish(
        self,
        message: Annotated[
            "SendableMessage",
            Doc("Message body to send."),
        ] = None,
        list: Annotated[
            Optional[str],
            Doc("Redis List object name to send message."),
        ] = None,
        reply_to: Annotated[
            str,
            Doc("Reply message destination PubSub object name."),
        ] = "",
        headers: Annotated[
            Optional["AnyDict"],
            Doc("Message headers to store metainformation."),
        ] = None,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        # publisher specific
        **kwargs: Any,  # option to suppress maxlen
    ) -> None:
        return await self._publish(
            message,
            list=list,
            reply_to=reply_to,
            headers=headers,
            correlation_id=correlation_id,
            _extra_middlewares=(),
            **kwargs,
        )

    @override
    async def _publish(
        self,
        message: "SendableMessage" = None,
        list: Optional[str] = None,
        reply_to: str = "",
        headers: Optional["AnyDict"] = None,
        correlation_id: Optional[str] = None,
        # publisher specific
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
        **kwargs: Any,  # option to suppress maxlen
    ) -> None:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        list_sub = ListSub.validate(list or self.list)
        reply_to = reply_to or self.reply_to
        correlation_id = correlation_id or gen_cor_id()

        call: Callable[..., Awaitable[None]] = self._producer.publish

        for m in chain(
            (
                _extra_middlewares
                or (
                    m(None, context=context).publish_scope
                    for m in self._broker_middlewares
                )
            ),
            self._middlewares,
        ):
            call = partial(m, call)

        await call(
            message,
            list=list_sub.name,
            # basic args
            reply_to=reply_to,
            headers=headers or self.headers,
            correlation_id=correlation_id,
        )

    @override
    async def request(
        self,
        message: Annotated[
            "SendableMessage",
            Doc("Message body to send."),
        ] = None,
        list: Annotated[
            Optional[str],
            Doc("Redis List object name to send message."),
        ] = None,
        *,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        headers: Annotated[
            Optional["AnyDict"],
            Doc("Message headers to store metainformation."),
        ] = None,
        timeout: Annotated[
            Optional[float],
            Doc("RPC reply waiting time."),
        ] = 30.0,
        # publisher specific
        _extra_middlewares: Annotated[
            Iterable["PublisherMiddleware"],
            Doc("Extra middlewares to wrap publishing process."),
        ] = (),
    ) -> "RedisMessage":
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        kwargs = {
            "list": ListSub.validate(list or self.list).name,
            # basic args
            "headers": headers or self.headers,
            "correlation_id": correlation_id or gen_cor_id(),
            "timeout": timeout,
        }

        request: Callable[..., Awaitable[Any]] = self._producer.request

        for pub_m in chain(
            (
                _extra_middlewares
                or (
                    m(None, context=context).publish_scope
                    for m in self._broker_middlewares
                )
            ),
            self._middlewares,
        ):
            request = partial(pub_m, request)

        published_msg = await request(
            message,
            **kwargs,
        )

        msg: RedisMessage = await process_msg(
            msg=published_msg,
            middlewares=self._broker_middlewares,
            parser=self._producer._parser,
            decoder=self._producer._decoder,
        )
        return msg


class ListBatchPublisher(ListPublisher):
    @override
    async def publish(  # type: ignore[override]
        self,
        message: Annotated[
            Iterable["SendableMessage"],
            Doc("Message body to send."),
        ] = (),
        list: Annotated[
            Optional[str],
            Doc("Redis List object name to send message."),
        ] = None,
        *,
        correlation_id: Annotated[
            Optional[str],
            Doc("Has no real effect. Option to be compatible with original protocol."),
        ] = None,
        headers: Annotated[
            Optional["AnyDict"],
            Doc("Message headers to store metainformation."),
        ] = None,
        # publisher specific
        **kwargs: Any,  # option to suppress maxlen
    ) -> None:
        return await self._publish(
            message,
            list=list,
            correlation_id=correlation_id,
            headers=headers,
            _extra_middlewares=(),
            **kwargs,
        )

    @override
    async def _publish(  # type: ignore[override]
        self,
        message: "SendableMessage" = (),
        list: Optional[str] = None,
        *,
        correlation_id: Optional[str] = None,
        headers: Optional["AnyDict"] = None,
        # publisher specific
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
        **kwargs: Any,  # option to suppress maxlen
    ) -> None:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        list_sub = ListSub.validate(list or self.list)
        correlation_id = correlation_id or gen_cor_id()

        call: Callable[..., Awaitable[None]] = self._producer.publish_batch

        for m in chain(
            (
                _extra_middlewares
                or (
                    m(None, context=context).publish_scope
                    for m in self._broker_middlewares
                )
            ),
            self._middlewares,
        ):
            call = partial(m, call)

        await call(
            *message,
            list=list_sub.name,
            correlation_id=correlation_id,
            headers=headers or self.headers,
        )


class StreamPublisher(LogicPublisher):
    def __init__(
        self,
        *,
        stream: "StreamSub",
        reply_to: str,
        headers: Optional["AnyDict"],
        # Regular publisher options
        broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"],
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI options
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            reply_to=reply_to,
            headers=headers,
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.stream = stream

    @override
    def subscriber_property(self, *, name_only: bool) -> "AnyDict":
        return {
            "channel": None,
            "list": None,
            "stream": self.stream.name if name_only else self.stream,
        }

    def add_prefix(self, prefix: str) -> None:
        stream_sub = deepcopy(self.stream)
        stream_sub.name = f"{prefix}{stream_sub.name}"
        self.stream = stream_sub

    @override
    async def publish(
        self,
        message: Annotated[
            "SendableMessage",
            Doc("Message body to send."),
        ] = None,
        stream: Annotated[
            Optional[str],
            Doc("Redis Stream object name to send message."),
        ] = None,
        reply_to: Annotated[
            str,
            Doc("Reply message destination PubSub object name."),
        ] = "",
        headers: Annotated[
            Optional["AnyDict"],
            Doc("Message headers to store metainformation."),
        ] = None,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        *,
        maxlen: Annotated[
            Optional[int],
            Doc(
                "Redis Stream maxlen publish option. "
                "Remove eldest message if maxlen exceeded.",
            ),
        ] = None,
    ) -> None:
        return await self._publish(
            message,
            stream=stream,
            reply_to=reply_to,
            headers=headers,
            correlation_id=correlation_id,
            maxlen=maxlen,
            _extra_middlewares=(),
        )

    @override
    async def _publish(
        self,
        message: "SendableMessage" = None,
        stream: Optional[str] = None,
        reply_to: str = "",
        headers: Optional["AnyDict"] = None,
        correlation_id: Optional[str] = None,
        *,
        maxlen: Optional[int] = None,
        # publisher specific
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
    ) -> None:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        stream_sub = StreamSub.validate(stream or self.stream)
        maxlen = maxlen or stream_sub.maxlen
        reply_to = reply_to or self.reply_to
        headers = headers or self.headers
        correlation_id = correlation_id or gen_cor_id()

        call: Callable[..., Awaitable[None]] = self._producer.publish

        for m in chain(
            (
                _extra_middlewares
                or (
                    m(None, context=context).publish_scope
                    for m in self._broker_middlewares
                )
            ),
            self._middlewares,
        ):
            call = partial(m, call)

        await call(
            message,
            stream=stream_sub.name,
            maxlen=maxlen,
            # basic args
            reply_to=reply_to,
            headers=headers,
            correlation_id=correlation_id,
        )

    @override
    async def request(
        self,
        message: Annotated[
            "SendableMessage",
            Doc("Message body to send."),
        ] = None,
        stream: Annotated[
            Optional[str],
            Doc("Redis Stream object name to send message."),
        ] = None,
        *,
        maxlen: Annotated[
            Optional[int],
            Doc(
                "Redis Stream maxlen publish option. "
                "Remove eldest message if maxlen exceeded.",
            ),
        ] = None,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages.",
            ),
        ] = None,
        headers: Annotated[
            Optional["AnyDict"],
            Doc("Message headers to store metainformation."),
        ] = None,
        timeout: Annotated[
            Optional[float],
            Doc("RPC reply waiting time."),
        ] = 30.0,
        # publisher specific
        _extra_middlewares: Annotated[
            Iterable["PublisherMiddleware"],
            Doc("Extra middlewares to wrap publishing process."),
        ] = (),
    ) -> "RedisMessage":
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        kwargs = {
            "stream": StreamSub.validate(stream or self.stream).name,
            # basic args
            "headers": headers or self.headers,
            "correlation_id": correlation_id or gen_cor_id(),
            "timeout": timeout,
        }

        request: Callable[..., Awaitable[Any]] = self._producer.request

        for pub_m in chain(
            (
                _extra_middlewares
                or (
                    m(None, context=context).publish_scope
                    for m in self._broker_middlewares
                )
            ),
            self._middlewares,
        ):
            request = partial(pub_m, request)

        published_msg = await request(
            message,
            **kwargs,
        )

        msg: RedisMessage = await process_msg(
            msg=published_msg,
            middlewares=self._broker_middlewares,
            parser=self._producer._parser,
            decoder=self._producer._decoder,
        )
        return msg

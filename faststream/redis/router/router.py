from typing import Any, Callable, Dict, Iterable, Optional, Sequence, Union

from typing_extensions import TypeAlias, override

from faststream._compat import model_copy
from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.router import BrokerRoute as RedisRoute
from faststream.broker.router import BrokerRouter
from faststream.broker.types import (
    P_HandlerParams,
    PublisherMiddleware,
    T_HandlerReturn,
)
from faststream.redis.asyncapi import Handler, Publisher
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub
from faststream.types import AnyDict, SendableMessage

Channel: TypeAlias = str


class RedisRouter(BrokerRouter[int, "AnyRedisDict"]):
    """A class to represent a Redis router."""

    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[RedisRoute["AnyRedisDict", SendableMessage]] = (),
        **kwargs: Any,
    ) -> None:
        """Initialize the Redis router.

        Args:
            prefix: The prefix.
            handlers: The handlers.
            **kwargs: The keyword arguments.
        """
        for h in handlers:
            if not (channel := h.kwargs.pop("channel", None)):
                if list := h.kwargs.pop("list", None):
                    h.kwargs["list"] = prefix + list
                    continue

                elif stream := h.kwargs.pop("stream", None):
                    h.kwargs["stream"] = prefix + stream
                    continue

                channel, h.args = h.args[0], h.args[1:]

            h.args = (prefix + channel, *h.args)

        super().__init__(prefix, handlers, **kwargs)

    @override
    def subscriber(  # type: ignore[override]
        self,
        channel: Union[Channel, PubSub, None] = None,
        *,
        list: Union[Channel, ListSub, None] = None,
        stream: Union[Channel, StreamSub, None] = None,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper["AnyRedisDict", P_HandlerParams, T_HandlerReturn],
    ]:
        channel = PubSub.validate(channel)
        list = ListSub.validate(list)
        stream = StreamSub.validate(stream)

        return self._wrap_subscriber(
            channel=model_copy(channel, update={"name": self.prefix + channel.name})
            if channel
            else None,
            list=model_copy(list, update={"name": self.prefix + list.name})
            if list
            else None,
            stream=model_copy(stream, update={"name": self.prefix + stream.name})
            if stream
            else None,
            **broker_kwargs,
        )

    _publishers: Dict[int, Publisher]  # type: ignore[assignment]

    @override
    @staticmethod
    def _get_publisher_key(publisher: Publisher) -> int:  # type: ignore[override]
        any_of = publisher.channel or publisher.list or publisher.stream
        if any_of is None:
            raise ValueError(INCORRECT_SETUP_MSG)
        return Handler.get_routing_hash(any_of)

    @override
    @staticmethod
    def _update_publisher_prefix(  # type: ignore[override]
        prefix: str,
        publisher: Publisher,
    ) -> Publisher:
        if publisher.channel is not None:
            publisher.channel = model_copy(
                publisher.channel, update={"name": prefix + publisher.channel.name}
            )
        elif publisher.list is not None:
            publisher.list = model_copy(
                publisher.list, update={"name": prefix + publisher.list.name}
            )
        elif publisher.stream is not None:
            publisher.stream = model_copy(
                publisher.stream, update={"name": prefix + publisher.stream.name}
            )
        else:
            raise AssertionError("unreachable")
        return publisher

    @override
    def publisher(  # type: ignore[override]
        self,
        channel: Union[str, PubSub, None] = None,
        list: Union[str, ListSub, None] = None,
        stream: Union[str, StreamSub, None] = None,
        headers: Optional[AnyDict] = None,
        reply_to: str = "",
        middlewares: Iterable["PublisherMiddleware"] = (),
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
    ) -> Publisher:
        if not any((stream, list, channel)):
            raise ValueError(INCORRECT_SETUP_MSG)

        new_publisher = self._update_publisher_prefix(
            self.prefix,
            Publisher(
                channel=PubSub.validate(channel),
                list=ListSub.validate(list),
                stream=StreamSub.validate(stream),
                reply_to=reply_to,
                headers=headers,
                middlewares=middlewares,
                # AsyncAPI options
                title_=title,
                description_=description,
                schema_=schema,
                include_in_schema=(
                    include_in_schema
                    if self.include_in_schema is None
                    else self.include_in_schema
                ),
            ),
        )
        publisher_key = self._get_publisher_key(new_publisher)
        publisher = self._publishers[publisher_key] = self._publishers.get(
            publisher_key, new_publisher
        )
        return publisher

from typing import Any, Dict, Optional, Union

from faststream._compat import model_copy, override
from faststream.redis.asyncapi import Handler, Publisher
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub
from faststream.redis.shared.router import RedisRouter as BaseRouter
from faststream.types import AnyDict


class RedisRouter(BaseRouter):
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
                title=title,
                _description=description,
                _schema=schema,
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

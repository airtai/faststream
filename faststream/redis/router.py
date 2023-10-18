from typing import Any, Dict, Optional

from faststream._compat import override
from faststream.redis.asyncapi import Publisher
from faststream.redis.shared.router import RedisRouter as BaseRouter
from faststream.types import AnyDict


class RedisRouter(BaseRouter):
    _publishers: Dict[str, Publisher]  # type: ignore[assignment]

    @override
    @staticmethod
    def _get_publisher_key(publisher: Publisher) -> str:  # type: ignore[override]
        return publisher.channel

    @override
    @staticmethod
    def _update_publisher_prefix(  # type: ignore[override]
        prefix: str,
        publisher: Publisher,
    ) -> Publisher:
        publisher.channel = prefix + publisher.channel
        return publisher

    @override
    def publisher(  # type: ignore[override]
        self,
        channel: str,
        headers: Optional[AnyDict] = None,
        reply_to: str = "",
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
    ) -> Publisher:
        new_publisher = self._update_publisher_prefix(
            self.prefix,
            Publisher(
                channel=channel,
                reply_to=reply_to,
                headers=headers,
                title=title,
                _description=description,
                _schema=schema,
                include_in_schema=include_in_schema,
            ),
        )
        publisher_key = self._get_publisher_key(new_publisher)
        publisher = self._publishers[publisher_key] = self._publishers.get(
            publisher_key, new_publisher
        )
        return publisher

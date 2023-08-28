from typing import Dict, Optional

from faststream._compat import override
from faststream.kafka.asyncapi import Publisher
from faststream.kafka.shared.router import KafkaRouter as BaseRouter


class KafkaRouter(BaseRouter):
    _publishers: Dict[str, Publisher]  # type: ignore[assignment]

    @override
    @staticmethod
    def _get_publisher_key(publisher: Publisher) -> str:  # type: ignore[override]
        return publisher.topic

    @override
    @staticmethod
    def _update_publisher_prefix(  # type: ignore[override]
        prefix: str,
        publisher: Publisher,
    ) -> Publisher:
        publisher.topic = prefix + publisher.topic
        return publisher

    @override
    def publisher(  # type: ignore[override]
        self,
        topic: str,
        key: Optional[bytes] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        batch: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Publisher:
        new_publisher = self._update_publisher_prefix(
            self.prefix,
            Publisher(
                topic=topic,
                key=key,
                partition=partition,
                timestamp_ms=timestamp_ms,
                headers=headers,
                reply_to=reply_to,
                title=title,
                batch=batch,
                _description=description,
            ),
        )
        publisher_key = self._get_publisher_key(new_publisher)
        publisher = self._publishers[publisher_key] = self._publishers.get(
            publisher_key, new_publisher
        )
        return publisher

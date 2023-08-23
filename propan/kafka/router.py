from typing import Dict, Optional

from propan._compat import override
from propan.kafka.asyncapi import Publisher
from propan.kafka.shared.router import KafkaRouter as BaseRouter


class KafkaRouter(BaseRouter):
    _publishers: Dict[str, Publisher]  # type: ignore[assignment]

    @override
    def publisher(  # type: ignore[override]
        self,
        topic: str,
        key: Optional[bytes] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Publisher:
        new_topic = self.prefix + topic
        publisher = self._publishers[new_topic] = self._publishers.get(
            new_topic,
            Publisher(
                topic=new_topic,
                key=key,
                partition=partition,
                timestamp_ms=timestamp_ms,
                headers=headers,
                reply_to=reply_to,
                title=title,
                _description=description,
            ),
        )
        return publisher

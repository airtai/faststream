from typing import Any

from faststream.confluent import TopicPartition
from tests.brokers.base.basic import BaseTestcaseConfig as _Base


class ConfluentTestcaseConfig(_Base):
    timeout: float = 10.0

    def get_subscriber_params(
        self,
        *topics: Any,
        **kwargs: Any,
    ) -> tuple[
        tuple[Any, ...],
        dict[str, Any],
    ]:
        if len(topics) == 1:
            partitions = [TopicPartition(topics[0], partition=0, offset=0)]
            topics = ()

        else:
            partitions = []

        return topics, {
            "auto_offset_reset": "earliest",
            "partitions": partitions,
            **kwargs,
        }

from typing import Generic, Optional, Sequence, Tuple, TypeVar

from pydantic.dataclasses import dataclass

KT = TypeVar("KT")
VT = TypeVar("VT")

_missing = object()


@dataclass
class ConsumerRecord(Generic[KT, VT]):
    topic: str
    "The topic this record is received from"

    partition: int
    "The partition from which this record is received"

    offset: int
    "The position of this record in the corresponding Kafka partition."

    timestamp: int
    "The timestamp of this record"

    timestamp_type: int
    "The timestamp type of this record"

    key: Optional[KT]
    "The key (or `None` if no key is specified)"

    value: Optional[VT]
    "The value"

    checksum: int
    "Deprecated"

    serialized_key_size: int
    "The size of the serialized, uncompressed key in bytes."

    serialized_value_size: int
    "The size of the serialized, uncompressed value in bytes."

    headers: Sequence[Tuple[str, bytes]]
    "The headers"

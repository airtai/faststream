from typing import Optional

from nats.js import api

from faststream._compat import TypedDict


class PullSubKwargs(TypedDict, total=False):
    subject: str
    durable: Optional[str]
    stream: Optional[str]
    config: Optional[api.ConsumerConfig]
    pending_msgs_limit: int
    pending_bytes_limit: int
    inbox_prefix: bytes

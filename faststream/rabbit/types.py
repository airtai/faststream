from typing import Union

import aio_pika

from faststream.rabbit.shared.types import TimeoutType
from faststream.types import SendableMessage

__all__ = (
    "TimeoutType",
    "AioPikaSendableMessage",
)

AioPikaSendableMessage = Union[aio_pika.Message, SendableMessage]

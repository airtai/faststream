from typing import Union

import aio_pika

from propan.rabbit.shared.types import TimeoutType
from propan.types import SendableMessage

__all__ = (
    "TimeoutType",
    "AioPikaSendableMessage",
)

AioPikaSendableMessage = Union[aio_pika.Message, SendableMessage]

from typing import Union

import aio_pika
from typing_extensions import TypeAlias

from faststream.rabbit.shared.types import TimeoutType
from faststream.types import SendableMessage

__all__ = (
    "TimeoutType",
    "AioPikaSendableMessage",
)

AioPikaSendableMessage: TypeAlias = Union[aio_pika.Message, SendableMessage]

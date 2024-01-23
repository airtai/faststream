from typing import Union

import aio_pika
from typing_extensions import TypeAlias

from faststream.types import SendableMessage


TimeoutType = Union[int, float, None]

AioPikaSendableMessage: TypeAlias = Union[aio_pika.Message, SendableMessage]

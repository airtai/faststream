from typing import Union

import aio_pika
from typing_extensions import TypeAlias

from faststream.types import SendableMessage

AioPikaSendableMessage: TypeAlias = Union[aio_pika.Message, SendableMessage]

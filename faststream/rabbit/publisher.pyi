from abc import abstractproperty
from dataclasses import dataclass, field
from typing import Optional, Union

import aio_pika
import aiormq

from faststream._compat import override
from faststream.rabbit.producer import AioPikaFastProducer
from faststream.rabbit.shared.publisher import ABCPublisher
from faststream.rabbit.shared.types import TimeoutType
from faststream.rabbit.types import AioPikaSendableMessage
from faststream.types import SendableMessage

@dataclass
class LogicPublisher(ABCPublisher[aio_pika.IncomingMessage]):
    _producer: Optional[AioPikaFastProducer] = field(default=None, init=False)

    @property
    def routing(self) -> Optional[str]: ...
    def _get_routing_hash(self) -> int: ...
    @abstractproperty
    def name(self) -> str:
        raise NotImplementedError()
    @override
    async def publish(  # type: ignore[override]
        self,
        message: AioPikaSendableMessage = "",
        *,
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: TimeoutType = None,
        persist: bool = False,
        reply_to: Optional[str] = None,
        # rpc args
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
        # message args
        headers: Optional[aio_pika.abc.HeadersType] = None,
        content_type: Optional[str] = None,
        content_encoding: Optional[str] = None,
        priority: Optional[int] = None,
        correlation_id: Optional[str] = None,
        expiration: Optional[aio_pika.abc.DateType] = None,
        message_id: Optional[str] = None,
        timestamp: Optional[aio_pika.abc.DateType] = None,
        type: Optional[str] = None,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
    ) -> Union[aiormq.abc.ConfirmationFrameType, SendableMessage]: ...

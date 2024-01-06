from abc import abstractproperty
from dataclasses import dataclass, field

import aio_pika
import aiormq
from typing_extensions import override

from faststream.rabbit.producer import AioPikaFastProducer
from faststream.rabbit.shared.publisher import ABCPublisher
from faststream.rabbit.shared.types import TimeoutType
from faststream.rabbit.types import AioPikaSendableMessage
from faststream.types import SendableMessage

@dataclass
class LogicPublisher(ABCPublisher[aio_pika.IncomingMessage]):
    _producer: AioPikaFastProducer | None = field(default=None, init=False)

    @property
    def routing(self) -> str | None: ...
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
        reply_to: str | None = None,
        # rpc args
        rpc: bool = False,
        rpc_timeout: float | None = 30.0,
        raise_timeout: bool = False,
        # message args
        headers: aio_pika.abc.HeadersType | None = None,
        content_type: str | None = None,
        content_encoding: str | None = None,
        priority: int | None = None,
        correlation_id: str | None = None,
        expiration: aio_pika.abc.DateType | None = None,
        message_id: str | None = None,
        timestamp: aio_pika.abc.DateType | None = None,
        type: str | None = None,
        user_id: str | None = None,
        app_id: str | None = None,
    ) -> aiormq.abc.ConfirmationFrameType | SendableMessage: ...

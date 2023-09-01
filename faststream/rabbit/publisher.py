from dataclasses import dataclass, field
from typing import Any, Optional, Union

import aiormq
from aio_pika import IncomingMessage

from faststream._compat import override
from faststream.rabbit.producer import AioPikaFastProducer
from faststream.rabbit.shared.publisher import ABCPublisher
from faststream.rabbit.types import AioPikaSendableMessage
from faststream.types import SendableMessage


@dataclass
class LogicPublisher(ABCPublisher[IncomingMessage]):
    _producer: Optional[AioPikaFastProducer] = field(default=None, init=False)

    @override
    async def publish(  # type: ignore[override]
        self,
        message: AioPikaSendableMessage = "",
        *,
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
        correlation_id: Optional[str] = None,
        **message_kwargs: Any,
    ) -> Union[aiormq.abc.ConfirmationFrameType, SendableMessage]:
        if self._producer is None:
            raise RuntimeError("Please, setup `_producer` first")
        return await self._producer.publish(
            message=message,
            queue=self.queue,
            exchange=self.exchange,
            routing_key=self.routing_key,
            mandatory=self.mandatory,
            immediate=self.immediate,
            timeout=self.timeout,
            rpc=rpc,
            rpc_timeout=rpc_timeout,
            raise_timeout=raise_timeout,
            persist=self.persist,
            reply_to=self.reply_to,
            correlation_id=correlation_id,
            **self.message_kwargs,
            **message_kwargs,
        )

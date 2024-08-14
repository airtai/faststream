from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional

from typing_extensions import override

from faststream.nats.publisher.usecase import LogicPublisher
from faststream.specification.asyncapi.utils import resolve_payloads
from faststream.specification.schema.bindings import ChannelBinding, nats
from faststream.specification.schema.channel import Channel
from faststream.specification.schema.message import CorrelationId, Message
from faststream.specification.schema.operation import Operation

if TYPE_CHECKING:
    from nats.aio.msg import Msg

    from faststream.broker.types import BrokerMiddleware, PublisherMiddleware
    from faststream.nats.schemas.js_stream import JStream


class SpecificationPublisher(LogicPublisher):
    """A class to represent a NATS publisher."""

    def get_name(self) -> str:
        return f"{self.subject}:Publisher"

    def get_schema(self) -> Dict[str, Channel]:
        payloads = self.get_payloads()

        return {
            self.name: Channel(
                description=self.description,
                publish=Operation(
                    message=Message(
                        title=f"{self.name}:Message",
                        payload=resolve_payloads(payloads, "Publisher"),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id"
                        ),
                    ),
                ),
                bindings=ChannelBinding(
                    nats=nats.ChannelBinding(
                        subject=self.subject,
                    )
                ),
            )
        }

    @override
    @classmethod
    def create(  # type: ignore[override]
        cls,
        *,
        subject: str,
        reply_to: str,
        headers: Optional[Dict[str, str]],
        stream: Optional["JStream"],
        timeout: Optional[float],
        # Publisher args
        broker_middlewares: Iterable["BrokerMiddleware[Msg]"],
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> "SpecificationPublisher":
        return cls(
            subject=subject,
            reply_to=reply_to,
            headers=headers,
            stream=stream,
            timeout=timeout,
            # Publisher args
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            # AsyncAPI args
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

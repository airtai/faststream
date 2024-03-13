from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from faststream.asyncapi.schema import (
    Channel,
    ChannelBinding,
    CorrelationId,
    Message,
    Operation,
)
from faststream.asyncapi.schema.bindings import nats
from faststream.asyncapi.utils import resolve_payloads
from faststream.nats.handler import BaseNatsHandler, BatchHandler, DefaultHandler
from faststream.nats.publisher import LogicPublisher

if TYPE_CHECKING:
    from faststream.nats.schemas.pull_sub import PullSub


class AsyncAPIHandler(BaseNatsHandler[Any]):
    """A class to represent a NATS handler."""

    def get_name(self) -> str:
        return f"{self.subject}:{self.call_name}"

    def get_schema(self) -> Dict[str, Channel]:
        payloads = self.get_payloads()

        return {
            self.name: Channel(
                description=self.description,
                subscribe=Operation(
                    message=Message(
                        title=f"{self.name}:Message",
                        payload=resolve_payloads(payloads),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id"
                        ),
                    ),
                ),
                bindings=ChannelBinding(
                    nats=nats.ChannelBinding(
                        subject=self.subject,
                        queue=self.queue or None,
                    )
                ),
            )
        }

    @staticmethod
    def create(
        *,
        pull_sub: Optional["PullSub"],
        max_workers: int,
        **kwargs,
    ) -> Union[
        "DefaultAsyncAPIHandler",
        "BatchAsyncAPIHandler",
    ]:
        if getattr(pull_sub, "batch", False):
            return BatchAsyncAPIHandler(
                pull_sub=pull_sub,
                **kwargs,
            )
        else:
            return DefaultAsyncAPIHandler(
                pull_sub=pull_sub,
                max_workers=max_workers,
                **kwargs,
            )


class DefaultAsyncAPIHandler(AsyncAPIHandler, DefaultHandler):
    """One-message consumer with AsyncAPI methods."""


class BatchAsyncAPIHandler(AsyncAPIHandler, BatchHandler):
    """Batch-message consumer with AsyncAPI methods."""


class Publisher(LogicPublisher):
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

from typing import Any

from typing_extensions import override

from faststream.nats.subscriber.usecase import (
    BatchPullStreamSubscriber,
    ConcurrentCoreSubscriber,
    ConcurrentPullStreamSubscriber,
    ConcurrentPushStreamSubscriber,
    CoreSubscriber,
    KeyValueWatchSubscriber,
    LogicSubscriber,
    ObjStoreWatchSubscriber,
    PullStreamSubscriber,
    PushStreamSubscription,
)
from faststream.specification.asyncapi.utils import resolve_payloads
from faststream.specification.schema.bindings import ChannelBinding, nats
from faststream.specification.schema.channel import Channel
from faststream.specification.schema.message import CorrelationId, Message
from faststream.specification.schema.operation import Operation


class SpecificationSubscriber(LogicSubscriber[Any, Any]):
    """A class to represent a NATS handler."""

    def get_name(self) -> str:
        return f"{self.subject}:{self.call_name}"

    def get_schema(self) -> dict[str, Channel]:
        payloads = self.get_payloads()

        return {
            self.name: Channel(
                description=self.description,
                subscribe=Operation(
                    message=Message(
                        title=f"{self.name}:Message",
                        payload=resolve_payloads(payloads),
                        correlationId=CorrelationId(
                            location="$message.header#/correlation_id",
                        ),
                    ),
                ),
                bindings=ChannelBinding(
                    nats=nats.ChannelBinding(
                        subject=self.subject,
                        queue=getattr(self, "queue", "") or None,
                    ),
                ),
            ),
        }


class SpecificationCoreSubscriber(
    SpecificationSubscriber,
    CoreSubscriber,
):
    """One-message core consumer with Specification methods."""


class SpecificationConcurrentCoreSubscriber(
    SpecificationSubscriber,
    ConcurrentCoreSubscriber,
):
    """One-message core concurrent consumer with Specification methods."""


class SpecificationStreamSubscriber(
    SpecificationSubscriber,
    PushStreamSubscription,
):
    """One-message JS Push consumer with Specification methods."""


class SpecificationConcurrentPushStreamSubscriber(
    SpecificationSubscriber,
    ConcurrentPushStreamSubscriber,
):
    """One-message JS Push concurrent consumer with Specification methods."""


class SpecificationPullStreamSubscriber(
    SpecificationSubscriber,
    PullStreamSubscriber,
):
    """One-message JS Pull consumer with Specification methods."""


class SpecificationConcurrentPullStreamSubscriber(
    SpecificationSubscriber,
    ConcurrentPullStreamSubscriber,
):
    """One-message JS Pull concurrent consumer with Specification methods."""


class SpecificationBatchPullStreamSubscriber(
    SpecificationSubscriber,
    BatchPullStreamSubscriber,
):
    """Batch-message Pull consumer with Specification methods."""


class SpecificationKeyValueWatchSubscriber(
    SpecificationSubscriber,
    KeyValueWatchSubscriber,
):
    """KeyValueWatch consumer with Specification methods."""

    @override
    def get_name(self) -> str:
        return ""

    @override
    def get_schema(self) -> dict[str, Channel]:
        return {}


class SpecificationObjStoreWatchSubscriber(
    SpecificationSubscriber,
    ObjStoreWatchSubscriber,
):
    """ObjStoreWatch consumer with Specification methods."""

    @override
    def get_name(self) -> str:
        return ""

    @override
    def get_schema(self) -> dict[str, Channel]:
        return {}

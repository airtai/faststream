from typing import Any, Dict

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
from faststream.specification.bindings import ChannelBinding, nats
from faststream.specification.channel import Channel
from faststream.specification.message import CorrelationId, Message
from faststream.specification.operation import Operation


class AsyncAPISubscriber(LogicSubscriber[Any]):
    """A class to represent a NATS handler."""

    def get_name(self) -> str:
        return f"{self.subject}:{self.call_name}"

    def get_schema(self) -> Dict[str, v2_6_0.Channel]:
        payloads = self.get_payloads()

        return {
            self.name: v2_6_0.Channel(
                description=self.description,
                subscribe=v2_6_0.Operation(
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
                        queue=getattr(self, "queue", "") or None,
                    )
                ),
            )
        }


class AsyncAPICoreSubscriber(AsyncAPISubscriber, CoreSubscriber):
    """One-message core consumer with AsyncAPI methods."""


class AsyncAPIConcurrentCoreSubscriber(AsyncAPISubscriber, ConcurrentCoreSubscriber):
    """One-message core concurrent consumer with AsyncAPI methods."""


class AsyncAPIStreamSubscriber(AsyncAPISubscriber, PushStreamSubscription):
    """One-message JS Push consumer with AsyncAPI methods."""


class AsyncAPIConcurrentPushStreamSubscriber(
    AsyncAPISubscriber, ConcurrentPushStreamSubscriber
):
    """One-message JS Push concurrent consumer with AsyncAPI methods."""


class AsyncAPIPullStreamSubscriber(AsyncAPISubscriber, PullStreamSubscriber):
    """One-message JS Pull consumer with AsyncAPI methods."""


class AsyncAPIConcurrentPullStreamSubscriber(
    AsyncAPISubscriber, ConcurrentPullStreamSubscriber
):
    """One-message JS Pull concurrent consumer with AsyncAPI methods."""


class AsyncAPIBatchPullStreamSubscriber(AsyncAPISubscriber, BatchPullStreamSubscriber):
    """Batch-message Pull consumer with AsyncAPI methods."""


class AsyncAPIKeyValueWatchSubscriber(AsyncAPISubscriber, KeyValueWatchSubscriber):
    """KeyValueWatch consumer with AsyncAPI methods."""

    @override
    def get_name(self) -> str:
        return ""

    @override
    def get_schema(self) -> Dict[str, v2_6_0.Channel]:
        return {}


class AsyncAPIObjStoreWatchSubscriber(AsyncAPISubscriber, ObjStoreWatchSubscriber):
    """ObjStoreWatch consumer with AsyncAPI methods."""

    @override
    def get_name(self) -> str:
        return ""

    @override
    def get_schema(self) -> Dict[str, v2_6_0.Channel]:
        return {}

from collections.abc import Iterable
from typing import (
    TYPE_CHECKING,
    Optional,
)

from typing_extensions import override

from faststream._internal.subscriber.mixins import ConcurrentMixin

from .stream_basic import StreamSubscriber

if TYPE_CHECKING:
    from fast_depends.dependencies import Dependant
    from nats.aio.msg import Msg
    from nats.js import JetStreamContext
    from nats.js.api import ConsumerConfig

    from faststream._internal.basic_types import (
        AnyDict,
    )
    from faststream._internal.types import (
        BrokerMiddleware,
    )
    from faststream.middlewares import AckPolicy
    from faststream.nats.schemas import JStream


class PushStreamSubscription(StreamSubscriber):
    subscription: Optional["JetStreamContext.PushSubscription"]

    @override
    async def _create_subscription(self) -> None:
        """Create NATS subscription and start consume task."""
        if self.subscription:
            return

        self.subscription = await self._connection_state.js.subscribe(
            subject=self.clear_subject,
            queue=self.queue,
            cb=self.consume,
            config=self.config,
            **self.extra_options,
        )


class ConcurrentPushStreamSubscriber(
    ConcurrentMixin,
    StreamSubscriber,
):
    subscription: Optional["JetStreamContext.PushSubscription"]

    def __init__(
        self,
        *,
        max_workers: int,
        stream: "JStream",
        # default args
        subject: str,
        config: "ConsumerConfig",
        queue: str,
        extra_options: Optional["AnyDict"],
        # Subscriber args
        ack_policy: "AckPolicy",
        no_reply: bool,
        broker_dependencies: Iterable["Dependant"],
        broker_middlewares: Iterable["BrokerMiddleware[Msg]"],
        # AsyncAPI args
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        super().__init__(
            max_workers=max_workers,
            # basic args
            stream=stream,
            subject=subject,
            config=config,
            queue=queue,
            extra_options=extra_options,
            # Propagated args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_middlewares=broker_middlewares,
            broker_dependencies=broker_dependencies,
            # AsyncAPI args
            description_=description_,
            title_=title_,
            include_in_schema=include_in_schema,
        )

    @override
    async def _create_subscription(self) -> None:
        """Create NATS subscription and start consume task."""
        if self.subscription:
            return

        self.start_consume_task()

        self.subscription = await self._connection_state.js.subscribe(
            subject=self.clear_subject,
            queue=self.queue,
            cb=self._put_msg,
            config=self.config,
            **self.extra_options,
        )

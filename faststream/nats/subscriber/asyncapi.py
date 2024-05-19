from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Union

from nats.aio.subscription import (
    DEFAULT_SUB_PENDING_BYTES_LIMIT,
    DEFAULT_SUB_PENDING_MSGS_LIMIT,
)
from nats.js.client import (
    DEFAULT_JS_SUB_PENDING_BYTES_LIMIT,
    DEFAULT_JS_SUB_PENDING_MSGS_LIMIT,
)
from typing_extensions import override

from faststream.asyncapi.schema import (
    Channel,
    ChannelBinding,
    CorrelationId,
    Message,
    Operation,
)
from faststream.asyncapi.schema.bindings import nats
from faststream.asyncapi.utils import resolve_payloads
from faststream.exceptions import SetupError
from faststream.nats.helpers import stream_builder
from faststream.nats.subscriber.usecase import (
    BatchHandler,
    DefaultHandler,
    LogicSubscriber,
)

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends
    from nats.js import api

    from faststream.broker.types import BrokerMiddleware
    from faststream.nats.schemas import JStream, PullSub
    from faststream.types import AnyDict


class AsyncAPISubscriber(LogicSubscriber[Any]):
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

    @override
    @staticmethod
    def create(  # type: ignore[override]
        *,
        subject: str,
        queue: str,
        pending_msgs_limit: Optional[int],
        pending_bytes_limit: Optional[int],
        # Core args
        max_msgs: int,
        # JS args
        durable: Optional[str],
        config: Optional["api.ConsumerConfig"],
        ordered_consumer: bool,
        idle_heartbeat: Optional[float],
        flow_control: bool,
        deliver_policy: Optional["api.DeliverPolicy"],
        headers_only: Optional[bool],
        # pull args
        pull_sub: Optional["PullSub"],
        inbox_prefix: bytes,
        # custom args
        ack_first: bool,
        max_workers: int,
        stream: Union[str, "JStream", None],
        # Subscriber args
        no_ack: bool,
        retry: Union[bool, int],
        broker_dependencies: Iterable["Depends"],
        broker_middlewares: Iterable["BrokerMiddleware[Any]"],
        # AsyncAPI information
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> Union[
        "AsyncAPIDefaultSubscriber",
        "AsyncAPIBatchSubscriber",
    ]:
        if stream := stream_builder.stream(stream):
            stream.add_subject(subject)

        if pull_sub is not None and stream is None:
            raise SetupError("Pull subscriber can be used only with a stream")

        if stream:
            # TODO: pull & queue warning
            # TODO: push & durable warning

            extra_options: AnyDict = {
                "pending_msgs_limit": pending_msgs_limit
                or DEFAULT_JS_SUB_PENDING_MSGS_LIMIT,
                "pending_bytes_limit": pending_bytes_limit
                or DEFAULT_JS_SUB_PENDING_BYTES_LIMIT,
                "durable": durable,
                "stream": stream.name,
                "config": config,
            }

            if pull_sub is not None:
                extra_options.update({"inbox_prefix": inbox_prefix})

            else:
                extra_options.update(
                    {
                        "ordered_consumer": ordered_consumer,
                        "idle_heartbeat": idle_heartbeat,
                        "flow_control": flow_control,
                        "deliver_policy": deliver_policy,
                        "headers_only": headers_only,
                        "manual_ack": not ack_first,
                    }
                )

        else:
            extra_options = {
                "pending_msgs_limit": pending_msgs_limit
                or DEFAULT_SUB_PENDING_MSGS_LIMIT,
                "pending_bytes_limit": pending_bytes_limit
                or DEFAULT_SUB_PENDING_BYTES_LIMIT,
                "max_msgs": max_msgs,
            }

        if getattr(pull_sub, "batch", False):
            return AsyncAPIBatchSubscriber(
                extra_options=extra_options,
                # basic args
                pull_sub=pull_sub,
                subject=subject,
                queue=queue,
                stream=stream,
                # Subscriber args
                no_ack=no_ack,
                retry=retry,
                broker_dependencies=broker_dependencies,
                broker_middlewares=broker_middlewares,
                # AsyncAPI information
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )

        else:
            return AsyncAPIDefaultSubscriber(
                max_workers=max_workers,
                extra_options=extra_options,
                # basic args
                pull_sub=pull_sub,
                subject=subject,
                queue=queue,
                stream=stream,
                # Subscriber args
                no_ack=no_ack,
                retry=retry,
                broker_dependencies=broker_dependencies,
                broker_middlewares=broker_middlewares,
                # AsyncAPI information
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )


class AsyncAPIDefaultSubscriber(DefaultHandler, AsyncAPISubscriber):
    """One-message consumer with AsyncAPI methods."""


class AsyncAPIBatchSubscriber(BatchHandler, AsyncAPISubscriber):
    """Batch-message consumer with AsyncAPI methods."""

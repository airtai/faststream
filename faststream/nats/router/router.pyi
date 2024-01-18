from typing import Any, Callable, Iterable, Sequence

from fast_depends.dependencies import Depends
from nats.aio.msg import Msg
from nats.js import api
from typing_extensions import override

from faststream.broker.core.broker import default_filter
from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.router import BrokerRouter
from faststream.broker.types import (
    BrokerMiddleware,
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    PublisherMiddleware,
    SubscriberMiddleware,
    T_HandlerReturn,
)
from faststream.nats.asyncapi import Publisher
from faststream.nats.message import NatsMessage
from faststream.nats.schemas import JStream, PullSub

class NatsRoute:
    """Delayed `NatsBroker.subscriber()` registration object."""

    def __init__(
        self,
        call: Callable[..., T_HandlerReturn],
        subject: str,
        queue: str = "",
        pending_msgs_limit: int | None = None,
        pending_bytes_limit: int | None = None,
        # Core arguments
        max_msgs: int = 0,
        ack_first: bool = False,
        # JS arguments
        stream: str | JStream | None = None,
        durable: str | None = None,
        config: api.ConsumerConfig | None = None,
        ordered_consumer: bool = False,
        idle_heartbeat: float | None = None,
        flow_control: bool = False,
        deliver_policy: api.DeliverPolicy | None = None,
        headers_only: bool | None = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: CustomParser[Msg] | None = None,
        decoder: CustomDecoder[NatsMessage] | None = None,
        middlewares: Iterable[BrokerMiddleware[Msg]] = (),
        filter: Filter[NatsMessage] = default_filter,
        retry: bool = False,
        no_ack: bool = False,
        max_workers: int = 1,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> None: ...

class NatsRouter(BrokerRouter[str, Msg]):
    _publishers: dict[str, Publisher]  # type: ignore[assignment]

    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[NatsRoute] = (),
        *,
        dependencies: Sequence[Depends] = (),
        middlewares: Iterable[BrokerMiddleware[Msg]] = (),
        parser: CustomParser[Msg] | None = None,
        decoder: CustomDecoder[NatsMessage] | None = None,
        include_in_schema: bool = True,
    ) -> None: ...
    @override
    @staticmethod
    def _get_publisher_key(publisher: Publisher) -> str: ...  # type: ignore[override]
    @override
    @staticmethod
    def _update_publisher_prefix(  # type: ignore[override]
        prefix: str,
        publisher: Publisher,
    ) -> Publisher: ...
    @override
    def publisher(  # type: ignore[override]
        self,
        subject: str,
        headers: dict[str, str] | None = None,
        # Core
        reply_to: str = "",
        # JS
        stream: str | JStream | None = None,
        timeout: float | None = None,
        # specific
        middlewares: Iterable[PublisherMiddleware] = (),
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        schema: Any | None = None,
        include_in_schema: bool = True,
    ) -> Publisher: ...
    @override
    def subscriber(  # type: ignore[override]
        self,
        subject: str,
        queue: str = "",
        pending_msgs_limit: int | None = None,
        pending_bytes_limit: int | None = None,
        # Core arguments
        max_msgs: int = 0,
        ack_first: bool = False,
        # JS arguments
        stream: str | JStream | None = None,
        durable: str | None = None,
        config: api.ConsumerConfig | None = None,
        ordered_consumer: bool = False,
        idle_heartbeat: float | None = None,
        flow_control: bool = False,
        deliver_policy: api.DeliverPolicy | None = None,
        headers_only: bool | None = None,
        # pull arguments
        pull_sub: PullSub | None = None,
        inbox_prefix: bytes = api.INBOX_PREFIX,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: CustomParser[Msg] | None = None,
        decoder: CustomDecoder[NatsMessage] | None = None,
        middlewares: Iterable[SubscriberMiddleware] = (),
        filter: Filter[NatsMessage] = default_filter,
        retry: bool = False,
        no_ack: bool = False,
        max_workers: int = 1,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Msg, P_HandlerParams, T_HandlerReturn],
    ]: ...

from abc import ABCMeta
from typing import Any, Callable, Sequence

from fast_depends.dependencies import Depends
from nats.aio.msg import Msg
from nats.js import api
from typing_extensions import override

from faststream.broker.core.asynchronous import default_filter
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.router import BrokerRouter
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.nats.js_stream import JStream
from faststream.nats.message import NatsMessage

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
        parser: CustomParser[Msg, NatsMessage] | None = None,
        decoder: CustomDecoder[NatsMessage] | None = None,
        middlewares: Sequence[Callable[[Msg], BaseMiddleware]] | None = None,
        filter: Filter[NatsMessage] = default_filter,
        retry: bool = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> None: ...

class NatsRouter(BrokerRouter[str, Msg], metaclass=ABCMeta):
    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[NatsRoute] = (),
        **kwargs: Any,
    ) -> None: ...
    @override
    def subscriber(  # type: ignore[override]
        self,
        subject: str,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Msg, P_HandlerParams, T_HandlerReturn],
    ]: ...

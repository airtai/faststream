from abc import ABCMeta
from typing import Any, Callable, Optional, Sequence, Union

from fast_depends.dependencies import Depends
from nats.aio.msg import Msg
from nats.js import api

from faststream._compat import override
from faststream.broker.core.asyncronous import default_filter
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
    """Delayed `NatsBroker.subscriber()` registration object"""

    def __init__(
        self,
        call: Callable[..., T_HandlerReturn],
        subject: str,
        queue: str = "",
        pending_msgs_limit: Optional[int] = None,
        pending_bytes_limit: Optional[int] = None,
        # Core arguments
        max_msgs: int = 0,
        ack_first: bool = False,
        # JS arguments
        stream: Union[str, JStream, None] = None,
        durable: Optional[str] = None,
        config: Optional[api.ConsumerConfig] = None,
        ordered_consumer: bool = False,
        idle_heartbeat: Optional[float] = None,
        flow_control: bool = False,
        deliver_policy: Optional[api.DeliverPolicy] = None,
        headers_only: Optional[bool] = None,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[Msg, NatsMessage]] = None,
        decoder: Optional[CustomDecoder[NatsMessage]] = None,
        middlewares: Optional[Sequence[Callable[[Msg], BaseMiddleware]]] = None,
        filter: Filter[NatsMessage] = default_filter,
        retry: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> None: ...

class NatsRouter(BrokerRouter[str, Msg], metaclass=ABCMeta):
    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[NatsRoute] = (),
        **kwargs: Any,
    ): ...
    @override
    def subscriber(  # type: ignore[override]
        self,
        subject: str,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Msg, P_HandlerParams, T_HandlerReturn],
    ]: ...

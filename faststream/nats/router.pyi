from typing import Any, Callable, Dict, Optional, Sequence, Union

from fast_depends.dependencies import Depends
from nats.aio.msg import Msg
from nats.js import api

from faststream._compat import override
from faststream.broker.core.asyncronous import default_filter
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.nats.asyncapi import Publisher
from faststream.nats.js_stream import JStream
from faststream.nats.message import NatsMessage
from faststream.nats.pull_sub import PullSub
from faststream.nats.shared.router import NatsRoute
from faststream.nats.shared.router import NatsRouter as BaseRouter

class NatsRouter(BaseRouter):
    _publishers: Dict[str, Publisher]  # type: ignore[assignment]

    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[NatsRoute] = (),
        *,
        dependencies: Sequence[Depends] = (),
        middlewares: Optional[Sequence[Callable[[Msg], BaseMiddleware]]] = None,
        parser: Optional[CustomParser[Msg, NatsMessage]] = None,
        decoder: Optional[CustomDecoder[NatsMessage]] = None,
        include_in_schema: bool = True,
    ): ...
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
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
    ) -> Publisher: ...
    @override
    def subscriber(  # type: ignore[override]
        self,
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
        # pull arguments
        pull_sub: Optional[PullSub] = None,
        inbox_prefix: bytes = api.INBOX_PREFIX,
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[CustomParser[Msg, NatsMessage]] = None,
        decoder: Optional[CustomDecoder[NatsMessage]] = None,
        middlewares: Optional[Sequence[Callable[[Msg], BaseMiddleware]]] = None,
        filter: Filter[NatsMessage] = default_filter,
        retry: bool = False,
        no_ack: bool = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Msg, P_HandlerParams, T_HandlerReturn],
    ]: ...

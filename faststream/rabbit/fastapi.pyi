from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Sequence,
)

import aio_pika
from aio_pika.message import IncomingMessage
from fastapi import params
from fastapi.datastructures import Default
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from pamqp.common import FieldTable
from starlette import routing
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Lifespan
from typing_extensions import override
from yarl import URL

from faststream.asyncapi import schema as asyncapi
from faststream.broker.core.asynchronous import default_filter
from faststream.broker.fastapi.router import StreamRouter
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.rabbit.asyncapi import Publisher
from faststream.rabbit.broker import RabbitBroker
from faststream.rabbit.message import RabbitMessage
from faststream.rabbit.shared.schemas import RabbitExchange, RabbitQueue, ReplyConfig
from faststream.rabbit.shared.types import TimeoutType
from faststream.security import BaseSecurity
from faststream.types import AnyDict

class RabbitRouter(StreamRouter[IncomingMessage]):
    broker_class: type[RabbitBroker]
    broker: RabbitBroker

    # nosemgrep: python.lang.security.audit.hardcoded-password-default-argument.hardcoded-password-default-argument
    def __init__(
        self,
        url: str
        | URL
        | None = "amqp://guest:guest@localhost:5672/",  # pragma: allowlist secret
        *,
        # aio-pika args
        host: str = "localhost",
        port: int = 5672,
        login: str = "guest",
        password: str = "guest",
        virtualhost: str = "/",
        ssl_options: aio_pika.abc.SSLOptions | None = None,
        timeout: aio_pika.abc.TimeoutType = None,
        client_properties: FieldTable | None = None,
        security: BaseSecurity | None = None,
        # specific args
        max_consumers: int | None = None,
        graceful_timeout: float | None = None,
        # Broker kwargs
        decoder: CustomDecoder[RabbitMessage] | None = None,
        parser: CustomParser[aio_pika.IncomingMessage, RabbitMessage] | None = None,
        middlewares: Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        | None = None,
        # AsyncAPI args
        asyncapi_url: str | None = None,
        protocol: str = "amqp",
        protocol_version: str | None = "0.9.1",
        description: str | None = None,
        asyncapi_tags: Sequence[asyncapi.Tag] | None = None,
        schema_url: str | None = "/asyncapi",
        setup_state: bool = True,
        # FastAPI kwargs
        prefix: str = "",
        tags: list[str | Enum] | None = None,
        dependencies: Sequence[params.Depends] | None = None,
        default_response_class: type[Response] = Default(JSONResponse),
        responses: dict[int | str, dict[str, Any]] | None = None,
        callbacks: list[routing.BaseRoute] | None = None,
        routes: list[routing.BaseRoute] | None = None,
        redirect_slashes: bool = True,
        default: ASGIApp | None = None,
        dependency_overrides_provider: Any | None = None,
        route_class: type[APIRoute] = APIRoute,
        on_startup: Sequence[Callable[[], Any]] | None = None,
        on_shutdown: Sequence[Callable[[], Any]] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        lifespan: Lifespan[Any] | None = None,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id
        ),
    ) -> None: ...
    def add_api_mq_route(  # type: ignore[override]
        self,
        queue: str | RabbitQueue,
        *,
        endpoint: Callable[..., T_HandlerReturn],
        exchange: str | RabbitExchange | None = None,
        consume_args: AnyDict | None = None,
        # broker arguments
        dependencies: Sequence[params.Depends] = (),
        filter: Filter[RabbitMessage] = default_filter,
        parser: CustomParser[aio_pika.IncomingMessage, RabbitMessage] | None = None,
        decoder: CustomDecoder[RabbitMessage] | None = None,
        middlewares: Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        | None = None,
        retry: bool | int = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        **__service_kwargs: Any,
    ) -> Callable[[IncomingMessage, bool], Awaitable[T_HandlerReturn]]: ...
    @override
    def subscriber(  # type: ignore[override]
        self,
        queue: str | RabbitQueue,
        exchange: str | RabbitExchange | None = None,
        *,
        consume_args: AnyDict | None = None,
        reply_config: ReplyConfig | None = None,
        # broker arguments
        dependencies: Sequence[params.Depends] = (),
        filter: Filter[RabbitMessage] = default_filter,
        parser: CustomParser[aio_pika.IncomingMessage, RabbitMessage] | None = None,
        decoder: CustomDecoder[RabbitMessage] | None = None,
        middlewares: Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        | None = None,
        retry: bool | int = False,
        no_ack: bool = False,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        include_in_schema: bool = True,
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[aio_pika.IncomingMessage, P_HandlerParams, T_HandlerReturn],
    ]: ...
    @override
    def publisher(  # type: ignore[override]
        self,
        queue: RabbitQueue | str = "",
        exchange: RabbitExchange | str | None = None,
        *,
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: TimeoutType = None,
        persist: bool = False,
        reply_to: str | None = None,
        # AsyncAPI information
        title: str | None = None,
        description: str | None = None,
        schema: Any | None = None,
        include_in_schema: bool = True,
        # message args
        headers: aio_pika.abc.HeadersType | None = None,
        content_type: str | None = None,
        content_encoding: str | None = None,
        priority: int | None = None,
        correlation_id: str | None = None,
        expiration: aio_pika.abc.DateType | None = None,
        message_id: str | None = None,
        timestamp: aio_pika.abc.DateType | None = None,
        type: str | None = None,
        user_id: str | None = None,
        app_id: str | None = None,
    ) -> Publisher: ...
    @override
    @staticmethod
    def _setup_log_context(  # type: ignore[override]
        main_broker: RabbitBroker,
        including_broker: RabbitBroker,
    ) -> None: ...

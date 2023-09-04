from enum import Enum
from ssl import SSLContext
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
    overload,
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
from starlette.types import AppType, ASGIApp, Lifespan
from yarl import URL

from faststream._compat import override
from faststream.asyncapi import schema as asyncapi
from faststream.broker.core.asyncronous import default_filter
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
from faststream.rabbit.shared.schemas import RabbitExchange, RabbitQueue
from faststream.rabbit.shared.types import TimeoutType
from faststream.types import AnyDict

class RabbitRouter(StreamRouter[IncomingMessage]):
    broker_class: Type[RabbitBroker]

    # nosemgrep: python.lang.security.audit.hardcoded-password-default-argument.hardcoded-password-default-argument
    def __init__(
        self,
        url: Union[str, URL, None] = "amqp://guest:guest@localhost:5672/",
        *,
        # aio-pika args
        host: str = "localhost",
        port: int = 5672,
        login: str = "guest",
        password: str = "guest",
        virtualhost: str = "/",
        ssl: bool = False,
        ssl_options: Optional[aio_pika.abc.SSLOptions] = None,
        ssl_context: Optional[SSLContext] = None,
        timeout: aio_pika.abc.TimeoutType = None,
        client_properties: Optional[FieldTable] = None,
        # specific args
        max_consumers: Optional[int] = None,
        # Broker kwargs
        decoder: Optional[CustomDecoder[aio_pika.IncomingMessage]] = None,
        parser: Optional[CustomParser[aio_pika.IncomingMessage]] = None,
        middlewares: Optional[
            Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        ] = None,
        # AsyncAPI args
        protocol: str = "amqp",
        protocol_version: Optional[str] = "0.9.1",
        description: Optional[str] = None,
        asyncapi_tags: Optional[Sequence[asyncapi.Tag]] = None,
        schema_url: Optional[str] = "/asyncapi",
        # FastAPI kwargs
        prefix: str = "",
        tags: Optional[List[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        callbacks: Optional[List[routing.BaseRoute]] = None,
        routes: Optional[List[routing.BaseRoute]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
        dependency_overrides_provider: Optional[Any] = None,
        route_class: Type[APIRoute] = APIRoute,
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        lifespan: Optional[Lifespan[Any]] = None,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id
        ),
    ) -> None:
        pass
    def add_api_mq_route(  # type: ignore[override]
        self,
        queue: Union[str, RabbitQueue],
        *,
        endpoint: Callable[..., T_HandlerReturn],
        exchange: Union[str, RabbitExchange, None] = None,
        consume_args: Optional[AnyDict] = None,
        # broker arguments
        dependencies: Sequence[params.Depends] = (),
        filter: Filter[RabbitMessage] = default_filter,
        parser: Optional[CustomParser[aio_pika.IncomingMessage]] = None,
        decoder: Optional[CustomDecoder[aio_pika.IncomingMessage]] = None,
        middlewares: Optional[
            Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        ] = None,
        retry: Union[bool, int] = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        **__service_kwargs: Any,
    ) -> Callable[[IncomingMessage, bool], Awaitable[T_HandlerReturn]]:
        pass
    @override
    def subscriber(  # type: ignore[override]
        self,
        queue: Union[str, RabbitQueue],
        exchange: Union[str, RabbitExchange, None] = None,
        *,
        consume_args: Optional[AnyDict] = None,
        # broker arguments
        dependencies: Sequence[params.Depends] = (),
        filter: Filter[RabbitMessage] = default_filter,
        parser: Optional[CustomParser[aio_pika.IncomingMessage]] = None,
        decoder: Optional[CustomDecoder[aio_pika.IncomingMessage]] = None,
        middlewares: Optional[
            Sequence[Callable[[aio_pika.IncomingMessage], BaseMiddleware]]
        ] = None,
        retry: Union[bool, int] = False,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[aio_pika.IncomingMessage, P_HandlerParams, T_HandlerReturn],
    ]: ...
    @override
    def publisher(  # type: ignore[override]
        self,
        queue: Union[RabbitQueue, str] = "",
        exchange: Union[RabbitExchange, str, None] = None,
        *,
        routing_key: str = "",
        mandatory: bool = True,
        immediate: bool = False,
        timeout: TimeoutType = None,
        persist: bool = False,
        reply_to: Optional[str] = None,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        # message args
        headers: Optional[aio_pika.abc.HeadersType] = None,
        content_type: Optional[str] = None,
        content_encoding: Optional[str] = None,
        priority: Optional[int] = None,
        correlation_id: Optional[str] = None,
        expiration: Optional[aio_pika.abc.DateType] = None,
        message_id: Optional[str] = None,
        timestamp: Optional[aio_pika.abc.DateType] = None,
        type: Optional[str] = None,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
    ) -> Publisher: ...
    @overload
    def after_startup(
        self,
        func: Callable[[AppType], Mapping[str, Any]],
    ) -> Callable[[AppType], Mapping[str, Any]]: ...
    @overload
    def after_startup(
        self,
        func: Callable[[AppType], Awaitable[Mapping[str, Any]]],
    ) -> Callable[[AppType], Awaitable[Mapping[str, Any]]]: ...
    @overload
    def after_startup(
        self,
        func: Callable[[AppType], None],
    ) -> Callable[[AppType], None]: ...
    @overload
    def after_startup(
        self,
        func: Callable[[AppType], Awaitable[None]],
    ) -> Callable[[AppType], Awaitable[None]]: ...
    @override
    @staticmethod
    def _setup_log_context(  # type: ignore[override]
        main_broker: RabbitBroker,
        including_broker: RabbitBroker,
    ) -> None: ...

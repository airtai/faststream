import logging
from inspect import Parameter
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Type,
    Union,
)

from fastapi import params
from fastapi.datastructures import Default
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from starlette.responses import JSONResponse
from starlette.routing import BaseRoute
from typing_extensions import Annotated, Doc, deprecated

from faststream.__about__ import SERVICE_NAME
from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.fastapi.router import StreamRouter
from faststream.broker.types import (
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.rabbit.broker import RabbitBroker as RB
from faststream.rabbit.schemas.schemas import RabbitQueue

if TYPE_CHECKING:
    from enum import Enum

    import aio_pika
    from aio_pika.abc import SSLOptions, TimeoutType
    from pamqp.common import FieldTable
    from starlette.responses import Response
    from starlette.types import ASGIApp, Lifespan
    from yarl import URL

    from faststream.asyncapi import schema as asyncapi
    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        BrokerMiddleware,
        CustomDecoder,
        CustomParser,
    )
    from faststream.security import BaseSecurity
    from faststream.types import AnyDict


class RabbitRouter(StreamRouter["aio_pika.IncomingMessage"]):
    """A class to represent a RabbitMQ router for incoming messages.

    Attributes:
        broker_class : the class representing the RabbitMQ broker

    Methods:
        _setup_log_context : sets up the log context for the main broker and the including broker
    """

    broker_class = RB

    def __init__(
        self,
        url: Annotated[
            Union[str, "URL", None],
            Doc("RabbitMQ destination location to connect."),
        ] = "amqp://guest:guest@localhost:5672/",
        *,
        # connection args
        host: Annotated[
            Optional[str],
            Doc("Destination host. This option overrides `url` option host."),
        ] = None,
        port: Annotated[
            Optional[int],
            Doc("Destination port. This option overrides `url` option port."),
        ] = None,
        virtualhost: Annotated[
            Optional[str],
            Doc("RabbitMQ virtual host to use in the current broker connection."),
        ] = None,
        ssl_options: Annotated[
            Optional["SSLOptions"],
            Doc("Extra ssl options to establish connection."),
        ] = None,
        client_properties: Annotated[
            Optional["FieldTable"],
            Doc("Add custom client capability."),
        ] = None,
        timeout: Annotated[
            "TimeoutType",
            Doc("Connection establishement timeout."),
        ] = None,
        # broker args
        max_consumers: Annotated[
            Optional[int],
            Doc(
                "RabbitMQ channel `qos` option. "
                "It limits max messages processing in the same time count."
            ),
        ] = None,
        app_id: Annotated[
            Optional[str],
            Doc("Application name to mark outgoing messages by."),
        ] = SERVICE_NAME,
        # broker base args
        graceful_timeout: Annotated[
            Optional[float],
            Doc(
                "Graceful shutdown timeout. Broker waits for all running subscribers completion before shut down."
            ),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[aio_pika.IncomingMessag]]"],
            Doc("Custom decoder object."),
        ] = None,
        parser: Annotated[
            Optional["CustomParser[aio_pika.IncomingMessag]"],
            Doc("Custom parser object."),
        ] = None,
        middlewares: Annotated[
            Iterable["BrokerMiddleware[aio_pika.IncomingMessag]"],
            Doc("Middlewares to apply to all broker publishers/subscribers."),
        ] = (),
        # AsyncAPI args
        security: Annotated[
            Optional["BaseSecurity"],
            Doc(
                "Security options to connect broker and generate AsyncAPI server security information."
            ),
        ] = None,
        asyncapi_url: Annotated[
            Optional[str],
            Doc("AsyncAPI hardcoded server addresses. Use `servers` if not specified."),
        ] = None,
        protocol: Annotated[
            Optional[str],
            Doc("AsyncAPI server protocol."),
        ] = None,
        protocol_version: Annotated[
            Optional[str],
            Doc("AsyncAPI server protocol version."),
        ] = "0.9.1",
        description: Annotated[
            Optional[str],
            Doc("AsyncAPI server description."),
        ] = None,
        asyncapi_tags: Annotated[
            Optional[Iterable[Union["asyncapi.Tag", "asyncapi.TagDict"]]],
            Doc("AsyncAPI server tags."),
        ] = None,
        # logging args
        logger: Annotated[
            Union[logging.Logger, None, object],
            Doc("User specified logger to pass into Context and log service messages."),
        ] = Parameter.empty,
        log_level: Annotated[
            int,
            Doc("Service messages log level."),
        ] = logging.INFO,
        log_fmt: Annotated[
            Optional[str],
            Doc("Default logger log format."),
        ] = None,
        # StreamRouter options
        setup_state: Annotated[
            bool,
            Doc(
                "Whether to add broker to app scope in lifespan. "
                "You should disable this option at old ASGI servers."
            ),
        ] = True,
        schema_url: Annotated[
            Optional[str],
            Doc(
                "AsyncAPI schema url. You should set this option to `None` to disable AsyncAPI routes at all."
            ),
        ] = "/asyncapi",
        # FastAPI args
        prefix: Annotated[
            str,
            Doc("An optional path prefix for the router."),
        ] = "",
        tags: Annotated[
            Optional[List[Union[str, "Enum"]]],
            Doc(
                """
                A list of tags to be applied to all the *path operations* in this
                router.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/).
                """
            ),
        ] = None,
        dependencies: Annotated[
            Optional[Sequence[params.Depends]],
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied to all the
                *path and stream operations* in this router.

                Read more about it in the
                [FastAPI docs for Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/#include-an-apirouter-with-a-custom-prefix-tags-responses-and-dependencies).
                """
            ),
        ] = None,
        default_response_class: Annotated[
            Type["Response"],
            Doc(
                """
                The default response class to be used.

                Read more in the
                [FastAPI docs for Custom Response - HTML, Stream, File, others](https://fastapi.tiangolo.com/advanced/custom-response/#default-response-class).
                """
            ),
        ] = Default(JSONResponse),
        responses: Annotated[
            Optional[Dict[Union[int, str], "AnyDict"]],
            Doc(
                """
                Additional responses to be shown in OpenAPI.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Additional Responses in OpenAPI](https://fastapi.tiangolo.com/advanced/additional-responses/).

                And in the
                [FastAPI docs for Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/#include-an-apirouter-with-a-custom-prefix-tags-responses-and-dependencies).
                """
            ),
        ] = None,
        callbacks: Annotated[
            Optional[List[BaseRoute]],
            Doc(
                """
                OpenAPI callbacks that should apply to all *path operations* in this
                router.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for OpenAPI Callbacks](https://fastapi.tiangolo.com/advanced/openapi-callbacks/).
                """
            ),
        ] = None,
        routes: Annotated[
            Optional[List[BaseRoute]],
            Doc(
                """
                **Note**: you probably shouldn't use this parameter, it is inherited
                from Starlette and supported for compatibility.

                ---

                A list of routes to serve incoming HTTP and WebSocket requests.
                """
            ),
            deprecated(
                """
                You normally wouldn't use this parameter with FastAPI, it is inherited
                from Starlette and supported for compatibility.

                In FastAPI, you normally would use the *path operation methods*,
                like `router.get()`, `router.post()`, etc.
                """
            ),
        ] = None,
        redirect_slashes: Annotated[
            bool,
            Doc(
                """
                Whether to detect and redirect slashes in URLs when the client doesn't
                use the same format.
                """
            ),
        ] = True,
        default: Annotated[
            Optional["ASGIApp"],
            Doc(
                """
                Default function handler for this router. Used to handle
                404 Not Found errors.
                """
            ),
        ] = None,
        dependency_overrides_provider: Annotated[
            Optional[Any],
            Doc(
                """
                Only used internally by FastAPI to handle dependency overrides.

                You shouldn't need to use it. It normally points to the `FastAPI` app
                object.
                """
            ),
        ] = None,
        route_class: Annotated[
            Type["APIRoute"],
            Doc(
                """
                Custom route (*path operation*) class to be used by this router.

                Read more about it in the
                [FastAPI docs for Custom Request and APIRoute class](https://fastapi.tiangolo.com/how-to/custom-request-and-route/#custom-apiroute-class-in-a-router).
                """
            ),
        ] = APIRoute,
        on_startup: Annotated[
            Optional[Sequence[Callable[[], Any]]],
            Doc(
                """
                A list of startup event handler functions.

                You should instead use the `lifespan` handlers.

                Read more in the [FastAPI docs for `lifespan`](https://fastapi.tiangolo.com/advanced/events/).
                """
            ),
        ] = None,
        on_shutdown: Annotated[
            Optional[Sequence[Callable[[], Any]]],
            Doc(
                """
                A list of shutdown event handler functions.

                You should instead use the `lifespan` handlers.

                Read more in the
                [FastAPI docs for `lifespan`](https://fastapi.tiangolo.com/advanced/events/).
                """
            ),
        ] = None,
        lifespan: Annotated[
            Optional["Lifespan[Any]"],
            Doc(
                """
                A `Lifespan` context manager handler. This replaces `startup` and
                `shutdown` functions with a single context manager.

                Read more in the
                [FastAPI docs for `lifespan`](https://fastapi.tiangolo.com/advanced/events/).
                """
            ),
        ] = None,
        deprecated: Annotated[
            Optional[bool],
            Doc(
                """
                Mark all *path operations* in this router as deprecated.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/).
                """
            ),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc(
                """
                To include (or not) all the *path operations* in this router in the
                generated OpenAPI.

                This affects the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Query Parameters and String Validations](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/#exclude-from-openapi).
                """
            ),
        ] = True,
        generate_unique_id_function: Annotated[
            Callable[["APIRoute"], str],
            Doc(
                """
                Customize the function used to generate unique IDs for the *path
                operations* shown in the generated OpenAPI.

                This is particularly useful when automatically generating clients or
                SDKs for your API.

                Read more about it in the
                [FastAPI docs about how to Generate Clients](https://fastapi.tiangolo.com/advanced/generate-clients/#custom-generate-unique-id-function).
                """
            ),
        ] = Default(generate_unique_id),
    ) -> None:
        super().__init__(
            url,
            host=host,
            port=port,
            virtualhost=virtualhost,
            ssl_options=ssl_options,
            client_properties=client_properties,
            timeout=timeout,
            max_consumers=max_consumers,
            app_id=app_id,
            graceful_timeout=graceful_timeout,
            decoder=decoder,
            parser=parser,
            middlewares=middlewares,
            security=security,
            asyncapi_url=asyncapi_url,
            protocol=protocol,
            protocol_version=protocol_version,
            description=description,
            logger=logger,
            log_level=log_level,
            log_fmt=log_fmt,
            asyncapi_tags=asyncapi_tags,
            schema_url=schema_url,
            setup_state=setup_state,
            # FastAPI kwargs
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            default_response_class=default_response_class,
            responses=responses,
            callbacks=callbacks,
            routes=routes,
            redirect_slashes=redirect_slashes,
            default=default,
            dependency_overrides_provider=dependency_overrides_provider,
            route_class=route_class,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            lifespan=lifespan,
            generate_unique_id_function=generate_unique_id_function,
        )

    def subscriber(  # type: ignore[override]
        self,
        queue: Union[str, RabbitQueue],
        *args: Any,
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[
            "aio_pika.IncomingMessage", P_HandlerParams, T_HandlerReturn
        ],
    ]:
        queue = RabbitQueue.validate(queue)
        return super().subscriber(
            queue.name,
            queue,
            *args,
            **__service_kwargs,
        )

    @staticmethod
    def _setup_log_context(
        main_broker: RB,
        including_broker: RB,
    ) -> None:
        """Sets up the log context for a main broker and an including broker."""
        for h in including_broker.handlers.values():
            main_broker._setup_log_context(h.queue, h.exchange)

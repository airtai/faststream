import json
from contextlib import asynccontextmanager
from enum import Enum
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    overload,
)

from fastapi import APIRouter, FastAPI, params
from fastapi.datastructures import Default
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from pydantic import AnyHttpUrl
from starlette import routing
from starlette.responses import JSONResponse, Response
from starlette.routing import _DefaultLifespan
from starlette.types import AppType, ASGIApp, Lifespan

from faststream.asyncapi.schema import (
    Contact,
    ContactDict,
    ExternalDocs,
    ExternalDocsDict,
    License,
    LicenseDict,
    Schema,
    Tag,
    TagDict,
)
from faststream.asyncapi.site import get_asyncapi_html
from faststream.broker.core.asyncronous import BrokerAsyncUsecase
from faststream.broker.fastapi.route import StreamRoute
from faststream.broker.publisher import BasePublisher
from faststream.broker.schemas import NameRequired
from faststream.broker.types import MsgType, P_HandlerParams, T_HandlerReturn
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.types import AnyDict
from faststream.utils.functions import to_async


class StreamRouter(APIRouter, Generic[MsgType]):
    broker_class: Type[BrokerAsyncUsecase[MsgType, Any]]
    broker: BrokerAsyncUsecase[MsgType, Any]
    docs_router: Optional[APIRouter]
    _after_startup_hooks: List[
        Callable[[AppType], Awaitable[Optional[Mapping[str, Any]]]]
    ]
    schema: Optional[Schema]

    def __init__(
        self,
        *connection_args: Tuple[Any, ...],
        prefix: str = "",
        tags: Optional[List[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        responses: Optional[Dict[Union[int, str], AnyDict]] = None,
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
        setup_state: bool = True,
        lifespan: Optional[Lifespan[Any]] = None,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id
        ),
        # AsyncAPI information
        title: str = "FastStream",
        version: str = "0.1.0",
        description: str = "",
        terms_of_service: Optional[AnyHttpUrl] = None,
        license: Optional[Union[License, LicenseDict, AnyDict]] = None,
        contact: Optional[Union[Contact, ContactDict, AnyDict]] = None,
        identifier: Optional[str] = None,
        asyncapi_tags: Optional[List[Union[Tag, TagDict, AnyDict]]] = None,
        external_docs: Optional[Union[ExternalDocs, ExternalDocsDict, AnyDict]] = None,
        schema_url: Optional[str] = "/asyncapi",
        **connection_kwars: Any,
    ) -> None:
        assert (
            self.broker_class
        ), "You should specify `broker_class` at your implementation"

        self.broker = self.broker_class(
            *connection_args,
            apply_types=False,
            **connection_kwars,
        )

        self.setup_state = setup_state

        # AsyncAPI information
        self.title = title
        self.version = version
        self.description = description
        self.terms_of_service = terms_of_service
        self.license = license
        self.contact = contact
        self.identifier = identifier
        self.asyncapi_tags = asyncapi_tags
        self.external_docs = external_docs
        self.schema = None

        super().__init__(
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
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            generate_unique_id_function=generate_unique_id_function,
            lifespan=self.wrap_lifespan(lifespan),
            on_startup=on_startup,
            on_shutdown=on_shutdown,
        )

        self.docs_router = self.asyncapi_router(schema_url)

        self._after_startup_hooks = []

    def add_api_mq_route(
        self,
        path: Union[NameRequired, str],
        *extra: Union[NameRequired, str],
        endpoint: Callable[P_HandlerParams, T_HandlerReturn],
        dependencies: Sequence[params.Depends],
        **broker_kwargs: Any,
    ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
        route: StreamRoute[MsgType, P_HandlerParams, T_HandlerReturn] = StreamRoute(
            path,
            *extra,
            endpoint=endpoint,
            dependencies=dependencies,
            dependency_overrides_provider=self.dependency_overrides_provider,
            broker=self.broker,
            **broker_kwargs,
        )
        self.routes.append(route)
        return route.handler

    def subscriber(
        self,
        path: Union[str, NameRequired],
        *extra: Union[NameRequired, str],
        dependencies: Optional[Sequence[params.Depends]] = None,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
    ]:
        current_dependencies = self.dependencies.copy()
        if dependencies:
            current_dependencies.extend(dependencies)

        def decorator(
            func: Callable[P_HandlerParams, T_HandlerReturn],
        ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
            return self.add_api_mq_route(
                path,
                *extra,
                endpoint=func,
                dependencies=current_dependencies,
                **broker_kwargs,
            )

        return decorator

    def wrap_lifespan(self, lifespan: Optional[Lifespan[Any]] = None) -> Lifespan[Any]:
        if lifespan is not None:
            lifespan_context = lifespan
        else:
            lifespan_context = _DefaultLifespan(self)

        @asynccontextmanager
        async def start_broker_lifespan(
            app: FastAPI,
        ) -> AsyncIterator[Mapping[str, Any]]:
            from faststream.asyncapi.generate import get_app_schema

            self.schema = get_app_schema(self)
            if self.docs_router:
                app.include_router(self.docs_router)

            async with lifespan_context(app) as maybe_context:
                if maybe_context is None:
                    context: AnyDict = {}
                else:
                    context = dict(maybe_context)

                context.update({"broker": self.broker})
                await self.broker.start()

                for h in self._after_startup_hooks:
                    h_context = await h(app)
                    if h_context:  # pragma: no branch
                        context.update(h_context)

                try:
                    if self.setup_state:
                        yield context
                    else:
                        # NOTE: old asgi compatibility
                        yield  # type: ignore

                finally:
                    await self.broker.close()

        return start_broker_lifespan

    @overload
    def after_startup(
        self,
        func: Callable[[AppType], Mapping[str, Any]],
    ) -> Callable[[AppType], Mapping[str, Any]]:
        ...

    @overload
    def after_startup(
        self,
        func: Callable[[AppType], Awaitable[Mapping[str, Any]]],
    ) -> Callable[[AppType], Awaitable[Mapping[str, Any]]]:
        ...

    @overload
    def after_startup(
        self,
        func: Callable[[AppType], None],
    ) -> Callable[[AppType], None]:
        ...

    @overload
    def after_startup(
        self,
        func: Callable[[AppType], Awaitable[None]],
    ) -> Callable[[AppType], Awaitable[None]]:
        ...

    def after_startup(
        self,
        func: Union[
            Callable[[AppType], Mapping[str, Any]],
            Callable[[AppType], Awaitable[Mapping[str, Any]]],
            Callable[[AppType], None],
            Callable[[AppType], Awaitable[None]],
        ],
    ) -> Union[
        Callable[[AppType], Mapping[str, Any]],
        Callable[[AppType], Awaitable[Mapping[str, Any]]],
        Callable[[AppType], None],
        Callable[[AppType], Awaitable[None]],
    ]:
        self._after_startup_hooks.append(to_async(func))  # type: ignore
        return func

    def publisher(
        self,
        queue: Union[NameRequired, str],
        *publisher_args: Any,
        **publisher_kwargs: Any,
    ) -> BasePublisher[MsgType]:
        return self.broker.publisher(
            queue,
            *publisher_args,
            **publisher_kwargs,
        )

    def asyncapi_router(self, schema_url: Optional[str]) -> Optional[APIRouter]:
        if not self.include_in_schema or not schema_url:
            return None

        def download_app_json_schema() -> Response:
            assert self.schema, "You need to run application lifespan at first"

            return Response(
                content=json.dumps(self.schema.to_jsonable(), indent=4),
                headers={"Content-Type": "application/octet-stream"},
            )

        def download_app_yaml_schema() -> Response:
            assert self.schema, "You need to run application lifespan at first"

            return Response(
                content=self.schema.to_yaml(),
                headers={
                    "Content-Type": "application/octet-stream",
                },
            )

        def serve_asyncapi_schema(
            sidebar: bool = True,
            info: bool = True,
            servers: bool = True,
            operations: bool = True,
            messages: bool = True,
            schemas: bool = True,
            errors: bool = True,
            expandMessageExamples: bool = True,
        ) -> HTMLResponse:
            assert self.schema, "You need to run application lifespan at first"

            return HTMLResponse(
                content=get_asyncapi_html(
                    self.schema,
                    sidebar=sidebar,
                    info=info,
                    servers=servers,
                    operations=operations,
                    messages=messages,
                    schemas=schemas,
                    errors=errors,
                    expand_message_examples=expandMessageExamples,
                    title=self.schema.info.title,
                )
            )

        docs_router = APIRouter(
            prefix=self.prefix,
            tags=["asyncapi"],
            redirect_slashes=self.redirect_slashes,
            default=self.default,
            deprecated=self.deprecated,
        )
        docs_router.get(schema_url)(serve_asyncapi_schema)
        docs_router.get(f"{schema_url}.json")(download_app_json_schema)
        docs_router.get(f"{schema_url}.yaml")(download_app_yaml_schema)
        return docs_router

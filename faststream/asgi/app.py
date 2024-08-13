import traceback
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncIterator, Optional, Sequence, Tuple, Union

import anyio

from faststream.app import FastStream
from faststream.asgi.factories import make_asyncapi_asgi
from faststream.asgi.response import AsgiResponse
from faststream.asgi.websocket import WebSocketClose
from faststream.log.logging import logger

if TYPE_CHECKING:
    from faststream.asgi.types import ASGIApp, Receive, Scope, Send
    from faststream.asyncapi.schema import (
        Contact,
        ContactDict,
        ExternalDocs,
        ExternalDocsDict,
        License,
        LicenseDict,
        Tag,
        TagDict,
    )
    from faststream.broker.core.usecase import BrokerUsecase
    from faststream.types import (
        AnyDict,
        AnyHttpUrl,
        Lifespan,
        LoggerProto,
    )


class AsgiFastStream(FastStream):
    def __init__(
        self,
        broker: Optional["BrokerUsecase[Any, Any]"] = None,
        /,
        asgi_routes: Sequence[Tuple[str, "ASGIApp"]] = (),
        asyncapi_path: Optional[str] = None,
        # regular broker args
        logger: Optional["LoggerProto"] = logger,
        lifespan: Optional["Lifespan"] = None,
        # AsyncAPI args,
        title: str = "FastStream",
        version: str = "0.1.0",
        description: str = "",
        terms_of_service: Optional["AnyHttpUrl"] = None,
        license: Optional[Union["License", "LicenseDict", "AnyDict"]] = None,
        contact: Optional[Union["Contact", "ContactDict", "AnyDict"]] = None,
        tags: Optional[Sequence[Union["Tag", "TagDict", "AnyDict"]]] = None,
        external_docs: Optional[
            Union["ExternalDocs", "ExternalDocsDict", "AnyDict"]
        ] = None,
        identifier: Optional[str] = None,
    ) -> None:
        super().__init__(
            broker=broker,
            logger=logger,
            lifespan=lifespan,
            title=title,
            version=version,
            description=description,
            terms_of_service=terms_of_service,
            license=license,
            contact=contact,
            tags=tags,
            external_docs=external_docs,
            identifier=identifier,
        )

        self.routes = list(asgi_routes)
        if asyncapi_path:
            self.mount(asyncapi_path, make_asyncapi_asgi(self))

    def mount(self, path: str, route: "ASGIApp") -> None:
        self.routes.append((path, route))

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        if scope["type"] == "lifespan":
            await self.lifespan(scope, receive, send)
            return

        if scope["type"] == "http":
            for path, app in self.routes:
                if scope["path"] == path:
                    await app(scope, receive, send)
                    return

        await self.not_found(scope, receive, send)
        return

    @asynccontextmanager
    async def start_lifespan_context(self) -> AsyncIterator[None]:
        async with anyio.create_task_group() as tg, self.lifespan_context():
            tg.start_soon(self._startup)

            try:
                yield
            finally:
                await self._shutdown()
                tg.cancel_scope.cancel()

    async def lifespan(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        """Handle ASGI lifespan messages to start and shutdown the app."""
        started = False
        await receive()  # handle `lifespan.startup` event

        try:
            async with self.start_lifespan_context():
                await send({"type": "lifespan.startup.complete"})
                started = True
                await receive()  # handle `lifespan.shutdown` event

        except BaseException:
            exc_text = traceback.format_exc()
            if started:
                await send({"type": "lifespan.shutdown.failed", "message": exc_text})
            else:
                await send({"type": "lifespan.startup.failed", "message": exc_text})
            raise

        else:
            await send({"type": "lifespan.shutdown.complete"})

    async def not_found(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        not_found_msg = "FastStream doesn't support regular HTTP protocol."

        if scope["type"] == "websocket":
            websocket_close = WebSocketClose(
                code=1000,
                reason=not_found_msg,
            )
            await websocket_close(scope, receive, send)
            return

        response = AsgiResponse(
            body=not_found_msg.encode(),
            status_code=404,
        )

        await response(scope, receive, send)

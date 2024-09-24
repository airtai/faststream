import logging
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

import anyio
from typing_extensions import ParamSpec

from faststream._internal._compat import ExceptionGroup
from faststream._internal.application import Application
from faststream._internal.basic_types import AnyDict, AnyHttpUrl, Lifespan, LoggerProto
from faststream._internal.broker.broker import BrokerUsecase
from faststream._internal.cli.supervisors.utils import set_exit
from faststream._internal.log import logger
from faststream.asgi.app import AsgiFastStream

P_HookParams = ParamSpec("P_HookParams")
T_HookReturn = TypeVar("T_HookReturn")


if TYPE_CHECKING:
    from faststream._internal.basic_types import (
        AnyCallable,
        AnyDict,
        AnyHttpUrl,
        Lifespan,
        LoggerProto,
        SettingField,
    )
    from faststream._internal.broker.broker import BrokerUsecase
    from faststream.asgi.types import ASGIApp
    from faststream.specification.schema.contact import Contact, ContactDict
    from faststream.specification.schema.docs import ExternalDocs, ExternalDocsDict
    from faststream.specification.schema.license import License, LicenseDict
    from faststream.specification.schema.tag import Tag


class FastStream(Application):
    """A class representing a FastStream application."""

    def __init__(
        self,
        broker: Optional["BrokerUsecase[Any, Any]"] = None,
        /,
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
        tags: Optional[Sequence[Union["Tag", "AnyDict"]]] = None,
        external_docs: Optional[
            Union["ExternalDocs", "ExternalDocsDict", "AnyDict"]
        ] = None,
        identifier: Optional[str] = None,
        # hooks
        on_startup: Sequence["AnyCallable"] = (),
        after_startup: Sequence["AnyCallable"] = (),
        on_shutdown: Sequence["AnyCallable"] = (),
        after_shutdown: Sequence["AnyCallable"] = (),
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
            on_startup=on_startup,
            after_startup=after_startup,
            on_shutdown=on_shutdown,
            after_shutdown=after_shutdown,
        )
        self._should_exit = anyio.Event()

    async def run(
        self,
        log_level: int = logging.INFO,
        run_extra_options: Optional[Dict[str, "SettingField"]] = None,
    ) -> None:
        """Run FastStream Application."""
        assert self.broker, "You should setup a broker"  # nosec B101

        set_exit(lambda *_: self.exit(), sync=False)

        async with self.lifespan_context(**(run_extra_options or {})):
            try:
                async with anyio.create_task_group() as tg:
                    tg.start_soon(self._startup, log_level, run_extra_options)
                    await self._should_exit.wait()
                    await self._shutdown(log_level)
                    tg.cancel_scope.cancel()
            except ExceptionGroup as e:
                for ex in e.exceptions:
                    raise ex from None

    def exit(self) -> None:
        """Stop application manually."""
        self._should_exit.set()

    def as_asgi(
        self,
        asgi_routes: Sequence[Tuple[str, "ASGIApp"]] = (),
        asyncapi_path: Optional[str] = None,
    ) -> AsgiFastStream:
        return AsgiFastStream.from_app(self, asgi_routes, asyncapi_path)

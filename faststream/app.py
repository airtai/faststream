import logging
import logging.config
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

import anyio
from typing_extensions import ParamSpec

from faststream._compat import ExceptionGroup
from faststream.cli.supervisors.utils import set_exit
from faststream.exceptions import ValidationError
from faststream.log.logging import logger
from faststream.utils import apply_types, context
from faststream.utils.functions import drop_response_type, fake_context, to_async

P_HookParams = ParamSpec("P_HookParams")
T_HookReturn = TypeVar("T_HookReturn")


if TYPE_CHECKING:
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
        AsyncFunc,
        Lifespan,
        LoggerProto,
        SettingField,
    )


class FastStream:
    """A class representing a FastStream application."""

    _on_startup_calling: List["AsyncFunc"]
    _after_startup_calling: List["AsyncFunc"]
    _on_shutdown_calling: List["AsyncFunc"]
    _after_shutdown_calling: List["AsyncFunc"]

    def __init__(
        self,
        broker: Optional["BrokerUsecase[Any, Any]"] = None,
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
        context.set_global("app", self)

        self.broker = broker
        self.logger = logger
        self.context = context

        self._on_startup_calling = []
        self._after_startup_calling = []
        self._on_shutdown_calling = []
        self._after_shutdown_calling = []

        self.lifespan_context = (
            apply_types(
                func=lifespan,
                wrap_model=drop_response_type,
            )
            if lifespan is not None
            else fake_context
        )

        self.should_exit = False

        # AsyncAPI information
        self.title = title
        self.version = version
        self.description = description
        self.terms_of_service = terms_of_service
        self.license = license
        self.contact = contact
        self.identifier = identifier
        self.asyncapi_tags = tags
        self.external_docs = external_docs

    def set_broker(self, broker: "BrokerUsecase[Any, Any]") -> None:
        """Set already existed App object broker.

        Useful then you create/init broker in `on_startup` hook.
        """
        self.broker = broker

    def on_startup(
        self,
        func: Callable[P_HookParams, T_HookReturn],
    ) -> Callable[P_HookParams, T_HookReturn]:
        """Add hook running BEFORE broker connected.

        This hook also takes an extra CLI options as a kwargs.
        """
        self._on_startup_calling.append(apply_types(to_async(func)))
        return func

    def on_shutdown(
        self,
        func: Callable[P_HookParams, T_HookReturn],
    ) -> Callable[P_HookParams, T_HookReturn]:
        """Add hook running BEFORE broker disconnected."""
        self._on_shutdown_calling.append(apply_types(to_async(func)))
        return func

    def after_startup(
        self,
        func: Callable[P_HookParams, T_HookReturn],
    ) -> Callable[P_HookParams, T_HookReturn]:
        """Add hook running AFTER broker connected."""
        self._after_startup_calling.append(apply_types(to_async(func)))
        return func

    def after_shutdown(
        self,
        func: Callable[P_HookParams, T_HookReturn],
    ) -> Callable[P_HookParams, T_HookReturn]:
        """Add hook running AFTER broker disconnected."""
        self._after_shutdown_calling.append(apply_types(to_async(func)))
        return func

    async def run(
        self,
        log_level: int = logging.INFO,
        run_extra_options: Optional[Dict[str, "SettingField"]] = None,
        sleep_time: float = 0.1,
    ) -> None:
        """Run FastStream Application."""
        assert self.broker, "You should setup a broker"  # nosec B101

        set_exit(lambda *_: self.exit(), sync=False)

        async with self.lifespan_context(**(run_extra_options or {})):
            try:
                async with anyio.create_task_group() as tg:
                    tg.start_soon(self._startup, log_level, run_extra_options)

                    while not self.should_exit:
                        await anyio.sleep(sleep_time)

                    await self._shutdown(log_level)
                    tg.cancel_scope.cancel()
            except ExceptionGroup as e:
                for ex in e.exceptions:
                    raise ex from None

    def exit(self) -> None:
        """Stop application manually."""
        self.should_exit = True

    async def start(
        self,
        **run_extra_options: "SettingField",
    ) -> None:
        """Executes startup hooks and start broker."""
        for func in self._on_startup_calling:
            call = func(**run_extra_options)

            try:
                from pydantic import ValidationError as PValidation

            except ImportError:
                await call

            else:
                try:
                    await call
                except PValidation as e:
                    fields = [str(x["loc"][0]) for x in e.errors()]
                    raise ValidationError(fields=fields) from e

        if self.broker is not None:
            await self.broker.start()

        for func in self._after_startup_calling:
            await func()

    async def stop(self) -> None:
        """Executes shutdown hooks and stop broker."""
        for func in self._on_shutdown_calling:
            await func()

        if self.broker is not None:
            await self.broker.close()

        for func in self._after_shutdown_calling:
            await func()

    async def _startup(
        self,
        log_level: int = logging.INFO,
        run_extra_options: Optional[Dict[str, "SettingField"]] = None,
    ) -> None:
        self._log(log_level, "FastStream app starting...")
        await self.start(**(run_extra_options or {}))
        self._log(
            log_level, "FastStream app started successfully! To exit, press CTRL+C"
        )

    async def _shutdown(self, log_level: int = logging.INFO) -> None:
        self._log(log_level, "FastStream app shutting down...")
        await self.stop()
        self._log(log_level, "FastStream app shut down gracefully.")

    def _log(self, level: int, message: str) -> None:
        if self.logger is not None:
            self.logger.log(level, message)

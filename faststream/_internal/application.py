import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

from typing_extensions import ParamSpec

from faststream._internal.context import context
from faststream._internal.log import logger
from faststream._internal.setup.state import EmptyState
from faststream._internal.utils import apply_types
from faststream._internal.utils.functions import (
    drop_response_type,
    fake_context,
    to_async,
)
from faststream.specification.proto import SpecApplication

P_HookParams = ParamSpec("P_HookParams")
T_HookReturn = TypeVar("T_HookReturn")


if TYPE_CHECKING:
    from faststream._internal.basic_types import (
        AnyDict,
        AnyHttpUrl,
        AsyncFunc,
        Lifespan,
        LoggerProto,
        SettingField,
    )
    from faststream._internal.broker.broker import BrokerUsecase
    from faststream.specification.schema.contact import Contact, ContactDict
    from faststream.specification.schema.docs import ExternalDocs, ExternalDocsDict
    from faststream.specification.schema.license import License, LicenseDict
    from faststream.specification.schema.tag import Tag, TagDict


class StartAbleApplication(ABC, SpecApplication):
    def __init__(
        self,
        broker: Optional["BrokerUsecase[Any, Any]"] = None,
    ) -> None:
        self._state = EmptyState()

        self.broker = broker

    def _setup(self) -> None:
        if self.broker is not None:
            self.broker._setup(self._state)

    async def _start_broker(self) -> None:
        if self.broker is not None:
            await self.broker.connect()
            self._setup()
            await self.broker.start()


class Application(StartAbleApplication):
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
        on_startup: Sequence[Callable[P_HookParams, T_HookReturn]] = (),
        after_startup: Sequence[Callable[P_HookParams, T_HookReturn]] = (),
        on_shutdown: Sequence[Callable[P_HookParams, T_HookReturn]] = (),
        after_shutdown: Sequence[Callable[P_HookParams, T_HookReturn]] = (),
    ) -> None:
        super().__init__(broker)

        context.set_global("app", self)

        self.logger = logger
        self.context = context

        self._on_startup_calling: List[AsyncFunc] = [
            apply_types(to_async(x)) for x in on_startup
        ]
        self._after_startup_calling: List[AsyncFunc] = [
            apply_types(to_async(x)) for x in after_startup
        ]
        self._on_shutdown_calling: List[AsyncFunc] = [
            apply_types(to_async(x)) for x in on_shutdown
        ]
        self._after_shutdown_calling: List[AsyncFunc] = [
            apply_types(to_async(x)) for x in after_shutdown
        ]

        if lifespan is not None:
            self.lifespan_context = apply_types(
                func=lifespan, wrap_model=drop_response_type
            )
        else:
            self.lifespan_context = fake_context

        # AsyncAPI information
        self.title = title
        self.version = version
        self.description = description
        self.terms_of_service = terms_of_service
        self.license = license
        self.contact = contact
        self.identifier = identifier
        self.specification_tags = tags
        self.external_docs = external_docs

    @abstractmethod
    def exit(self) -> None:
        """Stop application manually."""
        ...

    @abstractmethod
    async def run(
        self,
        log_level: int,
        run_extra_options: Optional[Dict[str, "SettingField"]] = None,
    ) -> None: ...

    # Startup

    async def _startup(
        self,
        log_level: int = logging.INFO,
        run_extra_options: Optional[Dict[str, "SettingField"]] = None,
    ) -> None:
        """Private method calls `start` with logging."""
        async with self._startup_logging(log_level=log_level):
            await self.start(**(run_extra_options or {}))

    async def start(
        self,
        **run_extra_options: "SettingField",
    ) -> None:
        """Executes startup hooks and start broker."""
        async with self._start_hooks_context(**run_extra_options):
            await self._start_broker()

    @asynccontextmanager
    async def _start_hooks_context(
        self,
        **run_extra_options: "SettingField",
    ) -> AsyncIterator[None]:
        async with catch_startup_validation_error():
            for func in self._on_startup_calling:
                await func(**run_extra_options)

        yield

        for func in self._after_startup_calling:
            await func()

    @asynccontextmanager
    async def _startup_logging(
        self, log_level: int = logging.INFO
    ) -> AsyncIterator[None]:
        """Separated startup logging."""
        self._log(
            log_level,
            "FastStream app starting...",
        )

        yield

        self._log(
            log_level,
            "FastStream app started successfully! To exit, press CTRL+C",
        )

    # Shutdown

    async def _shutdown(self, log_level: int = logging.INFO) -> None:
        """Private method calls `stop` with logging."""
        async with self._shutdown_logging(log_level=log_level):
            await self.stop()

    async def stop(self) -> None:
        """Executes shutdown hooks and stop broker."""
        async with self._shutdown_hooks_context():
            if self.broker is not None:
                await self.broker.close()

    @asynccontextmanager
    async def _shutdown_hooks_context(self) -> AsyncIterator[None]:
        for func in self._on_shutdown_calling:
            await func()

        yield

        for func in self._after_shutdown_calling:
            await func()

    @asynccontextmanager
    async def _shutdown_logging(
        self, log_level: int = logging.INFO
    ) -> AsyncIterator[None]:
        """Separated startup logging."""
        self._log(log_level, "FastStream app shutting down...")

        yield

        self._log(
            log_level,
            "FastStream app shut down gracefully.",
        )

    # Setvice methods

    def _log(self, level: int, message: str) -> None:
        if self.logger is not None:
            self.logger.log(level, message)

    def set_broker(self, broker: "BrokerUsecase[Any, Any]") -> None:
        """Set already existed App object broker.

        Useful then you create/init broker in `on_startup` hook.
        """
        self.broker = broker

    # Hooks

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


try:
    from pydantic import ValidationError as PValidation

    from faststream.exceptions import StartupValidationError

    @asynccontextmanager
    async def catch_startup_validation_error() -> AsyncIterator[None]:
        try:
            yield
        except PValidation as e:
            missed_fields = []
            invalid_fields = []
            for x in e.errors():
                location = str(x["loc"][0])
                if x["type"] == "missing":
                    missed_fields.append(location)
                else:
                    invalid_fields.append(location)

            raise StartupValidationError(
                missed_fields=missed_fields,
                invalid_fields=invalid_fields,
            ) from e

except ImportError:
    catch_startup_validation_error = fake_context

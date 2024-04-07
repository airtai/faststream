from contextlib import ExitStack
from functools import partial
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, TypeVar

from anyio.from_thread import start_blocking_portal

from faststream.broker.core.usecase import BrokerUsecase

if TYPE_CHECKING:
    from types import TracebackType

    from faststream.app import FastStream
    from faststream.types import SettingField

Broker = TypeVar("Broker", bound=BrokerUsecase[Any, Any])


class TestApp:
    """A class to represent a test application."""

    __test__ = False

    app: "FastStream"
    _extra_options: Dict[str, "SettingField"]

    def __init__(
        self,
        app: "FastStream",
        run_extra_options: Optional[Dict[str, "SettingField"]] = None,
    ) -> None:
        self.app = app
        self._extra_options = run_extra_options or {}

    def __enter__(self) -> "FastStream":
        with ExitStack() as stack:
            portal = stack.enter_context(start_blocking_portal())

            lifespan_context = self.app.lifespan_context(**self._extra_options)
            stack.enter_context(portal.wrap_async_context_manager(lifespan_context))
            portal.call(partial(self.app.start, **self._extra_options))

            @stack.callback
            def wait_shutdown() -> None:
                portal.call(self.app.stop)

            self.exit_stack = stack.pop_all()

        return self.app

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> None:
        self.exit_stack.close()

    async def __aenter__(self) -> "FastStream":
        self.lifespan_scope = self.app.lifespan_context(**self._extra_options)
        await self.lifespan_scope.__aenter__()
        await self.app.start(**self._extra_options)
        return self.app

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> None:
        """Exit the asynchronous context manager."""
        await self.app.stop()
        await self.lifespan_scope.__aexit__(exc_type, exc_val, exc_tb)

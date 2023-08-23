import logging
from types import TracebackType
from typing import Any, Optional, Type, TypeVar

Cls = TypeVar("Cls")


class CriticalLogMiddleware:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def __call__(self: Cls, msg: Any) -> Cls:
        return self

    async def __aenter__(self: Cls) -> Cls:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> bool:
        if exc_type and exc_val:
            self.logger.critical(f"{exc_type.__name__}: {exc_val}", exc_info=exc_val)
        return True

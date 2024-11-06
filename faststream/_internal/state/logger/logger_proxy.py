from typing import TYPE_CHECKING, Optional, Protocol

from faststream.exceptions import IncorrectState

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict, LoggerProto


class LoggerObject(Protocol):
    logger: Optional["LoggerProto"]

    def __bool__(self) -> bool: ...

    def log(
        self,
        message: str,
        log_level: int,
        extra: Optional["AnyDict"] = None,
        exc_info: Optional[Exception] = None,
    ) -> None: ...


class NotSetLoggerObject(LoggerObject):
    """Default logger proxy for state.

    Raises an error if user tries to log smth before state setup.
    """

    def __init__(self) -> None:
        self.logger = None

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def log(
        self,
        message: str,
        log_level: int,
        extra: Optional["AnyDict"] = None,
        exc_info: Optional[Exception] = None,
    ) -> None:
        msg = "Logger object not set. Please, call `_setup_logger_state` of parent broker state."
        raise IncorrectState(msg)


class EmptyLoggerObject(LoggerObject):
    """Empty logger proxy for state.

    Will be used if user setup `logger=None`.
    """

    def __init__(self) -> None:
        self.logger = None

    def __bool__(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def log(
        self,
        message: str,
        log_level: int,
        extra: Optional["AnyDict"] = None,
        exc_info: Optional[Exception] = None,
    ) -> None:
        pass


class RealLoggerObject(LoggerObject):
    """Empty logger proxy for state.

    Will be used if user setup custom `logger` (.params_storage.ManualLoggerStorage)
    or in default logger case (.params_storage.DefaultLoggerStorage).
    """

    def __init__(self, logger: "LoggerProto") -> None:
        self.logger = logger

    def __bool__(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(logger={self.logger})"

    def log(
        self,
        message: str,
        log_level: int,
        extra: Optional["AnyDict"] = None,
        exc_info: Optional[Exception] = None,
    ) -> None:
        self.logger.log(
            log_level,
            message,
            extra=extra,
            exc_info=exc_info,
        )

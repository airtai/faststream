import warnings
from dataclasses import dataclass, field
from typing import Optional, Protocol, Type

from faststream._internal.basic_types import AnyDict, LoggerProto
from faststream._internal.constants import EMPTY
from faststream.exceptions import IncorrectState

from .proto import SetupAble

__all__ = (
    "make_logger_state",
    "LoggerState",
    "LoggerParamsStorage",
    "DefaultLoggerStorage",
)


def make_logger_state(
    logger: Optional["LoggerProto"],
    log_level: int,
    log_fmt: Optional[str],
    default_storag_cls: Type["DefaultLoggerStorage"],
) -> "LoggerState":
    if logger is not EMPTY and log_fmt:
        warnings.warn(
            message="You can't set custom `logger` with `log_fmt` both.",
            category=RuntimeWarning,
            stacklevel=1,
        )

    if logger is EMPTY:
        storage = default_storag_cls(log_fmt)
    elif logger is None:
        storage = _EmptyLoggerStorage()
    else:
        storage = _ManualLoggerStorage(logger)

    return LoggerState(
        log_level=log_level,
        params_storage=storage,
    )


class _LoggerObject(Protocol):
    def log(
        self,
        message: str,
        log_level: int,
        extra: Optional["AnyDict"] = None,
        exc_info: Optional[Exception] = None,
    ) -> None: ...


class _NotSetLoggerObject(_LoggerObject):
    def log(
        self,
        message: str,
        log_level: int,
        extra: Optional["AnyDict"] = None,
        exc_info: Optional[Exception] = None,
    ) -> None:
        raise IncorrectState("Logger object was not set up.")


class _EmptyLoggerObject(_LoggerObject):
    def log(
        self,
        message: str,
        log_level: int,
        extra: Optional["AnyDict"] = None,
        exc_info: Optional[Exception] = None,
    ) -> None:
        pass


class _RealLoggerObject(_LoggerObject):
    def __init__(self, logger: "LoggerProto") -> None:
        self.logger = logger

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


class LoggerParamsStorage(Protocol):
    def setup_log_contest(self, params: "AnyDict") -> None: ...

    def get_logger(self) -> Optional["LoggerProto"]: ...


class _EmptyLoggerStorage(LoggerParamsStorage):
    def setup_log_contest(self, params: AnyDict) -> None:
        pass

    def get_logger(self) -> None:
        return None


class _ManualLoggerStorage(LoggerParamsStorage):
    def __init__(self, logger: "LoggerProto") -> None:
        self.__logger = logger

    def setup_log_contest(self, params: AnyDict) -> None:
        pass

    def get_logger(self) -> LoggerProto:
        return self.__logger


class DefaultLoggerStorage(LoggerParamsStorage):
    def __init__(self, log_fmt: Optional[str]) -> None:
        self._log_fmt = log_fmt


@dataclass(slots=True)
class LoggerState(SetupAble):
    log_level: int
    params_storage: LoggerParamsStorage

    logger: _LoggerObject = field(default=_NotSetLoggerObject(), init=False)

    def log(
        self,
        message: str,
        log_level: Optional[int] = None,
        extra: Optional["AnyDict"] = None,
        exc_info: Optional[Exception] = None,
    ) -> None:
        self.logger.log(
            log_level=(log_level or self.log_level),
            message=message,
            extra=extra,
            exc_info=exc_info,
        )

    def _setup(self) -> None:
        if logger := self.params_storage.get_logger():
            self.logger = _RealLoggerObject(logger)
        else:
            self.logger = _EmptyLoggerObject()

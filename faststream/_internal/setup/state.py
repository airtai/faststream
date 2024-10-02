from abc import abstractmethod, abstractproperty
from typing import Optional

from faststream.exceptions import IncorrectState

from .fast_depends import FastDependsData
from .logger import LoggerState
from .proto import SetupAble


class BaseState(SetupAble):
    _depends_params: FastDependsData
    _logger_params: LoggerState

    @abstractproperty
    def depends_params(self) -> FastDependsData:
        raise NotImplementedError

    @abstractproperty
    def logger_state(self) -> LoggerState:
        raise NotImplementedError

    @abstractmethod
    def __bool__(self) -> bool:
        raise NotImplementedError

    def _setup(self) -> None:
        self.logger_state._setup()

    def copy_with_params(
        self,
        *,
        depends_params: Optional[FastDependsData] = None,
        logger_state: Optional[LoggerState] = None,
    ) -> "SetupState":
        return self.__class__(
            logger_state=logger_state or self._logger_params,
            depends_params=depends_params or self._depends_params,
        )

    def copy_to_state(self, state_cls: type["SetupState"]) -> "SetupState":
        return state_cls(
            depends_params=self._depends_params,
            logger_state=self._logger_params,
        )


class SetupState(BaseState):
    """State after broker._setup() called."""

    def __init__(
        self,
        *,
        logger_state: LoggerState,
        depends_params: FastDependsData,
    ) -> None:
        self._depends_params = depends_params
        self._logger_params = logger_state

    @property
    def depends_params(self) -> FastDependsData:
        return self._depends_params

    @property
    def logger_state(self) -> LoggerState:
        return self._logger_params

    def __bool__(self) -> bool:
        return True


class EmptyState(BaseState):
    """Initial state for App, broker, etc."""

    def __init__(
        self,
        *,
        logger_state: Optional[LoggerState] = None,
        depends_params: Optional[FastDependsData] = None,
    ) -> None:
        self._depends_params = depends_params
        self._logger_params = logger_state

    @property
    def depends_params(self) -> FastDependsData:
        if not self._depends_params:
            raise IncorrectState

        return self._depends_params

    @property
    def logger_state(self) -> LoggerState:
        if not self._logger_params:
            raise IncorrectState

        return self._logger_params

    def __bool__(self) -> bool:
        return False

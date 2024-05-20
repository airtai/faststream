import logging
from abc import ABC, abstractmethod
from collections import Counter
from typing import TYPE_CHECKING, Any, Optional, Type, Union
from typing import Counter as CounterType

from faststream._compat import is_test_env
from faststream.exceptions import (
    AckMessage,
    HandlerException,
    NackMessage,
    RejectMessage,
    SkipMessage,
)

if TYPE_CHECKING:
    from types import TracebackType

    from faststream.broker.message import StreamMessage
    from faststream.broker.types import MsgType
    from faststream.types import LoggerProto


class BaseWatcher(ABC):
    """A base class for a watcher."""

    max_tries: int

    def __init__(
        self,
        max_tries: int = 0,
        logger: Optional["LoggerProto"] = None,
    ) -> None:
        self.logger = logger
        self.max_tries = max_tries

    @abstractmethod
    def add(self, message_id: str) -> None:
        """Add a message."""
        raise NotImplementedError()

    @abstractmethod
    def is_max(self, message_id: str) -> bool:
        """Check if the given message ID is the maximum attempt."""
        raise NotImplementedError()

    @abstractmethod
    def remove(self, message_id: str) -> None:
        """Remove a message."""
        raise NotImplementedError()


class EndlessWatcher(BaseWatcher):
    """A class to watch and track messages."""

    def add(self, message_id: str) -> None:
        """Add a message to the list."""
        pass

    def is_max(self, message_id: str) -> bool:
        """Check if the given message ID is the maximum attempt."""
        return False

    def remove(self, message_id: str) -> None:
        """Remove a message."""
        pass


class OneTryWatcher(BaseWatcher):
    """A class to watch and track messages."""

    def add(self, message_id: str) -> None:
        """Add a message."""
        pass

    def is_max(self, message_id: str) -> bool:
        """Check if the given message ID is the maximum attempt."""
        return True

    def remove(self, message_id: str) -> None:
        """Remove a message."""
        pass


class CounterWatcher(BaseWatcher):
    """A class to watch and track the count of messages."""

    memory: CounterType[str]

    def __init__(
        self,
        max_tries: int = 3,
        logger: Optional["LoggerProto"] = None,
    ) -> None:
        super().__init__(logger=logger, max_tries=max_tries)
        self.memory = Counter()

    def add(self, message_id: str) -> None:
        """Check if the given message ID is the maximum attempt."""
        self.memory[message_id] += 1

    def is_max(self, message_id: str) -> bool:
        """Check if the number of tries for a message has exceeded the maximum allowed tries."""
        is_max = self.memory[message_id] > self.max_tries
        if self.logger is not None:
            if is_max:
                self.logger.log(
                    logging.ERROR, f"Already retried {self.max_tries} times. Skipped."
                )
            else:
                self.logger.log(
                    logging.ERROR, "Error is occurred. Pushing back to queue."
                )
        return is_max

    def remove(self, message_id: str) -> None:
        """Remove a message from memory."""
        self.memory[message_id] = 0
        self.memory += Counter()


class WatcherContext:
    """A class representing a context for a watcher."""

    def __init__(
        self,
        message: "StreamMessage[MsgType]",
        watcher: BaseWatcher,
        logger: Optional["LoggerProto"] = None,
        **extra_options: Any,
    ) -> None:
        self.watcher = watcher
        self.message = message
        self.extra_options = extra_options
        self.logger = logger

    async def __aenter__(self) -> None:
        self.watcher.add(self.message.message_id)

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional["TracebackType"],
    ) -> bool:
        """Exit the asynchronous context manager."""
        if not exc_type:
            await self.__ack()

        elif isinstance(exc_val, HandlerException):
            if isinstance(exc_val, SkipMessage):
                self.watcher.remove(self.message.message_id)

            elif isinstance(exc_val, AckMessage):
                await self.__ack()

            elif isinstance(exc_val, NackMessage):
                if self.watcher.is_max(self.message.message_id):
                    await self.__reject()
                else:
                    await self.__nack()

            elif isinstance(exc_val, RejectMessage):  # pragma: no branch
                await self.__reject()

            return True

        elif self.watcher.is_max(self.message.message_id):
            await self.__reject()

        else:
            await self.__nack()

        return not is_test_env()

    async def __ack(self) -> None:
        try:
            await self.message.ack(**self.extra_options)
        except Exception as er:
            if self.logger is not None:
                self.logger.log(logging.ERROR, er, exc_info=er)
        else:
            self.watcher.remove(self.message.message_id)

    async def __nack(self) -> None:
        try:
            await self.message.nack(**self.extra_options)
        except Exception as er:
            if self.logger is not None:
                self.logger.log(logging.ERROR, er, exc_info=er)

    async def __reject(self) -> None:
        try:
            await self.message.reject(**self.extra_options)
        except Exception as er:
            if self.logger is not None:
                self.logger.log(logging.ERROR, er, exc_info=er)
        else:
            self.watcher.remove(self.message.message_id)


def get_watcher(
    logger: Optional["LoggerProto"],
    try_number: Union[bool, int],
) -> BaseWatcher:
    """Get a watcher object based on the provided parameters.

    Args:
        logger: Optional logger object for logging messages.
        try_number: Optional parameter to specify the type of watcher.
            - If set to True, an EndlessWatcher object will be returned.
            - If set to False, a OneTryWatcher object will be returned.
            - If set to an integer, a CounterWatcher object with the specified maximum number of tries will be returned.
    """
    watcher: Optional[BaseWatcher]
    if try_number is True:
        watcher = EndlessWatcher()
    elif try_number is False:
        watcher = OneTryWatcher()
    else:
        watcher = CounterWatcher(logger=logger, max_tries=try_number)
    return watcher

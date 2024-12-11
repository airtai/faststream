from typing import TYPE_CHECKING, Protocol

from faststream.exceptions import IncorrectState

if TYPE_CHECKING:
    from aio_pika import RobustChannel, RobustConnection


class ConnectionState(Protocol):
    connection: "RobustConnection"
    channel: "RobustChannel"


class EmptyConnectionState(ConnectionState):
    __slots__ = ()

    error_msg = "You should connect broker first."

    @property
    def connection(self) -> "RobustConnection":
        raise IncorrectState(self.error_msg)

    @property
    def channel(self) -> "RobustChannel":
        raise IncorrectState(self.error_msg)


class ConnectedState(ConnectionState):
    __slots__ = ("channel", "connection")

    def __init__(
        self, connection: "RobustConnection", channel: "RobustChannel"
    ) -> None:
        self.connection = connection
        self.channel = channel

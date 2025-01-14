from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from faststream._internal.constants import EMPTY
from faststream.middlewares import AckPolicy

if TYPE_CHECKING:
    from fast_depends.dependencies import Dependant

    from faststream._internal.types import (
        AsyncCallable,
        BrokerMiddleware,
        MsgType,
    )


@dataclass
class InternalOptions:
    no_reply: bool
    broker_dependencies: Iterable["Dependant"]
    broker_middlewares: Sequence["BrokerMiddleware[MsgType]"]
    ack_policy: AckPolicy
    default_parser: Optional["AsyncCallable"] = field(default_factory=EMPTY)
    default_decoder: Optional["AsyncCallable"] = field(default_factory=EMPTY)

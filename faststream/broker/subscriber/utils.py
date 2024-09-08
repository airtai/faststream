from contextlib import AsyncExitStack
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Iterable,
    Optional,
)

from typing_extensions import Literal, overload

from faststream.broker.types import MsgType
from faststream.utils.functions import return_input

if TYPE_CHECKING:
    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        BrokerMiddleware,
    )


@overload
async def process_msg(
    msg: Literal[None],
    middlewares: Iterable["BrokerMiddleware[MsgType]"],
    parser: Callable[[MsgType], Awaitable["StreamMessage[MsgType]"]],
    decoder: Callable[["StreamMessage[MsgType]"], "Any"],
) -> None: ...


@overload
async def process_msg(
    msg: MsgType,
    middlewares: Iterable["BrokerMiddleware[MsgType]"],
    parser: Callable[[MsgType], Awaitable["StreamMessage[MsgType]"]],
    decoder: Callable[["StreamMessage[MsgType]"], "Any"],
) -> "StreamMessage[MsgType]": ...


async def process_msg(
    msg: Optional[MsgType],
    middlewares: Iterable["BrokerMiddleware[MsgType]"],
    parser: Callable[[MsgType], Awaitable["StreamMessage[MsgType]"]],
    decoder: Callable[["StreamMessage[MsgType]"], "Any"],
) -> Optional["StreamMessage[MsgType]"]:
    if msg is None:
        return None

    async with AsyncExitStack() as stack:
        return_msg: Callable[
            [StreamMessage[MsgType]],
            Awaitable[StreamMessage[MsgType]],
        ] = return_input

        for m in middlewares:
            mid = m(msg)
            await stack.enter_async_context(mid)
            return_msg = partial(mid.consume_scope, return_msg)

        parsed_msg = await parser(msg)
        parsed_msg._decoded_body = await decoder(parsed_msg)
        return await return_msg(parsed_msg)

    raise AssertionError("unreachable")

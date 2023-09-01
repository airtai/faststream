from abc import abstractmethod
from contextlib import AsyncExitStack
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

from fast_depends.core import CallModel

from faststream._compat import IS_OPTIMIZED, override
from faststream.asyncapi.base import AsyncAPIOperation
from faststream.asyncapi.utils import to_camelcase
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.types import (
    AsyncDecoder,
    AsyncParser,
    CustomDecoder,
    CustomParser,
    Filter,
    MsgType,
    P_HandlerParams,
    SyncDecoder,
    SyncParser,
    T_HandlerReturn,
    WrappedReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.exceptions import StopConsume
from faststream.types import SendableMessage
from faststream.utils.functions import to_async


class BaseHandler(AsyncAPIOperation, Generic[MsgType]):
    calls: Union[
        List[
            Tuple[
                HandlerCallWrapper[MsgType, Any, SendableMessage],  # handler
                Callable[[StreamMessage[MsgType]], bool],  # filter
                SyncParser[MsgType],  # parser
                SyncDecoder[MsgType],  # decoder
                Sequence[Callable[[Any], BaseMiddleware]],  # middlewares
                CallModel[Any, SendableMessage],  # dependant
            ]
        ],
        List[
            Tuple[
                HandlerCallWrapper[MsgType, Any, SendableMessage],  # handler
                Callable[[StreamMessage[MsgType]], Awaitable[bool]],  # filter
                AsyncParser[MsgType],  # parser
                AsyncDecoder[MsgType],  # decoder
                Sequence[Callable[[Any], BaseMiddleware]],  # middlewares
                CallModel[Any, SendableMessage],  # dependant
            ]
        ],
    ]

    global_middlewares: Sequence[Callable[[Any], BaseMiddleware]]
    is_test: bool

    def __init__(
        self,
        *,
        description: Optional[str] = None,
        title: Optional[str] = None,
    ):
        self.calls = []  # type: ignore[assignment]
        self.global_middlewares = []
        # AsyncAPI information
        self._description = description
        self._title = title
        self.is_test = False

    def set_test(self) -> None:
        self.is_test = True

    @override
    @property
    def name(self) -> Union[str, bool]:  # type: ignore[override]
        if self._title:
            return self._title

        if not self.calls:  # pragma: no cover
            return False

        else:
            return True

    @property
    def call_name(self) -> str:
        caller = self.calls[0][0]._original_call
        name = getattr(caller, "__name__", str(caller))
        return to_camelcase(name)

    @property
    def description(self) -> Optional[str]:
        if not self.calls:  # pragma: no cover
            description = None

        else:
            caller = self.calls[0][0]._original_call
            description = getattr(caller, "__doc__", None)

        return self._description or description

    @abstractmethod
    def consume(self, msg: MsgType) -> SendableMessage:
        raise NotImplementedError()


class AsyncHandler(BaseHandler[MsgType]):
    calls: List[
        Tuple[
            HandlerCallWrapper[MsgType, Any, SendableMessage],  # handler
            Callable[[StreamMessage[MsgType]], Awaitable[bool]],  # filter
            AsyncParser[MsgType],  # parser
            AsyncDecoder[MsgType],  # decoder
            Sequence[Callable[[Any], BaseMiddleware]],  # middlewares
            CallModel[Any, SendableMessage],  # dependant
        ]
    ]

    def add_call(
        self,
        *,
        handler: HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
        parser: CustomParser[MsgType],
        decoder: CustomDecoder[MsgType],
        dependant: CallModel[P_HandlerParams, T_HandlerReturn],
        filter: Filter[StreamMessage[MsgType]],
        middlewares: Optional[Sequence[Callable[[Any], BaseMiddleware]]],
    ) -> None:
        self.calls.append(
            (  # type: ignore[arg-type]
                handler,
                to_async(filter),
                to_async(parser) if parser else None,
                to_async(decoder) if decoder else None,
                middlewares or (),
                dependant,
            )
        )

    @override
    async def consume(self, msg: MsgType) -> SendableMessage:  # type: ignore[override]
        result: Optional[WrappedReturn[SendableMessage]] = None
        result_msg: SendableMessage = None

        async with AsyncExitStack() as stack:
            gl_middlewares: List[BaseMiddleware] = []

            for m in self.global_middlewares:
                gl_middlewares.append(await stack.enter_async_context(m(msg)))

            processed = False
            for handler, filter_, parser, decoder, middlewares, _ in self.calls:
                local_middlewares: List[BaseMiddleware] = []
                for local_m in middlewares:
                    local_middlewares.append(
                        await stack.enter_async_context(local_m(msg))
                    )

                all_middlewares = gl_middlewares + local_middlewares

                # TODO: add parser & decoder cashes
                message = await parser(msg)
                message.decoded_body = await decoder(message)
                message.processed = processed

                if await filter_(message):
                    if processed:
                        raise RuntimeError(
                            "You can't proccess a message with multiple consumers"
                        )

                    try:
                        async with AsyncExitStack() as consume_stack:
                            for m_consume in all_middlewares:
                                message.decoded_body = (
                                    await consume_stack.enter_async_context(
                                        m_consume.consume_scope(message.decoded_body)
                                    )
                                )

                            result = await cast(
                                Awaitable[Optional[WrappedReturn[SendableMessage]]],
                                handler.call_wrapped(message),
                            )

                        if result is not None:
                            result_msg, pub_response = result

                            # TODO: suppress all publishing errors and raise them after all publishers will be tried
                            for publisher in (pub_response, *handler._publishers):
                                if publisher is not None:
                                    async with AsyncExitStack() as pub_stack:
                                        result_to_send = result_msg

                                        for m_pub in all_middlewares:
                                            result_to_send = (
                                                await pub_stack.enter_async_context(
                                                    m_pub.publish_scope(result_msg)
                                                )
                                            )

                                        await publisher.publish(
                                            message=result_to_send,
                                            correlation_id=message.correlation_id,
                                        )

                    except StopConsume:
                        await self.close()
                        return None

                    except Exception as e:
                        if self.is_test:
                            raise e
                        else:
                            return None

                    else:
                        message.processed = processed = True
                        if IS_OPTIMIZED:  # pragma: no cover
                            break

            if processed is None:
                raise RuntimeError("You have to consume message")

        return result_msg

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError()

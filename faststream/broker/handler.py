from abc import abstractmethod
from contextlib import AsyncExitStack
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
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
from faststream.exceptions import HandlerException, StopConsume
from faststream.types import SendableMessage
from faststream.utils.context.main import context
from faststream.utils.functions import to_async


class BaseHandler(AsyncAPIOperation, Generic[MsgType]):
    """A base handler class for asynchronous API operations.

    Attributes:
        calls : List of tuples representing handler calls, filters, parsers, decoders, middlewares, and dependants.
        global_middlewares : Sequence of global middlewares.

    Methods:
        __init__ : Initializes the BaseHandler object.
        name : Returns the name of the handler.
        call_name : Returns the name of the handler call.
        description : Returns the description of the handler.
        consume : Abstract method to consume a message.

    Note: This class inherits from AsyncAPIOperation and is a generic class with type parameter MsgType.
    !!! note

        The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
    """

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

    def __init__(
        self,
        *,
        log_context_builder: Callable[[StreamMessage[Any]], Dict[str, str]],
        description: Optional[str] = None,
        title: Optional[str] = None,
    ):
        """Initialize a new instance of the class.

        Args:
            description: Optional description of the instance.
            title: Optional title of the instance.
        !!! note

            The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
        """
        self.calls = []  # type: ignore[assignment]
        self.global_middlewares = []
        # AsyncAPI information
        self._description = description
        self._title = title
        self.log_context_builder = log_context_builder

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
        """Consume a message.

        Args:
            msg: The message to be consumed.

        Returns:
            The sendable message.

        Raises:
            NotImplementedError: If the method is not implemented.
        !!! note

            The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
        """
        raise NotImplementedError()


class AsyncHandler(BaseHandler[MsgType]):
    """A class representing an asynchronous handler.

    Attributes:
        calls : a list of tuples containing the following information:
            - handler : the handler function
            - filter : a callable that filters the stream message
            - parser : an async parser for the message
            - decoder : an async decoder for the message
            - middlewares : a sequence of middlewares
            - dependant : a call model for the handler

    Methods:
        add_call : adds a new call to the list of calls
        consume : consumes a message and returns a sendable message
        start : starts the handler
        close : closes the handler
    !!! note

        The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
    """

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
        """Adds a call to the handler.

        Args:
            handler: The handler call wrapper.
            parser: The custom parser.
            decoder: The custom decoder.
            dependant: The call model.
            filter: The filter for stream messages.
            middlewares: Optional sequence of middlewares.

        Returns:
            None
        !!! note

            The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
        """
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
        """Consume a message asynchronously.

        Args:
            msg: The message to be consumed.

        Returns:
            The sendable message.

        Raises:
            StopConsume: If the consumption needs to be stopped.

        Raises:
            Exception: If an error occurs during consumption.
        !!! note

            The above docstring is autogenerated by docstring-gen library (https://docstring-gen.airt.ai)
        """
        result: Optional[WrappedReturn[SendableMessage]] = None
        result_msg: SendableMessage = None

        async with AsyncExitStack() as stack:
            gl_middlewares: List[BaseMiddleware] = []

            for m in self.global_middlewares:
                gl_middlewares.append(await stack.enter_async_context(m(msg)))

            logged = False
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

                if not logged:
                    log_context_tag = context.set_local(
                        "log_context", self.log_context_builder(message)
                    )

                message.decoded_body = await decoder(message)
                message.processed = processed

                if await filter_(message):
                    assert (  # nosec B101
                        not processed
                    ), "You can't proccess a message with multiple consumers"

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
                        handler.trigger()

                    except HandlerException as e:
                        handler.trigger()
                        raise e

                    except Exception as e:
                        handler.trigger(error=e)
                        raise e

                    else:
                        handler.trigger(result=result[0] if result else None)
                        message.processed = processed = True
                        if IS_OPTIMIZED:  # pragma: no cover
                            break

            assert processed, "You have to consume message"  # nosec B101

        context.reset_local("log_context", log_context_tag)
        return result_msg

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError()

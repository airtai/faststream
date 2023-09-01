import logging
from abc import abstractmethod
from functools import wraps
from types import TracebackType
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Sized,
    Tuple,
    Type,
    Union,
    cast,
)

import anyio
from fast_depends.core import CallModel
from fast_depends.dependencies import Depends

from faststream._compat import Self, override
from faststream.broker.core.abc import BrokerUsecase
from faststream.broker.handler import AsyncHandler
from faststream.broker.message import StreamMessage
from faststream.broker.middlewares import BaseMiddleware
from faststream.broker.push_back_watcher import BaseWatcher
from faststream.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    ConnectionType,
    CustomDecoder,
    CustomParser,
    Filter,
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.exceptions import AckMessage, NackMessage, RejectMessage, SkipMessage
from faststream.log import access_logger
from faststream.types import SendableMessage
from faststream.utils import context
from faststream.utils.functions import to_async


async def default_filter(msg: StreamMessage[Any]) -> bool:
    return not msg.processed


class BrokerAsyncUsecase(BrokerUsecase[MsgType, ConnectionType]):
    handlers: Dict[Any, AsyncHandler[MsgType]]  # type: ignore[assignment]
    middlewares: Sequence[Callable[[MsgType], BaseMiddleware]]
    _global_parser: Optional[AsyncCustomParser[MsgType]]
    _global_decoder: Optional[AsyncCustomDecoder[MsgType]]

    @abstractmethod
    async def start(self) -> None:
        super()._abc_start()
        for h in self.handlers.values():
            for c, _, _, _, _, _ in h.calls:
                c.event = anyio.Event()
        await self.connect()

    @abstractmethod
    async def _connect(self, **kwargs: Any) -> ConnectionType:
        raise NotImplementedError()

    @abstractmethod
    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None:
        super()._abc__close(exc_type, exc_val, exec_tb)

    async def close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None:
        super()._abc_close(exc_type, exc_val, exec_tb)

        for h in self.handlers.values():
            await h.close()

        if self._connection is not None:
            await self._close(exc_type, exc_val, exec_tb)

    @override
    @abstractmethod
    def _process_message(
        self,
        func: Callable[[StreamMessage[MsgType]], Awaitable[T_HandlerReturn]],
        watcher: BaseWatcher,
    ) -> Callable[[StreamMessage[MsgType]], Awaitable[WrappedReturn[T_HandlerReturn]],]:
        raise NotImplementedError()

    @abstractmethod
    async def publish(
        self,
        message: SendableMessage,
        *args: Any,
        reply_to: str = "",
        rpc: bool = False,
        rpc_timeout: Optional[float] = None,
        raise_timeout: bool = False,
        **kwargs: Any,
    ) -> Optional[SendableMessage]:
        raise NotImplementedError()

    @override
    @abstractmethod
    def subscriber(  # type: ignore[override,return]
        self,
        *broker_args: Any,
        retry: Union[bool, int] = False,
        dependencies: Sequence[Depends] = (),
        decoder: Optional[CustomDecoder[MsgType]] = None,
        parser: Optional[CustomParser[MsgType]] = None,
        middlewares: Optional[Sequence[Callable[[MsgType], BaseMiddleware]]] = None,
        filter: Filter[StreamMessage[MsgType]] = default_filter,
        _raw: bool = False,
        _get_dependant: Optional[Any] = None,
        **broker_kwargs: Any,
    ) -> Callable[
        [
            Union[
                Callable[P_HandlerParams, T_HandlerReturn],
                HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
            ]
        ],
        HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
    ]:
        super().subscriber()

    def __init__(
        self,
        *args: Any,
        apply_types: bool = True,
        logger: Optional[logging.Logger] = access_logger,
        log_level: int = logging.INFO,
        log_fmt: Optional[str] = "%(asctime)s %(levelname)s - %(message)s",
        dependencies: Sequence[Depends] = (),
        decoder: Optional[CustomDecoder[MsgType]] = None,
        parser: Optional[CustomParser[MsgType]] = None,
        middlewares: Optional[Sequence[Callable[[MsgType], BaseMiddleware]]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            *args,
            apply_types=apply_types,
            logger=logger,
            log_level=log_level,
            log_fmt=log_fmt,
            dependencies=dependencies,
            decoder=cast(
                Optional[AsyncCustomDecoder[MsgType]],
                to_async(decoder) if decoder else None,
            ),
            parser=cast(
                Optional[AsyncCustomParser[MsgType]],
                to_async(parser) if parser else None,
            ),
            middlewares=middlewares,
            **kwargs,
        )

    async def connect(self, *args: Any, **kwargs: Any) -> ConnectionType:
        if self._connection is None:
            _kwargs = self._resolve_connection_kwargs(*args, **kwargs)
            self._connection = await self._connect(**_kwargs)
        return self._connection

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exec_tb: Optional[TracebackType],
    ) -> None:
        await self.close(exc_type, exc_val, exec_tb)

    @override
    def _wrap_decode_message(
        self,
        func: Callable[..., Awaitable[T_HandlerReturn]],
        params: Sized = (),
        _raw: bool = False,
    ) -> Callable[[StreamMessage[MsgType]], Awaitable[T_HandlerReturn]]:
        params_ln = len(params)

        @wraps(func)
        async def decode_wrapper(message: StreamMessage[MsgType]) -> T_HandlerReturn:
            if _raw is True:
                return await func(message)

            msg = message.decoded_body

            if params_ln > 1:
                if isinstance(msg, Mapping):
                    return await func(**msg)
                elif isinstance(msg, Sequence):
                    return await func(*msg)
            elif params_ln == 1:
                return await func(msg)
            else:
                return await func()

            raise AssertionError("unreachable")

        return decode_wrapper

    @override
    def _wrap_handler(
        self,
        func: Callable[P_HandlerParams, T_HandlerReturn],
        *,
        retry: Union[bool, int] = False,
        extra_dependencies: Sequence[Depends] = (),
        _raw: bool = False,
        _get_dependant: Optional[Any] = None,
        **broker_log_context_kwargs: Any,
    ) -> Tuple[
        HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
        CallModel[P_HandlerParams, T_HandlerReturn],
    ]:
        return super()._wrap_handler(  # type: ignore[return-value]
            func,
            retry=retry,
            extra_dependencies=extra_dependencies,
            _raw=_raw,
            _get_dependant=_get_dependant,
            **broker_log_context_kwargs,
        )

    async def _execute_handler(
        self,
        func: Callable[[StreamMessage[MsgType]], Awaitable[T_HandlerReturn]],
        message: StreamMessage[MsgType],
    ) -> T_HandlerReturn:
        try:
            return await func(message)
        except AckMessage as e:
            await message.ack()
            raise e
        except NackMessage as e:
            await message.nack()
            raise e
        except RejectMessage as e:
            await message.reject()
            raise e

    @override
    def _log_execution(
        self,
        func: Callable[
            [StreamMessage[MsgType]],
            Awaitable[WrappedReturn[T_HandlerReturn]],
        ],
        **broker_args: Any,
    ) -> Callable[[StreamMessage[MsgType]], Awaitable[WrappedReturn[T_HandlerReturn]]]:
        @wraps(func)
        async def log_wrapper(
            message: StreamMessage[MsgType],
        ) -> WrappedReturn[T_HandlerReturn]:
            log_context = self._get_log_context(message=message, **broker_args)

            with context.scope("log_context", log_context):
                self._log("Received", extra=log_context)

                try:
                    r = await func(message)
                except SkipMessage as e:
                    self._log("Skipped", extra=log_context)
                    raise e
                except Exception as e:
                    self._log(f"{type(e).__name__}: {e}", logging.ERROR, exc_info=e)
                    raise e
                else:
                    self._log("Processed", extra=log_context)
                    return r

        return log_wrapper

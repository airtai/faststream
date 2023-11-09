from types import TracebackType
from typing import Any, Awaitable, Callable, Dict, Optional, Sequence, Type, Union

from aiobotocore.client import AioBaseClient
from fast_depends.dependencies import Depends

from faststream import BaseMiddleware
from faststream.broker.core.asyncronous import BrokerAsyncUsecase, default_filter
from faststream.broker.message import StreamMessage
from faststream.broker.publisher import BasePublisher
from faststream.broker.push_back_watcher import BaseWatcher
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
    WrappedReturn,
)
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.sqs.asyncapi import Handler, Publisher
from faststream.sqs.producer import SQSFastProducer
from faststream.sqs.shared.logging import SQSLoggingMixin
from faststream.types import AnyDict, SendableMessage


class SQSBroker(
    SQSLoggingMixin,
    BrokerAsyncUsecase[AnyDict, AioBaseClient],
):
    handlers: Dict[str, Handler]  # type: ignore[assignment]
    _publishers: Dict[str, Publisher]  # type: ignore[assignment]
    _producer: Optional[SQSFastProducer]

    async def start(self) -> None:
        pass

    async def _connect(self, **kwargs: Any) -> AioBaseClient:
        pass

    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None:
        pass

    def _process_message(
        self,
        func: Callable[[StreamMessage[MsgType]], Awaitable[T_HandlerReturn]],
        watcher: BaseWatcher,
    ) -> Callable[[StreamMessage[MsgType]], Awaitable[WrappedReturn[T_HandlerReturn]],]:
        pass

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
        pass

    def subscriber(
        self,
        *broker_args: Any,
        retry: Union[bool, int] = False,
        dependencies: Sequence[Depends] = (),
        decoder: Optional[CustomDecoder[StreamMessage[MsgType]]] = None,
        parser: Optional[CustomParser[MsgType, StreamMessage[MsgType]]] = None,
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
        pass

    def publisher(
        self, key: Any, publisher: BasePublisher[MsgType]
    ) -> BasePublisher[MsgType]:
        pass

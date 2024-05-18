import warnings
from abc import abstractmethod
from contextlib import asynccontextmanager
from functools import partial
from types import MethodType
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
)
from unittest.mock import AsyncMock, MagicMock

from faststream.broker.core.usecase import BrokerUsecase
from faststream.broker.message import StreamMessage, decode_message, encode_message
from faststream.broker.middlewares.logging import CriticalLogMiddleware
from faststream.broker.wrapper.call import HandlerCallWrapper
from faststream.testing.app import TestApp
from faststream.utils.ast import is_contains_context_name
from faststream.utils.functions import timeout_scope

if TYPE_CHECKING:
    from types import TracebackType

    from faststream.broker.subscriber.proto import SubscriberProto
    from faststream.broker.types import BrokerMiddleware


Broker = TypeVar("Broker", bound=BrokerUsecase[Any, Any])


class TestBroker(Generic[Broker]):
    """A class to represent a test broker."""

    # This is set so pytest ignores this class
    __test__ = False

    def __init__(
        self,
        broker: Broker,
        with_real: bool = False,
        connect_only: Optional[bool] = None,
    ) -> None:
        self.with_real = with_real
        self.broker = broker

        if connect_only is None:
            try:
                connect_only = is_contains_context_name(
                    self.__class__.__name__,
                    TestApp.__name__,
                )
            except Exception:  # pragma: no cover
                warnings.warn(
                    (
                        "\nError `{e!r}` occurred at `{self.__class__.__name__}` AST parsing."
                        "\n`connect_only` is set to `False` by default."
                    ),
                    category=RuntimeWarning,
                    stacklevel=1,
                )

                connect_only = False

        self.connect_only = connect_only

    async def __aenter__(self) -> Broker:
        middlewares = tuple(
            filter(
                lambda x: not isinstance(x, CriticalLogMiddleware),
                self.broker._middlewares,
            )
        )

        self.broker._middlewares = middlewares

        for sub in self.broker._subscribers.values():
            sub._broker_middlewares = middlewares

        for pub in self.broker._publishers.values():
            pub._broker_middlewares = middlewares

        self._ctx = self._create_ctx()
        return await self._ctx.__aenter__()

    async def __aexit__(self, *args: Any) -> None:
        await self._ctx.__aexit__(*args)

        middlewares: Tuple["BrokerMiddleware[Any]", ...] = (
            CriticalLogMiddleware(  # type: ignore[arg-type]
                logger=self.broker.logger,
                log_level=self.broker._msg_log_level,
            ),
            *self.broker._middlewares,
        )

        self.broker._middlewares = middlewares

        for sub in self.broker._subscribers.values():
            sub._broker_middlewares = middlewares

        for pub in self.broker._publishers.values():
            pub._broker_middlewares = middlewares

    @asynccontextmanager
    async def _create_ctx(self) -> AsyncGenerator[Broker, None]:
        if self.with_real:
            self._fake_start(self.broker)
        else:
            self._patch_test_broker(self.broker)

        async with self.broker:
            try:
                if not self.connect_only:
                    await self.broker.start()
                yield self.broker
            finally:
                self._fake_close(self.broker)

    @classmethod
    def _patch_test_broker(cls, broker: Broker) -> None:
        broker.start = AsyncMock(wraps=partial(cls._fake_start, broker))  # type: ignore[method-assign]
        broker._connect = MethodType(cls._fake_connect, broker)  # type: ignore[method-assign]
        broker.close = AsyncMock()  # type: ignore[method-assign]

    @classmethod
    def _fake_start(cls, broker: Broker, *args: Any, **kwargs: Any) -> None:
        broker.setup()

        patch_broker_calls(broker)

        for key, p in broker._publishers.items():
            if getattr(p, "_fake_handler", None):
                continue

            handler = broker._subscribers.get(key)

            if handler is not None:
                mock = MagicMock()
                p.set_test(mock=mock, with_fake=False)  # type: ignore[attr-defined]
                for h in handler.calls:
                    h.handler.set_test()
                    assert h.handler.mock  # nosec B101
                    h.handler.mock.side_effect = mock

            else:
                f = cls.create_publisher_fake_subscriber(broker, p)
                f.set_test()
                assert f.mock  # nosec B101
                p.set_test(mock=f.mock, with_fake=True)  # type: ignore[attr-defined]

        for handler in broker._subscribers.values():
            handler.running = True

    @classmethod
    def _fake_close(
        cls,
        broker: Broker,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> None:
        for p in broker._publishers.values():
            if getattr(p, "_fake_handler", None):
                p.reset_test()  # type: ignore[attr-defined]
                cls.remove_publisher_fake_subscriber(broker, p)

        for h in broker._subscribers.values():
            h.running = False
            for call in h.calls:
                call.handler.reset_test()

    @staticmethod
    @abstractmethod
    def create_publisher_fake_subscriber(
        broker: Broker, publisher: Any
    ) -> HandlerCallWrapper[Any, Any, Any]:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def remove_publisher_fake_subscriber(broker: Broker, publisher: Any) -> None:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    async def _fake_connect(broker: Broker, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()


def patch_broker_calls(broker: "BrokerUsecase[Any, Any]") -> None:
    """Patch broker calls."""
    broker._abc_start()

    for handler in broker._subscribers.values():
        for h in handler.calls:
            h.handler.set_test()


async def call_handler(
    handler: "SubscriberProto[Any]",
    message: Any,
    rpc: bool = False,
    rpc_timeout: Optional[float] = 30.0,
    raise_timeout: bool = False,
) -> Any:
    """Asynchronously call a handler function."""
    with timeout_scope(rpc_timeout, raise_timeout):
        result = await handler.consume(message)

        if rpc:
            message_body, content_type = encode_message(result)
            msg_to_publish = StreamMessage(
                raw_message=None, body=message_body, content_type=content_type
            )
            consumed_data = decode_message(msg_to_publish)
            return consumed_data

    return None

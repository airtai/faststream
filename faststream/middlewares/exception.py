from collections.abc import Awaitable
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    NoReturn,
    Optional,
    Union,
    cast,
    overload,
)

from typing_extensions import Literal, TypeAlias

from faststream._internal.middlewares import BaseMiddleware
from faststream._internal.utils import apply_types
from faststream._internal.utils.functions import sync_fake_context, to_async
from faststream.exceptions import IgnoredException

if TYPE_CHECKING:
    from contextlib import AbstractContextManager
    from types import TracebackType

    from faststream._internal.basic_types import AsyncFuncAny
    from faststream._internal.context.repository import ContextRepo
    from faststream.message import StreamMessage


GeneralExceptionHandler: TypeAlias = Union[
    Callable[..., None],
    Callable[..., Awaitable[None]],
]
PublishingExceptionHandler: TypeAlias = Callable[..., Any]

CastedGeneralExceptionHandler: TypeAlias = Callable[..., Awaitable[None]]
CastedPublishingExceptionHandler: TypeAlias = Callable[..., Awaitable[Any]]
CastedHandlers: TypeAlias = list[
    tuple[
        type[Exception],
        CastedGeneralExceptionHandler,
    ]
]
CastedPublishingHandlers: TypeAlias = list[
    tuple[
        type[Exception],
        CastedPublishingExceptionHandler,
    ]
]


class ExceptionMiddleware:
    __slots__ = ("_handlers", "_publish_handlers")

    _handlers: CastedHandlers
    _publish_handlers: CastedPublishingHandlers

    def __init__(
        self,
        handlers: Optional[
            dict[
                type[Exception],
                GeneralExceptionHandler,
            ]
        ] = None,
        publish_handlers: Optional[
            dict[
                type[Exception],
                PublishingExceptionHandler,
            ]
        ] = None,
    ) -> None:
        self._handlers: CastedHandlers = [
            (IgnoredException, ignore_handler),
            *(
                (
                    exc_type,
                    apply_types(
                        cast("Callable[..., Awaitable[None]]", to_async(handler)),
                    ),
                )
                for exc_type, handler in (handlers or {}).items()
            ),
        ]

        self._publish_handlers: CastedPublishingHandlers = [
            (IgnoredException, ignore_handler),
            *(
                (exc_type, apply_types(to_async(handler)))
                for exc_type, handler in (publish_handlers or {}).items()
            ),
        ]

    @overload
    def add_handler(
        self,
        exc: type[Exception],
        publish: Literal[False] = False,
    ) -> Callable[[GeneralExceptionHandler], GeneralExceptionHandler]: ...

    @overload
    def add_handler(
        self,
        exc: type[Exception],
        publish: Literal[True],
    ) -> Callable[[PublishingExceptionHandler], PublishingExceptionHandler]: ...

    def add_handler(
        self,
        exc: type[Exception],
        publish: bool = False,
    ) -> Union[
        Callable[[GeneralExceptionHandler], GeneralExceptionHandler],
        Callable[[PublishingExceptionHandler], PublishingExceptionHandler],
    ]:
        if publish:

            def pub_wrapper(
                func: PublishingExceptionHandler,
            ) -> PublishingExceptionHandler:
                self._publish_handlers.append(
                    (
                        exc,
                        apply_types(to_async(func)),
                    ),
                )
                return func

            return pub_wrapper

        def default_wrapper(
            func: GeneralExceptionHandler,
        ) -> GeneralExceptionHandler:
            self._handlers.append(
                (
                    exc,
                    apply_types(to_async(func)),
                ),
            )
            return func

        return default_wrapper

    def __call__(
        self,
        msg: Optional[Any],
        /,
        *,
        context: "ContextRepo",
    ) -> "_BaseExceptionMiddleware":
        """Real middleware runtime constructor."""
        return _BaseExceptionMiddleware(
            handlers=self._handlers,
            publish_handlers=self._publish_handlers,
            context=context,
            msg=msg,
        )


class _BaseExceptionMiddleware(BaseMiddleware):
    def __init__(
        self,
        *,
        handlers: CastedHandlers,
        publish_handlers: CastedPublishingHandlers,
        context: "ContextRepo",
        msg: Optional[Any],
    ) -> None:
        super().__init__(msg, context=context)
        self._handlers = handlers
        self._publish_handlers = publish_handlers

    async def consume_scope(
        self,
        call_next: "AsyncFuncAny",
        msg: "StreamMessage[Any]",
    ) -> Any:
        try:
            return await call_next(await self.on_consume(msg))

        except Exception as exc:
            exc_type = type(exc)

            for handler_type, handler in self._publish_handlers:
                if issubclass(exc_type, handler_type):
                    return await handler(exc, context__=self.context)

            raise

    async def after_processed(
        self,
        exc_type: Optional[type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exc_tb: Optional["TracebackType"] = None,
    ) -> Optional[bool]:
        if exc_type:
            for handler_type, handler in self._handlers:
                if issubclass(exc_type, handler_type):
                    # TODO: remove it after context will be moved to middleware
                    # In case parser/decoder error occurred
                    scope: AbstractContextManager[Any]
                    if not self.context.get_local("message"):
                        scope = self.context.scope("message", self.msg)
                    else:
                        scope = sync_fake_context()

                    with scope:
                        await handler(exc_val, context__=self.context)

                    return True

            return False

        return None


async def ignore_handler(
    exception: IgnoredException,
    **kwargs: Any,  # suppress context
) -> NoReturn:
    raise exception

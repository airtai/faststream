from functools import partial, wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Generic,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

from fast_depends import inject
from fast_depends.core import build_call_model
from pydantic import create_model

from faststream._compat import PYDANTIC_V2
from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.types import (
    CustomDecoder,
    CustomParser,
    Filter,
    MsgType,
    P_HandlerParams,
    T_HandlerReturn,
)
from faststream.types import F_Return, F_Spec
from faststream.utils.functions import to_async

if TYPE_CHECKING:
    from typing import Protocol, overload

    from fast_depends.core import CallModel
    from fast_depends.dependencies import Depends

    from faststream.broker.message import StreamMessage
    from faststream.broker.middlewares import BaseMiddleware

    class WrapperProtocol(Generic[MsgType], Protocol):
        """Annotation class to represent @subsriber return type."""

        @overload
        def __call__(
            self,
            func: None = None,
            *,
            filter: Filter["StreamMessage[MsgType]"],
            parser: CustomParser[MsgType, Any],
            decoder: CustomDecoder["StreamMessage[MsgType]"],
            middlewares: Sequence["BaseMiddleware"] = (),
            dependencies: Sequence["Depends"] = (),
        ) -> Callable[
            [Callable[P_HandlerParams, T_HandlerReturn]],
            HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
        ]:
            ...

        @overload
        def __call__(
            self,
            func: Callable[P_HandlerParams, T_HandlerReturn],
            *,
            filter: Filter["StreamMessage[MsgType]"],
            parser: CustomParser[MsgType, Any],
            decoder: CustomDecoder["StreamMessage[MsgType]"],
            middlewares: Sequence["BaseMiddleware"] = (),
            dependencies: Sequence["Depends"] = (),
        ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
            ...

        def __call__(
            self,
            func: Optional[Callable[P_HandlerParams, T_HandlerReturn]] = None,
            *,
            filter: Filter["StreamMessage[MsgType]"],
            parser: CustomParser[MsgType, Any],
            decoder: CustomDecoder["StreamMessage[MsgType]"],
            middlewares: Sequence["BaseMiddleware"] = (),
            dependencies: Sequence["Depends"] = (),
        ) -> Union[
            HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
            Callable[
                [Callable[P_HandlerParams, T_HandlerReturn]],
                HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
            ],
        ]:
            ...


class WrapHandlerMixin(Generic[MsgType]):
    """A class to patch original handle function."""

    def wrap_handler(
        self,
        *,
        func: Callable[P_HandlerParams, T_HandlerReturn],
        dependencies: Sequence["Depends"],
        apply_types: bool,
        is_validate: bool,
        raw: bool = False,
        get_dependant: Optional[Any] = None,
    ) -> Tuple[
        HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
        "CallModel[P_HandlerParams, T_HandlerReturn]",
    ]:
        build_dep = build_dep = cast(
            Callable[
                [Callable[F_Spec, F_Return]],
                "CallModel[F_Spec, F_Return]",
            ],
            get_dependant
            or partial(
                build_call_model,
                cast=is_validate,
                extra_dependencies=dependencies,
            ),
        )

        if isinstance(func, HandlerCallWrapper):
            handler_call, func = func, func._original_call
            if handler_call._wrapped_call is not None:
                return handler_call, build_dep(func)

        else:
            handler_call = HandlerCallWrapper(func)

        f = to_async(func)
        dependant = build_dep(f)

        if getattr(dependant, "flat_params", None) is None:  # FastAPI case
            extra = [build_dep(d.dependency) for d in dependencies]
            dependant.dependencies.extend(extra)
            dependant = _patch_fastapi_dependant(dependant)

        else:
            if apply_types and not raw:
                f = inject(None)(f, dependant)

            if not raw:
                f = self._wrap_decode_message(
                    func=f,
                    params_ln=len(dependant.flat_params),
                )

        handler_call.set_wrapped(f)
        return handler_call, dependant

    def _wrap_decode_message(
        self,
        func: Callable[..., Awaitable[T_HandlerReturn]],
        params_ln: int,
    ) -> Callable[
        ["StreamMessage[MsgType]"],
        Awaitable[T_HandlerReturn],
    ]:
        """Wraps a function to decode a message and pass it as an argument to the wrapped function.

        Args:
            func: The function to be wrapped.
            params_ln: The parameters number to be passed to the wrapped function.

        Returns:
            The wrapped function.
        """

        @wraps(func)
        async def decode_wrapper(message: "StreamMessage[MsgType]") -> T_HandlerReturn:
            """A wrapper function to decode and handle a message.

            Args:
                message : The message to be decoded and handled

            Returns:
                The return value of the handler function
            """
            msg = message.decoded_body

            if params_ln > 1:
                if isinstance(msg, Mapping):
                    return await func(**msg)
                elif isinstance(msg, Sequence):
                    return await func(*msg)
            else:
                return await func(msg)

            raise AssertionError("unreachable")

        return decode_wrapper


def _patch_fastapi_dependant(
    dependant: "CallModel[P_HandlerParams, Awaitable[T_HandlerReturn]]",
) -> "CallModel[P_HandlerParams, Awaitable[T_HandlerReturn]]":
    """Patch FastAPI dependant.

    Args:
        dependant: The dependant to be patched.

    Returns:
        The patched dependant.
    """
    params = dependant.query_params + dependant.body_params  # type: ignore[attr-defined]

    for d in dependant.dependencies:
        params.extend(d.query_params + d.body_params)  # type: ignore[attr-defined]

    params_unique = {}
    params_names = set()
    for p in params:
        if p.name not in params_names:
            params_names.add(p.name)
            info = p.field_info if PYDANTIC_V2 else p
            params_unique[p.name] = (info.annotation, info.default)

    dependant.model = create_model(  # type: ignore[call-overload]
        getattr(dependant.call.__name__, "__name__", type(dependant.call).__name__),
        **params_unique,
    )
    dependant.custom_fields = {}
    dependant.flat_params = params_unique  # type: ignore[assignment,misc]

    return dependant

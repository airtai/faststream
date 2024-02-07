from functools import partial, wraps
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Generic,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

from fast_depends.core import CallModel, build_call_model
from fast_depends.use import _InjectWrapper, inject
from typing_extensions import Annotated, Doc

from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.types import MsgType, P_HandlerParams, T_HandlerReturn
from faststream.utils.functions import to_async

if TYPE_CHECKING:
    from typing import Protocol, overload

    from fast_depends.dependencies import Depends
    from typing_extensions import TypedDict

    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        CustomDecoder,
        CustomParser,
        Filter,
        SubscriberMiddleware,
    )

    class WrapExtraKwargs(TypedDict):
        """Class to annotate `wrap_handler` method extra options using `typing_extensions.Unpack`."""

        apply_types: Annotated[
            bool,
            Doc("Flag to wrap original function to FastDepends"),
        ]
        is_validate: Annotated[
            bool,
            Doc(
                "Flag to use pydantic to serialize incoming message body."
                "Passing as `cast` option to FastDepends"
            ),
        ]
        get_dependant: Annotated[
            Optional[Any],
            Doc("Function to build dependant object. Using FastDepends as default.")
        ]

    class WrapperProtocol(Protocol[MsgType]):
        """Annotation class to represent @subsriber return type."""

        @overload
        def __call__(
            self,
            func: None = None,
            *,
            filter: Optional["Filter[StreamMessage[MsgType]]"] = None,
            parser: Optional["CustomParser[MsgType]"] = None,
            decoder: Optional["CustomDecoder[StreamMessage[MsgType]]"] = None,
            middlewares: Iterable["SubscriberMiddleware"] = (),
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
            filter: Optional[Filter[StreamMessage[MsgType]]] = None,
            parser: Optional[CustomParser[MsgType]] = None,
            decoder: Optional[CustomDecoder[StreamMessage[MsgType]]] = None,
            middlewares: Iterable[SubscriberMiddleware] = (),
            dependencies: Sequence[Depends] = (),
        ) -> HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn]:
            ...

        def __call__(
            self,
            func: Optional[Callable[P_HandlerParams, T_HandlerReturn]] = None,
            *,
            filter: Optional[Filter[StreamMessage[MsgType]]] = None,
            parser: Optional[CustomParser[MsgType]] = None,
            decoder: Optional[CustomDecoder[StreamMessage[MsgType]]] = None,
            middlewares: Iterable[SubscriberMiddleware] = (),
            dependencies: Sequence[Depends] = (),
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
        func: Union[
            Callable[P_HandlerParams, T_HandlerReturn],
            HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
        ],
        dependencies: Sequence["Depends"],
        apply_types: Annotated[
            bool,
            Doc("Flag to wrap original function to FastDepends"),
        ],
        is_validate: Annotated[
            bool,
            Doc(
                "Flag to use pydantic to serialize incoming message body."
                "Passing as `cast` option to FastDepends"
            ),
        ],
        get_dependant: Annotated[
            Optional[Any],
            Doc("Function to build dependant object. Using FastDepends as default.")
        ],
    ) -> Tuple[
        HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn],
        "CallModel[..., Any]",
    ]:
        build_dep = cast(
            Callable[
                [Callable[..., Any]],
                "CallModel[..., Any]",
            ],
            get_dependant
            or partial(
                build_call_model,
                cast=is_validate,
                extra_dependencies=dependencies,
            ),
        )

        if isinstance(func, HandlerCallWrapper):
            handler_call = cast(HandlerCallWrapper[MsgType, P_HandlerParams, T_HandlerReturn], func)
            func = handler_call._original_call

            if handler_call._wrapped_call is not None:
                return handler_call, build_dep(func)

        else:
            handler_call = HandlerCallWrapper[
                MsgType, P_HandlerParams, T_HandlerReturn
            ](func)

        f: Callable[..., Awaitable[T_HandlerReturn]] = to_async(func)
        dependant = build_dep(f)

        if isinstance(dependant, CallModel):  # not custom (FastAPI) case
            if apply_types:
                wrapper: _InjectWrapper[Any, Any] = inject(func=None)
                f = wrapper(func=f, model=dependant)

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

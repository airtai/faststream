from typing import Any, Callable, Iterable, TYPE_CHECKING

from nats.aio.msg import Msg
from typing_extensions import override, Annotated, Doc

from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.fastapi.router import StreamRouter
from faststream.broker.types import P_HandlerParams, T_HandlerReturn
from faststream.nats.broker import NatsBroker

if TYPE_CHECKING:
    from fastapi import params


class NatsRouter(StreamRouter[Msg]):
    """A class to represent a NATS router."""

    broker_class = NatsBroker

    def subscriber(  # type: ignore[override]
        self,
        subject: str,
        *args: Any,
        dependencies: Annotated[
            Iterable["params.Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to the subscriber."),
        ] = (),
        **__service_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Msg, P_HandlerParams, T_HandlerReturn],
    ]:
        return super().subscriber(
            subject,
            subject,
            *args,
            dependencies=dependencies,
            **__service_kwargs,
        )

    @override
    @staticmethod
    def _setup_log_context(  # type: ignore[override]
        main_broker: NatsBroker,
        including_broker: NatsBroker,
    ) -> None:
        for h in including_broker.handlers.values():
            main_broker._setup_log_context(
                queue=h.queue,
                subject=h.subject,
                stream=h.stream.name if h.stream else None,
            )

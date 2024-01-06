from typing import Any, Callable, Sequence

from nats.aio.msg import Msg
from typing_extensions import override

from faststream.broker.router import BrokerRoute as NatsRoute
from faststream.broker.router import BrokerRouter
from faststream.broker.types import P_HandlerParams, T_HandlerReturn
from faststream.broker.wrapper import HandlerCallWrapper
from faststream.types import SendableMessage

__all__ = (
    "NatsRouter",
    "NatsRoute",
)


class NatsRouter(BrokerRouter[str, Msg]):
    """A class to represent a NATS router."""

    def __init__(
        self,
        prefix: str = "",
        handlers: Sequence[NatsRoute[Msg, SendableMessage]] = (),
        **kwargs: Any,
    ) -> None:
        """Initialize the NATS router.

        Args:
            prefix: The prefix.
            handlers: The handlers.
            **kwargs: The keyword arguments.
        """
        for h in handlers:
            if not (subj := h.kwargs.pop("subject", None)):
                subj, h.args = h.args[0], h.args[1:]
            h.args = (prefix + subj, *h.args)
        super().__init__(prefix, handlers, **kwargs)

    @override
    def subscriber(  # type: ignore[override]
        self,
        subject: str,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[Msg, P_HandlerParams, T_HandlerReturn],
    ]:
        return self._wrap_subscriber(
            self.prefix + subject,
            **broker_kwargs,
        )

from typing import Any, Callable, Dict, Iterable, Optional, Sequence

from nats.aio.msg import Msg
from typing_extensions import override

from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.router import BrokerRoute as NatsRoute
from faststream.broker.router import BrokerRouter
from faststream.broker.types import (
    P_HandlerParams,
    PublisherMiddleware,
    T_HandlerReturn,
)
from faststream.nats.asyncapi import Publisher
from faststream.types import SendableMessage


class NatsRouter(BrokerRouter[str, Msg]):
    """A class to represent a NATS router."""

    _publishers: Dict[str, Publisher]

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

    @override
    @staticmethod
    def _get_publisher_key(publisher: Publisher) -> str:  # type: ignore[override]
        return publisher.subject

    @override
    @staticmethod
    def _update_publisher_prefix(  # type: ignore[override]
        prefix: str,
        publisher: Publisher,
    ) -> Publisher:
        publisher.subject = prefix + publisher.subject
        return publisher

    @override
    def publisher(  # type: ignore[override]
        self,
        subject: str,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        middlewares: Iterable["PublisherMiddleware"] = (),
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
    ) -> Publisher:
        new_publisher = self._update_publisher_prefix(
            self.prefix,
            Publisher(
                subject=subject,
                reply_to=reply_to,
                headers=headers,
                title=title,
                _description=description,
                _schema=schema,
                middlewares=middlewares,
                include_in_schema=(
                    include_in_schema
                    if self.include_in_schema is None
                    else self.include_in_schema
                ),
            ),
        )
        publisher_key = self._get_publisher_key(new_publisher)
        publisher = self._publishers[publisher_key] = self._publishers.get(
            publisher_key, new_publisher
        )
        return publisher

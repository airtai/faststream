from functools import partial
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Optional,
    Union,
)

from nats.aio.msg import Msg
from typing_extensions import Annotated, Doc, override

from faststream._internal.publisher.usecase import PublisherUsecase
from faststream._internal.subscriber.utils import process_msg
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.message import gen_cor_id

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict, AsyncFunc, SendableMessage
    from faststream._internal.types import BrokerMiddleware, PublisherMiddleware
    from faststream.nats.message import NatsMessage
    from faststream.nats.publisher.producer import NatsFastProducer, NatsJSFastProducer
    from faststream.nats.schemas import JStream


class LogicPublisher(PublisherUsecase[Msg]):
    """A class to represent a NATS publisher."""

    _producer: Union["NatsFastProducer", "NatsJSFastProducer", None]

    def __init__(
        self,
        *,
        subject: str,
        reply_to: str,
        headers: Optional[Dict[str, str]],
        stream: Optional["JStream"],
        timeout: Optional[float],
        # Publisher args
        broker_middlewares: Iterable["BrokerMiddleware[Msg]"],
        middlewares: Iterable["PublisherMiddleware"],
        # AsyncAPI args
        schema_: Optional[Any],
        title_: Optional[str],
        description_: Optional[str],
        include_in_schema: bool,
    ) -> None:
        """Initialize NATS publisher object."""
        super().__init__(
            broker_middlewares=broker_middlewares,
            middlewares=middlewares,
            # AsyncAPI args
            schema_=schema_,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

        self.subject = subject
        self.stream = stream
        self.timeout = timeout
        self.headers = headers
        self.reply_to = reply_to

    def __hash__(self) -> int:
        return hash(self.subject)

    @override
    async def publish(
        self,
        message: "SendableMessage",
        subject: str = "",
        *,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        correlation_id: Optional[str] = None,
        stream: Optional[str] = None,
        timeout: Optional[float] = None,
        # publisher specific
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
    ) -> None:
        """Publish message directly.

        Args:
            message (SendableMessage): Message body to send.
                Can be any encodable object (native python types or `pydantic.BaseModel`).
            subject (str): NATS subject to send message (default is `''`).
            headers (:obj:`dict` of :obj:`str`: :obj:`str`, optional): Message headers to store metainformation (default is `None`).
                **content-type** and **correlation_id** will be set automatically by framework anyway.

            reply_to (str): NATS subject name to send response (default is `None`).
            correlation_id (str, optional): Manual message **correlation_id** setter (default is `None`).
                **correlation_id** is a useful option to trace messages.

            stream (str, optional): This option validates that the target subject is in presented stream (default is `None`).
                Can be omitted without any effect.
            timeout (float, optional): Timeout to send message to NATS in seconds (default is `None`).

            _extra_middlewares (:obj:`Iterable` of :obj:`PublisherMiddleware`): Extra middlewares to wrap publishing process (default is `()`).
        """
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        kwargs: AnyDict = {
            "subject": subject or self.subject,
            "headers": headers or self.headers,
            "reply_to": reply_to or self.reply_to,
            "correlation_id": correlation_id or gen_cor_id(),
        }

        if stream := stream or getattr(self.stream, "name", None):
            kwargs.update({"stream": stream, "timeout": timeout or self.timeout})

        call: AsyncFunc = self._producer.publish

        for m in chain(
            (
                _extra_middlewares
                or (m(None).publish_scope for m in self._broker_middlewares)
            ),
            self._middlewares,
        ):
            call = partial(m, call)

        return await call(message, **kwargs)

    @override
    async def request(
        self,
        message: Annotated[
            "SendableMessage",
            Doc(
                "Message body to send. "
                "Can be any encodable object (native python types or `pydantic.BaseModel`)."
            ),
        ],
        subject: Annotated[
            str,
            Doc("NATS subject to send message."),
        ] = "",
        *,
        headers: Annotated[
            Optional[Dict[str, str]],
            Doc(
                "Message headers to store metainformation. "
                "**content-type** and **correlation_id** will be set automatically by framework anyway."
            ),
        ] = None,
        correlation_id: Annotated[
            Optional[str],
            Doc(
                "Manual message **correlation_id** setter. "
                "**correlation_id** is a useful option to trace messages."
            ),
        ] = None,
        timeout: Annotated[
            float,
            Doc("Timeout to send message to NATS."),
        ] = 0.5,
        # publisher specific
        _extra_middlewares: Annotated[
            Iterable["PublisherMiddleware"],
            Doc("Extra middlewares to wrap publishing process."),
        ] = (),
    ) -> "NatsMessage":
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        kwargs: AnyDict = {
            "subject": subject or self.subject,
            "headers": headers or self.headers,
            "timeout": timeout or self.timeout,
            "correlation_id": correlation_id or gen_cor_id(),
        }

        request: AsyncFunc = self._producer.request

        for pub_m in chain(
            (
                _extra_middlewares
                or (m(None).publish_scope for m in self._broker_middlewares)
            ),
            self._middlewares,
        ):
            request = partial(pub_m, request)

        published_msg = await request(
            message,
            **kwargs,
        )

        msg: NatsMessage = await process_msg(
            msg=published_msg,
            middlewares=self._broker_middlewares,
            parser=self._producer._parser,
            decoder=self._producer._decoder,
        )
        return msg

    def add_prefix(self, prefix: str) -> None:
        self.subject = prefix + self.subject

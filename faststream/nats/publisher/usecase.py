from functools import partial
from itertools import chain
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Union

from nats.aio.msg import Msg
from typing_extensions import override

from faststream.broker.message import gen_cor_id
from faststream.broker.publisher.usecase import PublisherUsecase
from faststream.exceptions import NOT_CONNECTED_YET

if TYPE_CHECKING:
    from faststream.broker.types import BrokerMiddleware, PublisherMiddleware
    from faststream.nats.publisher.producer import NatsFastProducer, NatsJSFastProducer
    from faststream.nats.schemas import JStream
    from faststream.types import AnyDict, AsyncFunc, SendableMessage


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
        rpc: bool = False,
        rpc_timeout: Optional[float] = 30.0,
        raise_timeout: bool = False,
        # publisher specific
        _extra_middlewares: Iterable["PublisherMiddleware"] = (),
    ) -> Optional[Any]:
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
            rpc (bool): Whether to wait for reply in blocking mode (default is `False`).
            rpc_timeout (float, optional): RPC reply waiting time (default is `30.0`).
            raise_timeout (bool): Whetever to raise `TimeoutError` or return `None` at **rpc_timeout** (default is `False`).
                RPC request returns `None` at timeout by default.

            _extra_middlewares (:obj:`Iterable` of :obj:`PublisherMiddleware`): Extra middlewares to wrap publishing process (default is `()`).
        """
        assert self._producer, NOT_CONNECTED_YET  # nosec B101

        kwargs: AnyDict = {
            "subject": subject or self.subject,
            "headers": headers or self.headers,
            "reply_to": reply_to or self.reply_to,
            "correlation_id": correlation_id or gen_cor_id(),
            # specific args
            "rpc": rpc,
            "rpc_timeout": rpc_timeout,
            "raise_timeout": raise_timeout,
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

    def add_prefix(self, prefix: str) -> None:
        self.subject = prefix + self.subject

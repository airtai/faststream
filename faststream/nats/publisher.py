from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Union

from nats.aio.msg import Msg
from typing_extensions import Annotated, Doc, override

from faststream.broker.core.publisher import BasePublisher
from faststream.exceptions import NOT_CONNECTED_YET
from faststream.nats.producer import NatsFastProducer, NatsJSFastProducer
from faststream.nats.schemas import JStream
from faststream.types import AnyDict, DecodedMessage, SendableMessage

if TYPE_CHECKING:
    from faststream.broker.types import PublisherMiddleware


@dataclass
class LogicPublisher(BasePublisher[Msg]):
    """A class to represent a NATS publisher."""

    subject: str
    reply_to: str
    headers: Optional[Dict[str, str]]
    stream: Optional[JStream]
    timeout: Optional[float]

    _producer: Union[NatsFastProducer, NatsJSFastProducer, None]

    def __init__(
        self,
        *,
        subject: Annotated[
            str,
            Doc("NATS subject to publish messages."),
        ],
        reply_to: Annotated[
            str,
            Doc("NATS subject to send publishing message response."),
        ],
        headers: Annotated[
            Optional[Dict[str, str]],
            Doc(
                "Publishing message default headers."
                "Can be overrided by `publish.headers` if specified"
            ),
        ],
        stream: Annotated[
            Optional[JStream],
            Doc("Validate `subject` is in specified stream or not."),
        ],
        timeout: Annotated[
            Optional[float],
            Doc("Message publish timeout."),
        ],
        # Regular publisher options
        middlewares: Annotated[
            Iterable["PublisherMiddleware"],
            Doc("Publisher middlewares."),
        ],
        # AsyncAPI options
        schema_: Annotated[
            Optional[Any],
            Doc(
                "AsyncAPI publishing message type"
                "Should be any python-native object annotation or `pydantic.BaseModel`."
            ),
        ],
        title_: Annotated[
            Optional[str],
            Doc("AsyncAPI object title."),
        ],
        description_: Annotated[
            Optional[str],
            Doc("AsyncAPI object description."),
        ],
        include_in_schema: Annotated[
            bool,
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ],
    ) -> None:
        """Initialize NATS publisher object."""
        super().__init__(
            middlewares=middlewares,
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

        self._producer = None

    @override
    async def _publish(  # type: ignore[override]
        self,
        message: SendableMessage = "",
        **producer_kwargs: Any,
    ) -> Optional[DecodedMessage]:
        assert self._producer, NOT_CONNECTED_YET  # nosec B101
        assert self.subject, "You have to specify outgoing subject"  # nosec B101

        return await self._producer.publish(
            message=message,
            **producer_kwargs,
        )

    @cached_property
    def publish_kwargs(self) -> AnyDict:  # type: ignore[overide]
        kwargs = {
            "subject": self.subject,
            "reply_to": self.reply_to,
            "headers": self.headers,
        }

        if self.stream is not None:
            kwargs.update(
                {
                    "stream": self.stream.name,
                    "timeout": self.timeout,
                }
            )

        return kwargs

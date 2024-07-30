from typing import TYPE_CHECKING, Optional

from typing_extensions import override

from faststream.broker.response import Response

if TYPE_CHECKING:
    from aio_pika.abc import DateType, TimeoutType

    from faststream.rabbit.types import AioPikaSendableMessage
    from faststream.types import AnyDict


class RabbitResponse(Response):
    def __init__(
        self,
        body: "AioPikaSendableMessage",
        *,
        headers: Optional["AnyDict"] = None,
        correlation_id: Optional[str] = None,
        message_id: Optional[str] = None,
        mandatory: bool = True,
        immediate: bool = False,
        timeout: "TimeoutType" = None,
        persist: Optional[bool] = None,
        priority: Optional[int] = None,
        message_type: Optional[str] = None,
        content_type: Optional[str] = None,
        expiration: Optional["DateType"] = None,
        content_encoding: Optional[str] = None,
    ) -> None:
        super().__init__(
            body=body,
            headers=headers,
            correlation_id=correlation_id,
        )

        self.message_id = message_id
        self.mandatory = mandatory
        self.immediate = immediate
        self.timeout = timeout
        self.persist = persist
        self.priority = priority
        self.message_type = message_type
        self.content_type = content_type
        self.expiration = expiration
        self.content_encoding = content_encoding

    @override
    def as_publish_kwargs(self) -> "AnyDict":
        publish_options = {
            **super().as_publish_kwargs(),
            "message_id": self.message_id,
            "mandatory": self.mandatory,
            "immediate": self.immediate,
            "timeout": self.timeout,
            "persist": self.persist,
            "priority": self.priority,
            "message_type": self.message_type,
            "content_type": self.content_type,
            "expiration": self.expiration,
            "content_encoding": self.content_encoding,
        }
        return publish_options

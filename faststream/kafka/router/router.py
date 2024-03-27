from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional

from typing_extensions import Annotated, Doc, override

from faststream.broker.core.call_wrapper import HandlerCallWrapper
from faststream.broker.router import BrokerRoute, BrokerRouter
from faststream.broker.types import P_HandlerParams, T_HandlerReturn
from faststream.kafka.asyncapi import Publisher

if TYPE_CHECKING:
    from aiokafka import ConsumerRecord
    from fast_depends.dependencies import Depends

    from faststream.broker.message import StreamMessage
    from faststream.broker.types import (
        BrokerMiddleware,
        CustomDecoder,
        CustomParser,
    )


class KafkaRouter(BrokerRouter["ConsumerRecord"]):
    """A class to represent a Kafka router."""

    _publishers: Dict[int, Publisher]  # type: ignore[assignment]

    def __init__(
        self,
        prefix: Annotated[
            str,
            Doc("String prefix to add to all subscribers topics."),
        ] = "",
        handlers: Annotated[
            Iterable[BrokerRoute],
            Doc("Route object to include."),
        ] = (),
        *,
        dependencies: Annotated[
            Iterable["Depends"],
            Doc("Dependencies list (`[Depends(),]`) to apply to all routers' publishers/subscribers."),
        ] = (),
        middlewares: Annotated[
            Iterable["BrokerMiddleware[ConsumerRecord]"],
            Doc("Router middlewares to apply to all routers' publishers/subscribers."),
        ] = (),
        parser: Annotated[
            Optional["CustomParser[ConsumerRecord]"],
            Doc(
                "Parser to map original nats-py **Msg** to FastStream one."
            ),
        ] = None,
        decoder: Annotated[
            Optional["CustomDecoder[StreamMessage[ConsumerRecord]]"],
            Doc("Function to decode FastStream msg bytes body to python objects."),
        ] = None,
        include_in_schema: Annotated[
            Optional[bool],
            Doc("Whetever to include operation in AsyncAPI schema or not."),
        ] = None,
    ) -> None:
        for h in handlers:
            h.args = tuple(prefix + x for x in h.args)
        super().__init__(prefix, handlers, dependencies=dependencies, middlewares=middlewares,
                         parser=parser, decoder=decoder, include_in_schema=include_in_schema,)

    def subscriber(
        self,
        *topics: str,
        **broker_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper["ConsumerRecord", P_HandlerParams, T_HandlerReturn],
    ]:
        """A function to subscribe to topics.

        Args:
            *topics : variable number of topic names
            **broker_kwargs : keyword arguments for the broker

        Returns:
            A callable function that wraps the handler function
        """
        return self._wrap_subscriber(
            *(self.prefix + x for x in topics),
            **broker_kwargs,
        )

    @override
    def publisher(  # type: ignore[override]
        self,
        topic: str,
        key: Optional[bytes] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        reply_to: str = "",
        batch: bool = False,
        # publisher-specfic
        middlewares: Iterable = (),
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Any] = None,
        include_in_schema: bool = True,
    ) -> Publisher:
        """Publishes a message to a topic.

        Args:
            topic (str): The topic to publish the message to.
            key (bytes, optional): The key associated with the message.
            partition (int, optional): The partition to publish the message to.
            timestamp_ms (int, optional): The timestamp of the message in milliseconds.
            headers (Dict[str, str], optional): Additional headers for the message.
            reply_to (str, optional): The topic to reply to.
            batch (bool, optional): Whether to publish the message as part of a batch.
            title (str, optional): The title of the message.
            description (str, optional): The description of the message.
            schema (Any, optional): The schema of the message.
            include_in_schema (bool, optional): Whether to include the message in the API specification.

        Returns:
            Publisher: The publisher object used to publish the message.
        """
        new_publisher = self._update_publisher_prefix(
            self.prefix,
            Publisher.create(
                topic=topic,
                key=key,
                partition=partition,
                timestamp_ms=timestamp_ms,
                headers=headers,
                reply_to=reply_to,
                batch=batch,
                # publisher-specific
                middlewares=(
                    *(m(None).publish_scope for m in self._middlewares),
                    *middlewares
                ),
                # AsyncAPI
                title_=title,
                schema_=schema,
                description_=description,
                include_in_schema=(
                    include_in_schema
                    if self.include_in_schema is None
                    else self.include_in_schema
                ),
                # delay
                client_id="",
            ),
        )
        publisher_key = hash(new_publisher)
        publisher = self._publishers[publisher_key] = self._publishers.get(
            publisher_key, new_publisher
        )
        return publisher

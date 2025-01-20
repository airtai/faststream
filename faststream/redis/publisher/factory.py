from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional, Union

from typing_extensions import TypeAlias

from faststream._internal.publisher.schemas import (
    PublisherUsecaseOptions,
)
from faststream.exceptions import SetupError
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub
from faststream.redis.schemas.proto import validate_options
from faststream.redis.schemas.publishers import RedisPublisherBaseOptions
from faststream.specification.schema.base import SpecificationOptions

from .specified import (
    SpecificationChannelPublisher,
    SpecificationListBatchPublisher,
    SpecificationListPublisher,
    SpecificationStreamPublisher,
)

if TYPE_CHECKING:
    from faststream._internal.basic_types import AnyDict
    from faststream._internal.types import BrokerMiddleware, PublisherMiddleware
    from faststream.redis.message import UnifyRedisDict


PublisherType: TypeAlias = Union[
    SpecificationChannelPublisher,
    SpecificationStreamPublisher,
    SpecificationListPublisher,
    SpecificationListBatchPublisher,
]


def create_publisher(
    *,
    channel: Union["PubSub", str, None],
    list: Union["ListSub", str, None],
    stream: Union["StreamSub", str, None],
    headers: Optional["AnyDict"],
    reply_to: str,
    broker_middlewares: Sequence["BrokerMiddleware[UnifyRedisDict]"],
    middlewares: Sequence["PublisherMiddleware"],
    # AsyncAPI args
    title_: Optional[str],
    description_: Optional[str],
    schema_: Optional[Any],
    include_in_schema: bool,
) -> PublisherType:
    validate_options(channel=channel, list=list, stream=stream)

    internal_options = PublisherUsecaseOptions(
        broker_middlewares=broker_middlewares, middlewares=middlewares
    )

    base_options = RedisPublisherBaseOptions(
        reply_to=reply_to, headers=headers, internal_options=internal_options
    )

    specification_options = SpecificationOptions(
        title_=title_,
        description_=description_,
        include_in_schema=include_in_schema,
    )

    if (channel := PubSub.validate(channel)) is not None:
        return SpecificationChannelPublisher(
            channel=channel,
            base_options=base_options,
            specification_options=specification_options,
            schema_=schema_,
        )

    if (stream := StreamSub.validate(stream)) is not None:
        return SpecificationStreamPublisher(
            stream=stream,
            base_options=base_options,
            specification_options=specification_options,
            schema_=schema_,
        )

    if (list := ListSub.validate(list)) is not None:
        if list.batch:
            return SpecificationListBatchPublisher(
                list=list,
                base_options=base_options,
                specification_options=specification_options,
                schema_=schema_,
            )
        return SpecificationListPublisher(
            list=list,
            base_options=base_options,
            specification_options=specification_options,
            schema_=schema_,
        )

    raise SetupError(INCORRECT_SETUP_MSG)

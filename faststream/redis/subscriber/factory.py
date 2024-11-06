import warnings
from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional, Union

from typing_extensions import TypeAlias

from faststream._internal.constants import EMPTY
from faststream.exceptions import SetupError
from faststream.middlewares import AckPolicy
from faststream.redis.schemas import INCORRECT_SETUP_MSG, ListSub, PubSub, StreamSub
from faststream.redis.schemas.proto import validate_options
from faststream.redis.subscriber.specified import (
    SpecificationChannelSubscriber,
    SpecificationListBatchSubscriber,
    SpecificationListSubscriber,
    SpecificationStreamBatchSubscriber,
    SpecificationStreamSubscriber,
)

if TYPE_CHECKING:
    from fast_depends.dependencies import Dependant

    from faststream._internal.types import BrokerMiddleware
    from faststream.redis.message import UnifyRedisDict

SubsciberType: TypeAlias = Union[
    "SpecificationChannelSubscriber",
    "SpecificationStreamBatchSubscriber",
    "SpecificationStreamSubscriber",
    "SpecificationListBatchSubscriber",
    "SpecificationListSubscriber",
]


def create_subscriber(
    *,
    channel: Union["PubSub", str, None],
    list: Union["ListSub", str, None],
    stream: Union["StreamSub", str, None],
    # Subscriber args
    ack_policy: "AckPolicy" = EMPTY,
    no_reply: bool = False,
    broker_dependencies: Iterable["Dependant"] = (),
    broker_middlewares: Iterable["BrokerMiddleware[UnifyRedisDict]"] = (),
    # AsyncAPI args
    title_: Optional[str] = None,
    description_: Optional[str] = None,
    include_in_schema: bool = True,
) -> SubsciberType:
    validate_options(channel=channel, list=list, stream=stream)

    if (channel_sub := PubSub.validate(channel)) is not None:
        if ack_policy is not EMPTY:
            warnings.warn(
                "You can't use acknowledgement policy with core subscriber",
                RuntimeWarning,
                stacklevel=2,
            )

        return SpecificationChannelSubscriber(
            channel=channel_sub,
            # basic args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_dependencies=broker_dependencies,
            broker_middlewares=broker_middlewares,
            # AsyncAPI args
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    if (stream_sub := StreamSub.validate(stream)) is not None:
        if stream_sub.batch:
            return SpecificationStreamBatchSubscriber(
                stream=stream_sub,
                # basic args
                ack_policy=AckPolicy.REJECT_ON_ERROR
                if ack_policy is EMPTY
                else ack_policy,
                no_reply=no_reply,
                broker_dependencies=broker_dependencies,
                broker_middlewares=broker_middlewares,
                # AsyncAPI args
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )
        return SpecificationStreamSubscriber(
            stream=stream_sub,
            # basic args
            ack_policy=AckPolicy.REJECT_ON_ERROR if ack_policy is EMPTY else ack_policy,
            no_reply=no_reply,
            broker_dependencies=broker_dependencies,
            broker_middlewares=broker_middlewares,
            # AsyncAPI args
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    if (list_sub := ListSub.validate(list)) is not None:
        if ack_policy is not EMPTY:
            warnings.warn(
                "You can't use acknowledgement policy with core subscriber",
                RuntimeWarning,
                stacklevel=2,
            )

        if list_sub.batch:
            return SpecificationListBatchSubscriber(
                list=list_sub,
                # basic args
                ack_policy=ack_policy,
                no_reply=no_reply,
                broker_dependencies=broker_dependencies,
                broker_middlewares=broker_middlewares,
                # AsyncAPI args
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )
        return SpecificationListSubscriber(
            list=list_sub,
            # basic args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_dependencies=broker_dependencies,
            broker_middlewares=broker_middlewares,
            # AsyncAPI args
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    raise SetupError(INCORRECT_SETUP_MSG)

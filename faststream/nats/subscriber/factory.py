from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Optional, Union

from nats.aio.subscription import (
    DEFAULT_SUB_PENDING_BYTES_LIMIT,
    DEFAULT_SUB_PENDING_MSGS_LIMIT,
)
from nats.js.api import ConsumerConfig
from nats.js.client import (
    DEFAULT_JS_SUB_PENDING_BYTES_LIMIT,
    DEFAULT_JS_SUB_PENDING_MSGS_LIMIT,
)

from faststream.exceptions import SetupError
from faststream.nats.subscriber.specified import (
    SpecificationBatchPullStreamSubscriber,
    SpecificationConcurrentCoreSubscriber,
    SpecificationConcurrentPullStreamSubscriber,
    SpecificationConcurrentPushStreamSubscriber,
    SpecificationCoreSubscriber,
    SpecificationKeyValueWatchSubscriber,
    SpecificationObjStoreWatchSubscriber,
    SpecificationPullStreamSubscriber,
    SpecificationStreamSubscriber,
)

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends
    from nats.js import api

    from faststream._internal.basic_types import AnyDict
    from faststream._internal.types import BrokerMiddleware
    from faststream.middlewares import AckPolicy
    from faststream.nats.schemas import JStream, KvWatch, ObjWatch, PullSub


def create_subscriber(
    *,
    subject: str,
    queue: str,
    pending_msgs_limit: Optional[int],
    pending_bytes_limit: Optional[int],
    # Core args
    max_msgs: int,
    # JS args
    durable: Optional[str],
    config: Optional["api.ConsumerConfig"],
    ordered_consumer: bool,
    idle_heartbeat: Optional[float],
    flow_control: bool,
    deliver_policy: Optional["api.DeliverPolicy"],
    headers_only: Optional[bool],
    # pull args
    pull_sub: Optional["PullSub"],
    kv_watch: Optional["KvWatch"],
    obj_watch: Optional["ObjWatch"],
    inbox_prefix: bytes,
    # custom args
    ack_first: bool,
    max_workers: int,
    stream: Optional["JStream"],
    # Subscriber args
    ack_policy: "AckPolicy",
    no_reply: bool,
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable["BrokerMiddleware[Any]"],
    # Specification information
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "SpecificationCoreSubscriber",
    "SpecificationConcurrentCoreSubscriber",
    "SpecificationStreamSubscriber",
    "SpecificationConcurrentPushStreamSubscriber",
    "SpecificationPullStreamSubscriber",
    "SpecificationConcurrentPullStreamSubscriber",
    "SpecificationBatchPullStreamSubscriber",
    "SpecificationKeyValueWatchSubscriber",
    "SpecificationObjStoreWatchSubscriber",
]:
    if pull_sub is not None and stream is None:
        msg = "Pull subscriber can be used only with a stream"
        raise SetupError(msg)

    if not subject and not config:
        msg = "You must provide either `subject` or `config` option."
        raise SetupError(msg)

    config = config or ConsumerConfig(filter_subjects=[])

    if stream:
        # TODO: pull & queue warning
        # TODO: push & durable warning

        extra_options: AnyDict = {
            "pending_msgs_limit": pending_msgs_limit
            or DEFAULT_JS_SUB_PENDING_MSGS_LIMIT,
            "pending_bytes_limit": pending_bytes_limit
            or DEFAULT_JS_SUB_PENDING_BYTES_LIMIT,
            "durable": durable,
            "stream": stream.name,
        }

        if pull_sub is not None:
            extra_options.update({"inbox_prefix": inbox_prefix})

        else:
            extra_options.update(
                {
                    "ordered_consumer": ordered_consumer,
                    "idle_heartbeat": idle_heartbeat,
                    "flow_control": flow_control,
                    "deliver_policy": deliver_policy,
                    "headers_only": headers_only,
                    "manual_ack": not ack_first,
                },
            )

    else:
        extra_options = {
            "pending_msgs_limit": pending_msgs_limit or DEFAULT_SUB_PENDING_MSGS_LIMIT,
            "pending_bytes_limit": pending_bytes_limit
            or DEFAULT_SUB_PENDING_BYTES_LIMIT,
            "max_msgs": max_msgs,
        }

    if obj_watch is not None:
        return SpecificationObjStoreWatchSubscriber(
            subject=subject,
            config=config,
            obj_watch=obj_watch,
            broker_dependencies=broker_dependencies,
            broker_middlewares=broker_middlewares,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    if kv_watch is not None:
        return SpecificationKeyValueWatchSubscriber(
            subject=subject,
            config=config,
            kv_watch=kv_watch,
            broker_dependencies=broker_dependencies,
            broker_middlewares=broker_middlewares,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    if stream is None:
        if max_workers > 1:
            return SpecificationConcurrentCoreSubscriber(
                max_workers=max_workers,
                subject=subject,
                config=config,
                queue=queue,
                # basic args
                extra_options=extra_options,
                # Subscriber args
                ack_policy=ack_policy,
                no_reply=no_reply,
                broker_dependencies=broker_dependencies,
                broker_middlewares=broker_middlewares,
                # Specification
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )

        return SpecificationCoreSubscriber(
            subject=subject,
            config=config,
            queue=queue,
            # basic args
            extra_options=extra_options,
            # Subscriber args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_dependencies=broker_dependencies,
            broker_middlewares=broker_middlewares,
            # Specification
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    if max_workers > 1:
        if pull_sub is not None:
            return SpecificationConcurrentPullStreamSubscriber(
                max_workers=max_workers,
                pull_sub=pull_sub,
                stream=stream,
                subject=subject,
                config=config,
                # basic args
                extra_options=extra_options,
                # Subscriber args
                ack_policy=ack_policy,
                no_reply=no_reply,
                broker_dependencies=broker_dependencies,
                broker_middlewares=broker_middlewares,
                # Specification
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )

        return SpecificationConcurrentPushStreamSubscriber(
            max_workers=max_workers,
            stream=stream,
            subject=subject,
            config=config,
            queue=queue,
            # basic args
            extra_options=extra_options,
            # Subscriber args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_dependencies=broker_dependencies,
            broker_middlewares=broker_middlewares,
            # Specification
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    if pull_sub is not None:
        if pull_sub.batch:
            return SpecificationBatchPullStreamSubscriber(
                pull_sub=pull_sub,
                stream=stream,
                subject=subject,
                config=config,
                # basic args
                extra_options=extra_options,
                # Subscriber args
                ack_policy=ack_policy,
                no_reply=no_reply,
                broker_dependencies=broker_dependencies,
                broker_middlewares=broker_middlewares,
                # Specification
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )

        return SpecificationPullStreamSubscriber(
            pull_sub=pull_sub,
            stream=stream,
            subject=subject,
            config=config,
            # basic args
            extra_options=extra_options,
            # Subscriber args
            ack_policy=ack_policy,
            no_reply=no_reply,
            broker_dependencies=broker_dependencies,
            broker_middlewares=broker_middlewares,
            # Specification
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    return SpecificationStreamSubscriber(
        stream=stream,
        subject=subject,
        queue=queue,
        config=config,
        # basic args
        extra_options=extra_options,
        # Subscriber args
        ack_policy=ack_policy,
        no_reply=no_reply,
        broker_dependencies=broker_dependencies,
        broker_middlewares=broker_middlewares,
        # Specification information
        title_=title_,
        description_=description_,
        include_in_schema=include_in_schema,
    )

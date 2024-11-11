import warnings
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Optional, Union

from nats.aio.subscription import (
    DEFAULT_SUB_PENDING_BYTES_LIMIT,
    DEFAULT_SUB_PENDING_MSGS_LIMIT,
)
from nats.js.api import ConsumerConfig, DeliverPolicy
from nats.js.client import (
    DEFAULT_JS_SUB_PENDING_BYTES_LIMIT,
    DEFAULT_JS_SUB_PENDING_MSGS_LIMIT,
)

from faststream._internal.constants import EMPTY
from faststream.exceptions import SetupError
from faststream.middlewares import AckPolicy
from faststream.nats.subscriber.specified import (
    SpecificationBatchPullStreamSubscriber,
    SpecificationConcurrentCoreSubscriber,
    SpecificationConcurrentPullStreamSubscriber,
    SpecificationConcurrentPushStreamSubscriber,
    SpecificationCoreSubscriber,
    SpecificationKeyValueWatchSubscriber,
    SpecificationObjStoreWatchSubscriber,
    SpecificationPullStreamSubscriber,
    SpecificationPushStreamSubscriber,
)

if TYPE_CHECKING:
    from fast_depends.dependencies import Dependant
    from nats.js import api

    from faststream._internal.basic_types import AnyDict
    from faststream._internal.types import BrokerMiddleware
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
    flow_control: Optional[bool],
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
    broker_dependencies: Iterable["Dependant"],
    broker_middlewares: Iterable["BrokerMiddleware[Any]"],
    # Specification information
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "SpecificationCoreSubscriber",
    "SpecificationConcurrentCoreSubscriber",
    "SpecificationPushStreamSubscriber",
    "SpecificationConcurrentPushStreamSubscriber",
    "SpecificationPullStreamSubscriber",
    "SpecificationConcurrentPullStreamSubscriber",
    "SpecificationBatchPullStreamSubscriber",
    "SpecificationKeyValueWatchSubscriber",
    "SpecificationObjStoreWatchSubscriber",
]:
    _validate_input_for_misconfigure(
        subject=subject,
        queue=queue,
        pending_msgs_limit=pending_msgs_limit,
        pending_bytes_limit=pending_bytes_limit,
        max_msgs=max_msgs,
        durable=durable,
        config=config,
        ordered_consumer=ordered_consumer,
        idle_heartbeat=idle_heartbeat,
        flow_control=flow_control,
        deliver_policy=deliver_policy,
        headers_only=headers_only,
        pull_sub=pull_sub,
        kv_watch=kv_watch,
        obj_watch=obj_watch,
        ack_first=ack_first,
        max_workers=max_workers,
        stream=stream,
    )

    if ack_policy is EMPTY:
        ack_policy = AckPolicy.REJECT_ON_ERROR

    config = config or ConsumerConfig(filter_subjects=[])
    if config.durable_name is None:
        config.durable_name = durable
    if config.idle_heartbeat is None:
        config.idle_heartbeat = idle_heartbeat
    if config.headers_only is None:
        config.headers_only = headers_only
    if config.deliver_policy is DeliverPolicy.ALL:
        config.deliver_policy = deliver_policy or DeliverPolicy.ALL

    if stream:
        # Both JS Subscribers
        extra_options: AnyDict = {
            "pending_msgs_limit": pending_msgs_limit
            or DEFAULT_JS_SUB_PENDING_MSGS_LIMIT,
            "pending_bytes_limit": pending_bytes_limit
            or DEFAULT_JS_SUB_PENDING_BYTES_LIMIT,
            "durable": durable,
            "stream": stream.name,
        }

        if pull_sub is not None:
            # JS Pull Subscriber
            extra_options.update({"inbox_prefix": inbox_prefix})

        else:
            # JS Push Subscriber
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
        # Core Subscriber
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

    return SpecificationPushStreamSubscriber(
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


def _validate_input_for_misconfigure(
    subject: str,
    queue: str,  # default ""
    pending_msgs_limit: Optional[int],
    pending_bytes_limit: Optional[int],
    max_msgs: int,  # default 0
    durable: Optional[str],
    config: Optional["api.ConsumerConfig"],
    ordered_consumer: bool,  # default False
    idle_heartbeat: Optional[float],
    flow_control: Optional[bool],
    deliver_policy: Optional["api.DeliverPolicy"],
    headers_only: Optional[bool],
    pull_sub: Optional["PullSub"],
    kv_watch: Optional["KvWatch"],
    obj_watch: Optional["ObjWatch"],
    ack_first: bool,  # default False
    max_workers: int,  # default 1
    stream: Optional["JStream"],
) -> None:
    if not subject and not config:
        raise SetupError("You must provide either the `subject` or `config` option.")

    if stream and kv_watch:
        raise SetupError(
            "You can't use both the `stream` and `kv_watch` options simultaneously."
        )

    if stream and obj_watch:
        raise SetupError(
            "You can't use both the `stream` and `obj_watch` options simultaneously."
        )

    if kv_watch and obj_watch:
        raise SetupError(
            "You can't use both the `kv_watch` and `obj_watch` options simultaneously."
        )

    if pull_sub and not stream:
        raise SetupError(
            "The pull subscriber can only be used with the `stream` option."
        )
    

    if ack_policy is not EMPTY:
        if stream is None:
            warnings.warn(
                "You can't use acknowledgement policy with core subscriber. Use JetStream instead.",
                RuntimeWarning,
                stacklevel=3,
            )

        if obj_watch is not None:
            warnings.warn(
                "You can't use acknowledgement policy with ObjectStorage watch subscriber.",
                RuntimeWarning,
                stacklevel=3,
            )

        if kv_watch is not None:
            warnings.warn(
                "You can't use acknowledgement policy with KeyValue watch subscriber.",
                RuntimeWarning,
                stacklevel=3,
            )

    if max_msgs > 0 and any((stream, kv_watch, obj_watch)):
        warnings.warn(
            "The `max_msgs` option can be used only with a NATS Core Subscriber.",
            RuntimeWarning,
            stacklevel=4,
        )

    if not stream:
        if obj_watch or kv_watch:
            # Obj/Kv Subscriber
            if pending_msgs_limit is not None:
                warnings.warn(
                    message="The `pending_msgs_limit` option can be used only with JetStream (Pull/Push) or Core Subscription.",
                    category=RuntimeWarning,
                    stacklevel=4,
                )

            if pending_bytes_limit is not None:
                warnings.warn(
                    message="The `pending_bytes_limit` option can be used only with JetStream (Pull/Push) or Core Subscription.",
                    category=RuntimeWarning,
                    stacklevel=4,
                )

            if queue:
                warnings.warn(
                    message="The `queue` option can be used only with JetStream Push or Core Subscription.",
                    category=RuntimeWarning,
                    stacklevel=4,
                )

            if max_workers > 1:
                warnings.warn(
                    message="The `max_workers` option can be used only with JetStream (Pull/Push) or Core Subscription.",
                    category=RuntimeWarning,
                    stacklevel=4,
                )

        # Core/Obj/Kv Subscriber
        if durable:
            warnings.warn(
                message="The `durable` option can be used only with JetStream (Pull/Push) Subscription.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if config is not None:
            warnings.warn(
                message="The `config` option can be used only with JetStream (Pull/Push) Subscription.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if ordered_consumer:
            warnings.warn(
                message="The `ordered_consumer` option can be used only with JetStream (Pull/Push) Subscription.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if idle_heartbeat is not None:
            warnings.warn(
                message="The `idle_heartbeat` option can be used only with JetStream (Pull/Push) Subscription.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if flow_control:
            warnings.warn(
                message="The `flow_control` option can be used only with JetStream Push Subscription.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if deliver_policy:
            warnings.warn(
                message="The `deliver_policy` option can be used only with JetStream (Pull/Push) Subscription.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if headers_only:
            warnings.warn(
                message="The `headers_only` option can be used only with JetStream (Pull/Push) Subscription.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if ack_first:
            warnings.warn(
                message="The `ack_first` option can be used only with JetStream Push Subscription.",
                category=RuntimeWarning,
                stacklevel=4,
            )

    else:
        # JetStream Subscribers
        if pull_sub:
            if queue:
                warnings.warn(
                    message="The `queue` option has no effect with JetStream Pull Subscription. You probably wanted to use the `durable` option instead.",
                    category=RuntimeWarning,
                    stacklevel=4,
                )

            if ordered_consumer:
                warnings.warn(
                    "The `ordered_consumer` option has no effect with JetStream Pull Subscription. It can only be used with JetStream Push Subscription.",
                    RuntimeWarning,
                    stacklevel=4,
                )

            if ack_first:
                warnings.warn(
                    message="The `ack_first` option has no effect with JetStream Pull Subscription. It can only be used with JetStream Push Subscription.",
                    category=RuntimeWarning,
                    stacklevel=4,
                )

            if flow_control:
                warnings.warn(
                    message="The `flow_control` option has no effect with JetStream Pull Subscription. It can only be used with JetStream Push Subscription.",
                    category=RuntimeWarning,
                    stacklevel=4,
                )

        else:
            # JS PushSub
            if durable is not None:
                warnings.warn(
                    message="The JetStream Push consumer with the `durable` option can't be scaled horizontally across multiple instances. You probably wanted to use the `queue` option instead. Also, we strongly recommend using the Jetstream PullSubsriber with the `durable` option as the default.",
                    category=RuntimeWarning,
                    stacklevel=4,
                )

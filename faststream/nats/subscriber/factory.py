import warnings
from typing import TYPE_CHECKING, Any, Iterable, Optional, Union

from nats.aio.subscription import (
    DEFAULT_SUB_PENDING_BYTES_LIMIT,
    DEFAULT_SUB_PENDING_MSGS_LIMIT,
)
from nats.js.api import ConsumerConfig, DeliverPolicy
from nats.js.client import (
    DEFAULT_JS_SUB_PENDING_BYTES_LIMIT,
    DEFAULT_JS_SUB_PENDING_MSGS_LIMIT,
)

from faststream.exceptions import SetupError
from faststream.nats.subscriber.asyncapi import (
    AsyncAPIBatchPullStreamSubscriber,
    AsyncAPIConcurrentCoreSubscriber,
    AsyncAPIConcurrentPullStreamSubscriber,
    AsyncAPIConcurrentPushStreamSubscriber,
    AsyncAPICoreSubscriber,
    AsyncAPIKeyValueWatchSubscriber,
    AsyncAPIObjStoreWatchSubscriber,
    AsyncAPIPullStreamSubscriber,
    AsyncAPIStreamSubscriber,
)

if TYPE_CHECKING:
    from fast_depends.dependencies import Depends
    from nats.js import api

    from faststream.broker.types import BrokerMiddleware
    from faststream.nats.schemas import JStream, KvWatch, ObjWatch, PullSub
    from faststream.types import AnyDict


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
    no_ack: bool,
    no_reply: bool,
    retry: Union[bool, int],
    broker_dependencies: Iterable["Depends"],
    broker_middlewares: Iterable["BrokerMiddleware[Any]"],
    # AsyncAPI information
    title_: Optional[str],
    description_: Optional[str],
    include_in_schema: bool,
) -> Union[
    "AsyncAPICoreSubscriber",
    "AsyncAPIConcurrentCoreSubscriber",
    "AsyncAPIStreamSubscriber",
    "AsyncAPIConcurrentPushStreamSubscriber",
    "AsyncAPIPullStreamSubscriber",
    "AsyncAPIConcurrentPullStreamSubscriber",
    "AsyncAPIBatchPullStreamSubscriber",
    "AsyncAPIKeyValueWatchSubscriber",
    "AsyncAPIObjStoreWatchSubscriber",
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

    config = config or ConsumerConfig(filter_subjects=[])
    if config.durable_name is None:
        config.durable_name = durable
    if config.idle_heartbeat is None:
        config.idle_heartbeat = idle_heartbeat
    if config.flow_control is None:
        config.flow_control = flow_control
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
                }
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
        return AsyncAPIObjStoreWatchSubscriber(
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
        return AsyncAPIKeyValueWatchSubscriber(
            subject=subject,
            config=config,
            kv_watch=kv_watch,
            broker_dependencies=broker_dependencies,
            broker_middlewares=broker_middlewares,
            title_=title_,
            description_=description_,
            include_in_schema=include_in_schema,
        )

    elif stream is None:
        if max_workers > 1:
            return AsyncAPIConcurrentCoreSubscriber(
                max_workers=max_workers,
                subject=subject,
                config=config,
                queue=queue,
                # basic args
                extra_options=extra_options,
                # Subscriber args
                no_ack=no_ack,
                no_reply=no_reply,
                retry=retry,
                broker_dependencies=broker_dependencies,
                broker_middlewares=broker_middlewares,
                # AsyncAPI information
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )

        else:
            return AsyncAPICoreSubscriber(
                subject=subject,
                config=config,
                queue=queue,
                # basic args
                extra_options=extra_options,
                # Subscriber args
                no_ack=no_ack,
                no_reply=no_reply,
                retry=retry,
                broker_dependencies=broker_dependencies,
                broker_middlewares=broker_middlewares,
                # AsyncAPI information
                title_=title_,
                description_=description_,
                include_in_schema=include_in_schema,
            )

    else:
        if max_workers > 1:
            if pull_sub is not None:
                return AsyncAPIConcurrentPullStreamSubscriber(
                    max_workers=max_workers,
                    pull_sub=pull_sub,
                    stream=stream,
                    subject=subject,
                    config=config,
                    # basic args
                    extra_options=extra_options,
                    # Subscriber args
                    no_ack=no_ack,
                    no_reply=no_reply,
                    retry=retry,
                    broker_dependencies=broker_dependencies,
                    broker_middlewares=broker_middlewares,
                    # AsyncAPI information
                    title_=title_,
                    description_=description_,
                    include_in_schema=include_in_schema,
                )

            else:
                return AsyncAPIConcurrentPushStreamSubscriber(
                    max_workers=max_workers,
                    stream=stream,
                    subject=subject,
                    config=config,
                    queue=queue,
                    # basic args
                    extra_options=extra_options,
                    # Subscriber args
                    no_ack=no_ack,
                    no_reply=no_reply,
                    retry=retry,
                    broker_dependencies=broker_dependencies,
                    broker_middlewares=broker_middlewares,
                    # AsyncAPI information
                    title_=title_,
                    description_=description_,
                    include_in_schema=include_in_schema,
                )

        else:
            if pull_sub is not None:
                if pull_sub.batch:
                    return AsyncAPIBatchPullStreamSubscriber(
                        pull_sub=pull_sub,
                        stream=stream,
                        subject=subject,
                        config=config,
                        # basic args
                        extra_options=extra_options,
                        # Subscriber args
                        no_ack=no_ack,
                        no_reply=no_reply,
                        retry=retry,
                        broker_dependencies=broker_dependencies,
                        broker_middlewares=broker_middlewares,
                        # AsyncAPI information
                        title_=title_,
                        description_=description_,
                        include_in_schema=include_in_schema,
                    )

                else:
                    return AsyncAPIPullStreamSubscriber(
                        pull_sub=pull_sub,
                        stream=stream,
                        subject=subject,
                        config=config,
                        # basic args
                        extra_options=extra_options,
                        # Subscriber args
                        no_ack=no_ack,
                        no_reply=no_reply,
                        retry=retry,
                        broker_dependencies=broker_dependencies,
                        broker_middlewares=broker_middlewares,
                        # AsyncAPI information
                        title_=title_,
                        description_=description_,
                        include_in_schema=include_in_schema,
                    )

            else:
                return AsyncAPIStreamSubscriber(
                    stream=stream,
                    subject=subject,
                    queue=queue,
                    config=config,
                    # basic args
                    extra_options=extra_options,
                    # Subscriber args
                    no_ack=no_ack,
                    no_reply=no_reply,
                    retry=retry,
                    broker_dependencies=broker_dependencies,
                    broker_middlewares=broker_middlewares,
                    # AsyncAPI information
                    title_=title_,
                    description_=description_,
                    include_in_schema=include_in_schema,
                )


def _validate_input_for_misconfigure(
    subject: str,
    queue: str,
    pending_msgs_limit: Optional[int],
    pending_bytes_limit: Optional[int],
    max_msgs: int,
    durable: Optional[str],
    config: Optional["api.ConsumerConfig"],
    ordered_consumer: bool,
    idle_heartbeat: Optional[float],
    flow_control: Optional[bool],
    deliver_policy: Optional["api.DeliverPolicy"],
    headers_only: Optional[bool],
    pull_sub: Optional["PullSub"],
    kv_watch: Optional["KvWatch"],
    obj_watch: Optional["ObjWatch"],
    ack_first: bool,
    max_workers: int,
    stream: Optional["JStream"],
):
    if pull_sub is not None and stream is None:
        raise SetupError("Pull subscriber can be used only with a stream")

    if not subject and not config:
        raise SetupError("You must provide either `subject` or `config` option.")

    if max_msgs > 0 and any((stream, kv_watch, obj_watch, pull_sub)):
        warnings.warn(
            "`max_msgs` option can be used with NATS Core Subscriber - only.",
            RuntimeWarning,
            stacklevel=4,
        )

    if not stream:
        # Core/Obj/Kv Subscriber
        if idle_heartbeat is not None:
            warnings.warn(
                "`idle_heartbeat` option can be used with JetStream (Pull/Push) - only.",
                RuntimeWarning,
                stacklevel=4,
            )

        if flow_control is not None:
            warnings.warn(
                "`flow_control` option can be used with JetStream (Pull/Push) - only.",
                RuntimeWarning,
                stacklevel=4,
            )

        if deliver_policy is not None:
            warnings.warn(
                "`deliver_policy` option can be used with JetStream (Pull/Push) - only.",
                RuntimeWarning,
                stacklevel=4,
            )

        if headers_only is not None:
            warnings.warn(
                "`headers_only` option can be used with JetStream (Pull/Push) - only.",
                RuntimeWarning,
                stacklevel=4,
            )

    elif stream:
        if pull_sub is not None:
            if queue:  # default ""
                warnings.warn(
                    message="`queue` option has no effect with JetStream Pull Subscription. Probably, you wanted to use `durable` instead.",
                    category=RuntimeWarning,
                    stacklevel=4,
                )

            if ordered_consumer:  # default False
                warnings.warn(
                    "`ordered_consumer` option has no effect with JetStream Pull Subscription. It can be used with JetStream Push Subscription - only.",
                    RuntimeWarning,
                    stacklevel=4,
                )

            if ack_first:  # default False
                warnings.warn(
                    message="`ack_first` option has no effect with JetStream Pull Subscription. It can be used with JetStream Push Subscription - only.",
                    category=RuntimeWarning,
                    stacklevel=4,
                )

        else:
            # JS PushSub
            if durable is not None:
                warnings.warn(
                    message="JetStream Push consumer with durable option can't be scaled horizontally by multiple instances. Probably, you are looking for `queue` option. Also, we strongly recommend to use Jetstream PullSubsriber with durable option as a default.",
                    category=RuntimeWarning,
                    stacklevel=4,
                )

    if obj_watch is not None or kv_watch is not None:
        # Obj/Kv Subscriber
        if pending_msgs_limit is not None:
            warnings.warn(
                message="`pending_msgs_limit` has no effect for KeyValue/ObjectValue subscriber. It can be used with JetStream (Pull/Push) or Core Subscription - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )
        if pending_bytes_limit is not None:
            warnings.warn(
                message="`pending_bytes_limit` has no effect for KeyValue/ObjectValue subscriber. It can be used with JetStream (Pull/Push) or Core Subscription - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if queue:
            warnings.warn(
                message="`queue` has no effect for KeyValue/ObjectValue subscriber. It can be used with JetStream (Pull/Push) or Core Subscription - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if durable:
            warnings.warn(
                message="`durable` has no effect for KeyValue/ObjectValue subscriber. It can be used with JetStream (Pull/Push) or Core Subscription - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if config is not None:
            warnings.warn(
                message="`config` has no effect for KeyValue/ObjectValue subscriber. It can be used with JetStream (Pull/Push) or Core Subscription - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if ordered_consumer:
            warnings.warn(
                message="`ordered_consumer` has no effect for KeyValue/ObjectValue subscriber. It can be used with JetStream (Pull/Push) or Core Subscription - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if idle_heartbeat is not None:
            warnings.warn(
                message="`idle_heartbeat` has no effect for KeyValue/ObjectValue subscriber. It can be used with JetStream (Pull/Push) or Core Subscription - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if flow_control:
            warnings.warn(
                message="`flow_control` has no effect for KeyValue/ObjectValue subscriber. It can be used with JetStream (Pull/Push) or Core Subscription - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if deliver_policy:
            warnings.warn(
                message="`deliver_policy` has no effect for KeyValue/ObjectValue subscriber. It can be used with JetStream (Pull/Push) or Core Subscription - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if headers_only:
            warnings.warn(
                message="`headers_only` has no effect for KeyValue/ObjectValue subscriber. It can be used with JetStream (Pull/Push) or Core Subscription - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if ack_first:
            warnings.warn(
                message="`ack_first` has no effect for KeyValue/ObjectValue subscriber. It can be used with JetStream (Pull/Push) or Core Subscription - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if max_workers > 1:
            warnings.warn(
                message="`max_workers` has no effect for KeyValue/ObjectValue subscriber. It can be used with JetStream (Pull/Push) or Core Subscription - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )
    else:
        # Core Subscriber
        if durable:
            warnings.warn(
                message="`durable` option has no effect for NATS Core Subscription. It can be used with JetStream (Pull) - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if config:
            warnings.warn(
                message="`config` option has no effect for NATS Core Subscription. It can be used with JetStream (Pull/Push) - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if ordered_consumer:
            warnings.warn(
                message="`ordered_consumer` option has no effect for NATS Core Subscription. It can be used with JetStream Push - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if idle_heartbeat is not None:
            warnings.warn(
                message="`idle_heartbeat` option has no effect for NATS Core Subscription. It can be used with JetStream (Pull/Push) - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if flow_control:
            warnings.warn(
                message="`flow_control` option has no effect for NATS Core Subscription. It can be used with JetStream (Pull/Push) - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if deliver_policy:
            warnings.warn(
                message="`deliver_policy` option has no effect for NATS Core Subscription. It can be used with JetStream (Pull/Push) - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if headers_only:
            warnings.warn(
                message="`headers_only` option has no effect for NATS Core Subscription. It can be used with JetStream (Pull/Push) - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

        if ack_first:
            warnings.warn(
                message="`ack_first` option has no effect for NATS Core Subscription. It can be used with JetStream Push - only.",
                category=RuntimeWarning,
                stacklevel=4,
            )

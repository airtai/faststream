import warnings
from typing import TYPE_CHECKING, Any, Iterable, Optional, Union

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
    if pull_sub is not None and stream is None:
        raise SetupError("Pull subscriber can be used only with a stream")

    if not subject and not config:
        raise SetupError("You must provide either `subject` or `config` option.")

    config = config or ConsumerConfig(filter_subjects=[])

    if stream:
        if pull_sub is not None and queue is not None:
            warnings.warn(
                "`queue` option has no effect with JetStream Pull Subscribtion. Probably, you wanted to use durable instead.",
                RuntimeWarning,
                stacklevel=3,
            )

        if pull_sub is None and durable is not None:
            warnings.warn(
                "We recommend use `queue` for Push Subscription.",
                RuntimeWarning,
                stacklevel=3,
            )

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
                }
            )

        if pull_sub is not None:
            if ordered_consumer is not None:
                warnings.warn(
                    "`ordered_consumer` option has no effect with JetStream Pull Subscribtion.",
                    RuntimeWarning,
                    stacklevel=3,
                )

            if idle_heartbeat is not None:
                warnings.warn(
                    "`idle_heartbeat` option has no effect with JetStream Pull Subscribtion.",
                    RuntimeWarning,
                    stacklevel=3,
                )

            if flow_control is not None:
                warnings.warn(
                    "`flow_control` option has no effect with JetStream Pull Subscribtion.",
                    RuntimeWarning,
                    stacklevel=3,
                )

            if deliver_policy is not None:
                warnings.warn(
                    "`deliver_policy` option has no effect with JetStream Pull Subscribtion.",
                    RuntimeWarning,
                    stacklevel=3,
                )

            if headers_only is not None:
                warnings.warn(
                    "`headers_only` option has no effect with JetStream Pull Subscribtion.",
                    RuntimeWarning,
                    stacklevel=3,
                )

            if ack_first:
                warnings.warn(
                    "`ack_first` option has no effect with JetStream Pull Subscribtion.",
                    RuntimeWarning,
                    stacklevel=3,
                )

    else:
        extra_options = {
            "pending_msgs_limit": pending_msgs_limit or DEFAULT_SUB_PENDING_MSGS_LIMIT,
            "pending_bytes_limit": pending_bytes_limit
            or DEFAULT_SUB_PENDING_BYTES_LIMIT,
            "max_msgs": max_msgs,
        }

    if obj_watch is not None:
        if max_workers > 1:
            warnings.warn(
                "`max_workers` has no effect for ObjectValue subscriber.",
                RuntimeWarning,
                stacklevel=3,
            )

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
        if max_workers > 1:
            warnings.warn(
                "`max_workers` has no effect for KeyValue subscriber.",
                RuntimeWarning,
                stacklevel=3,
            )

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

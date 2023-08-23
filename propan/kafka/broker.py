import logging
from functools import partial, wraps
from types import TracebackType
from typing import (
    Any,
    AsyncContextManager,
    Awaitable,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Type,
    Union,
)

import aiokafka
from fast_depends.dependencies import Depends
from kafka.coordinator.assignors.abstract import AbstractPartitionAssignor
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor

from propan.__about__ import __version__
from propan._compat import override
from propan.broker.core.asyncronous import BrokerAsyncUsecase, default_filter
from propan.broker.message import PropanMessage
from propan.broker.push_back_watcher import BaseWatcher, WatcherContext
from propan.broker.types import (
    AsyncCustomDecoder,
    AsyncCustomParser,
    P_HandlerParams,
    T_HandlerReturn,
)
from propan.broker.wrapper import HandlerCallWrapper
from propan.kafka.asyncapi import Handler, Publisher
from propan.kafka.producer import AioKafkaPropanProducer
from propan.kafka.shared.logging import KafkaLoggingMixin
from propan.kafka.shared.schemas import ConsumerConnectionParams
from propan.types import SendableMessage
from propan.utils import context
from propan.utils.data import filter_by_dict
from propan.utils.functions import to_async

KafkaMessage = PropanMessage[aiokafka.ConsumerRecord]


class KafkaBroker(
    KafkaLoggingMixin,
    BrokerAsyncUsecase[aiokafka.ConsumerRecord, ConsumerConnectionParams],
):
    handlers: Dict[str, Handler]  # type: ignore[assignment]
    _publishers: Dict[str, Publisher]  # type: ignore[assignment]
    _producer: Optional[AioKafkaPropanProducer]

    def __init__(
        self,
        bootstrap_servers: Union[str, List[str]] = "localhost",
        *,
        protocol: str = "kafka",
        protocol_version: str = "auto",
        client_id: str = "propan-" + __version__,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            url=bootstrap_servers,
            protocol=protocol,
            protocol_version=protocol_version,
            **kwargs,
            client_id=client_id,
            bootstrap_servers=bootstrap_servers,
        )
        self.client_id = client_id
        self._producer = None

    async def _close(
        self,
        exc_type: Optional[Type[BaseException]] = None,
        exc_val: Optional[BaseException] = None,
        exec_tb: Optional[TracebackType] = None,
    ) -> None:
        if self._producer is not None:  # pragma: no branch
            await self._producer.stop()
            self._producer = None

        await super()._close(exc_type, exc_val, exec_tb)

    async def connect(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> ConsumerConnectionParams:
        connection = await super().connect(*args, **kwargs)
        for p in self._publishers.values():
            p._producer = self._producer
        return connection

    @override
    async def _connect(  # type: ignore[override]
        self,
        *,
        client_id: str,
        **kwargs: Any,
    ) -> ConsumerConnectionParams:
        producer = aiokafka.AIOKafkaProducer(**kwargs, client_id=client_id)
        await producer.start()
        self._producer = AioKafkaPropanProducer(
            producer=producer,
            decoder=self._global_decoder,
            parser=self._global_parser,
        )
        return filter_by_dict(ConsumerConnectionParams, kwargs)

    async def start(self) -> None:
        context.set_local(
            "log_context",
            self._get_log_context(None, ""),
        )

        await super().start()

        for handler in self.handlers.values():
            c = self._get_log_context(None, handler.topics)
            self._log(f"`{handler.name}` waiting for messages", extra=c)
            await handler.start(**(self._connection or {}))

    def _process_message(
        self,
        func: Callable[[KafkaMessage], Awaitable[T_HandlerReturn]],
        call_wrapper: HandlerCallWrapper[
            aiokafka.ConsumerRecord, P_HandlerParams, T_HandlerReturn
        ],
        watcher: BaseWatcher,
    ) -> Callable[[KafkaMessage], Awaitable[T_HandlerReturn]]:
        @wraps(func)
        async def process_wrapper(message: KafkaMessage) -> T_HandlerReturn:
            async with WatcherContext(watcher, message):
                r = await self._execute_handler(func, message)
                headers = {"correlation_id": message.correlation_id}

                if message.reply_to:
                    await self.publish(
                        message=r or "",
                        headers=headers,
                        topic=message.reply_to,
                    )

                for publisher in call_wrapper._publishers:
                    try:
                        await publisher.publish(
                            message=r,
                            correlation_id=message.correlation_id,
                        )
                    except Exception as e:
                        self._log(
                            f"Publish exception: {e}",
                            logging.ERROR,
                            self._get_log_context(
                                context.get_local("message"),
                                (getattr(publisher, "topic", ""),),
                            ),
                            exc_info=e,
                        )

                return r

            raise AssertionError("unreachable")

        return process_wrapper

    @override
    def subscriber(  # type: ignore[override]
        self,
        *topics: str,
        group_id: Optional[str] = None,
        key_deserializer: Optional[Callable[[bytes], Any]] = None,
        value_deserializer: Optional[Callable[[bytes], Any]] = None,
        fetch_max_wait_ms: int = 500,
        fetch_max_bytes: int = 52428800,
        fetch_min_bytes: int = 1,
        max_partition_fetch_bytes: int = 1 * 1024 * 1024,
        auto_offset_reset: Literal[
            "latest",
            "earliest",
            "none",
        ] = "latest",
        enable_auto_commit: bool = True,
        auto_commit_interval_ms: int = 5000,
        check_crcs: bool = True,
        partition_assignment_strategy: Sequence[AbstractPartitionAssignor] = (
            RoundRobinPartitionAssignor,
        ),
        max_poll_interval_ms: int = 300000,
        rebalance_timeout_ms: Optional[int] = None,
        session_timeout_ms: int = 10000,
        heartbeat_interval_ms: int = 3000,
        consumer_timeout_ms: int = 200,
        max_poll_records: Optional[int] = None,
        exclude_internal_topics: bool = True,
        isolation_level: Literal[
            "read_uncommitted",
            "read_committed",
        ] = "read_uncommitted",
        # broker arguments
        dependencies: Sequence[Depends] = (),
        parser: Optional[AsyncCustomParser[aiokafka.ConsumerRecord]] = None,
        decoder: Optional[AsyncCustomDecoder[aiokafka.ConsumerRecord]] = None,
        middlewares: Optional[
            List[
                Callable[
                    [KafkaMessage],
                    AsyncContextManager[None],
                ]
            ]
        ] = None,
        filter: Union[
            Callable[[KafkaMessage], bool], Callable[[KafkaMessage], Awaitable[bool]]
        ] = default_filter,
        batch: bool = False,
        max_records: Optional[int] = None,
        batch_timeout_ms: int = 200,
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
        **original_kwargs: Any,
    ) -> Callable[
        [Callable[P_HandlerParams, T_HandlerReturn]],
        HandlerCallWrapper[aiokafka.ConsumerRecord, P_HandlerParams, T_HandlerReturn],
    ]:
        super().subscriber()

        self._setup_log_context(topics)

        key = "".join(topics)
        builder = partial(
            aiokafka.AIOKafkaConsumer,
            key_deserializer=key_deserializer,
            value_deserializer=value_deserializer,
            fetch_max_wait_ms=fetch_max_wait_ms,
            fetch_max_bytes=fetch_max_bytes,
            fetch_min_bytes=fetch_min_bytes,
            max_partition_fetch_bytes=max_partition_fetch_bytes,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=enable_auto_commit,
            auto_commit_interval_ms=auto_commit_interval_ms,
            check_crcs=check_crcs,
            partition_assignment_strategy=partition_assignment_strategy,
            max_poll_interval_ms=max_poll_interval_ms,
            rebalance_timeout_ms=rebalance_timeout_ms,
            session_timeout_ms=session_timeout_ms,
            heartbeat_interval_ms=heartbeat_interval_ms,
            consumer_timeout_ms=consumer_timeout_ms,
            max_poll_records=max_poll_records,
            exclude_internal_topics=exclude_internal_topics,
            isolation_level=isolation_level,
        )
        handler = self.handlers.get(
            key,
            Handler(
                *topics,
                group_id=group_id,
                client_id=self.client_id,
                builder=builder,
                description=description,
                title=title,
                batch=batch,
                batch_timeout_ms=batch_timeout_ms,
                max_records=max_records,
            ),
        )

        self.handlers[key] = handler

        def consumer_wrapper(
            func: Callable[P_HandlerParams, T_HandlerReturn],
        ) -> HandlerCallWrapper[
            aiokafka.ConsumerRecord, P_HandlerParams, T_HandlerReturn
        ]:
            handler_call, dependant = self._wrap_handler(
                func=func,
                extra_dependencies=dependencies,
                **original_kwargs,
                topics=topics,
            )

            handler.add_call(
                handler=handler_call,
                filter=to_async(filter),
                middlewares=middlewares,
                parser=parser or self._global_parser,
                decoder=decoder or self._global_decoder,
                dependant=dependant,
            )

            return handler_call

        return consumer_wrapper

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
        # AsyncAPI information
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Publisher:
        publisher = self._publishers.get(
            topic,
            Publisher(
                topic=topic,
                client_id=self.client_id,
                key=key,
                batch=batch,
                partition=partition,
                timestamp_ms=timestamp_ms,
                headers=headers,
                reply_to=reply_to,
                title=title,
                _description=description,
            ),
        )
        super().publisher(topic, publisher)
        return publisher

    async def publish(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[SendableMessage]:
        if self._producer is None:
            raise ValueError("KafkaBroker is not started yet")
        return await self._producer.publish(*args, **kwargs)

    async def publish_batch(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if self._producer is None:
            raise ValueError("KafkaBroker is not started yet")
        await self._producer.publish_batch(*args, **kwargs)

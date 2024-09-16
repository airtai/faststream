import time
from typing import TYPE_CHECKING, Any, Callable, Optional

from prometheus_client import Counter, Gauge, Histogram

from faststream import BaseMiddleware
from faststream.exceptions import (
    AckMessage,
    NackMessage,
    RejectMessage,
    SkipMessage,
)
from faststream.prometheus.provider import MetricsSettingsProvider

if TYPE_CHECKING:  # pragma: no cover
    from prometheus_client import CollectorRegistry

    from faststream.broker.message import StreamMessage
    from faststream.types import AsyncFunc, AsyncFuncAny


class _MetricsContainer:
    def __init__(self, registry: "CollectorRegistry"):
        self.received_messages = Counter(
            name="received_messages",
            documentation="Received messages",
            labelnames=["broker", "handler"],
            registry=registry,
        )
        self.received_messages_size = Histogram(
            name="received_messages_size",
            documentation="Received messages size",
            labelnames=["broker", "handler"],
            registry=registry,
            buckets=[pow(2, x) for x in range(30)],  # from 2^0 to 2^30
        )
        self.received_messages_processing_time = Histogram(
            name="received_messages_processing_time",
            documentation="Received messages processing time",
            labelnames=["broker", "handler"],
            registry=registry,
        )
        self.received_messages_in_process = Gauge(
            name="received_messages_in_process",
            documentation="Received messages in process",
            labelnames=["broker", "handler"],
            registry=registry,
        )
        self.received_processed_messages = Counter(
            name="received_processed_messages",
            documentation="Received processed messages",
            labelnames=["broker", "handler", "status"],
            registry=registry,
        )
        self.messages_processing_exceptions = Counter(
            name="messages_processing_exceptions",
            documentation="messages processing exceptions",
            labelnames=["broker", "handler", "exception_type"],
            registry=registry,
        )
        self.published_messages = Counter(
            name="published_messages",
            documentation="Published messages",
            labelnames=["broker", "destination", "status"],
            registry=registry,
        )
        self.messages_publish_time = Histogram(
            name="messages_publish_time",
            documentation="Messages publish time",
            labelnames=["broker", "destination"],
            registry=registry,
        )
        self.messages_publishing_exceptions = Counter(
            name="messages_publishing_exceptions",
            documentation="messages publishing exceptions",
            labelnames=["broker", "destination", "exception_type"],
            registry=registry,
        )


class _PrometheusMiddleware(BaseMiddleware):
    def __init__(
        self,
        msg: Optional[Any] = None,
        *,
        settings_provider_factory: Callable[[Any], MetricsSettingsProvider[Any]],
        metrics_container: _MetricsContainer,
    ) -> None:
        self._metrics = metrics_container
        self._settings_provider = settings_provider_factory(msg)
        super().__init__(msg)

    async def consume_scope(
        self,
        call_next: "AsyncFuncAny",
        msg: "StreamMessage[Any]",
    ) -> Any:
        messaging_system = self._settings_provider.messaging_system
        consume_attrs = self._settings_provider.get_consume_attrs_from_message(msg)
        destination_name = consume_attrs["destination_name"]

        self._metrics.received_messages.labels(
            broker=messaging_system,
            handler=destination_name,
        ).inc(consume_attrs["messages_count"])

        self._metrics.received_messages_size.labels(
            broker=messaging_system,
            handler=destination_name,
        ).observe(consume_attrs["message_size"])

        err: Optional[Exception] = None

        self._metrics.received_messages_in_process.labels(
            broker=messaging_system,
            handler=destination_name,
        ).inc()

        start_time = time.perf_counter()

        try:
            result = await call_next(await self.on_consume(msg))

        except Exception as e:
            err = e
            raise

        finally:
            duration = time.perf_counter() - start_time
            self._metrics.received_messages_processing_time.labels(
                broker=messaging_system,
                handler=destination_name,
            ).observe(duration)

            self._metrics.received_messages_in_process.labels(
                broker=messaging_system,
                handler=destination_name,
            ).dec()

            status = "acked"

            if msg.committed or err:
                status = (
                    msg.committed.value
                    if msg.committed
                    else PROCESSING_STATUS_BY_HANDLER_EXCEPTION_MAP.get(type(err))
                    or "error"
                )

            self._metrics.received_processed_messages.labels(
                broker=messaging_system,
                handler=destination_name,
                status=status,
            ).inc()

            if status == "error":
                self._metrics.messages_processing_exceptions.labels(
                    broker=messaging_system,
                    handler=destination_name,
                    exception_type=type(err).__name__,
                ).inc()

        return result

    async def publish_scope(
        self,
        call_next: "AsyncFunc",
        msg: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        err: Optional[Exception] = None
        start_time = time.perf_counter()

        try:
            result = await call_next(
                await self.on_publish(msg, *args, **kwargs),
                *args,
                **kwargs,
            )

        except Exception as e:
            err = e
            raise

        finally:
            duration = time.perf_counter() - start_time
            destination_name = (
                self._settings_provider.get_publish_destination_name_from_kwargs(kwargs)
            )
            messaging_system = self._settings_provider.messaging_system

            self._metrics.messages_publish_time.labels(
                broker=messaging_system,
                destination=destination_name,
            ).observe(duration)

            status = "error" if err else "success"
            messages_count = len((msg, *args))

            self._metrics.published_messages.labels(
                broker=messaging_system,
                destination=destination_name,
                status=status,
            ).inc(messages_count)

            if status == "error":
                self._metrics.messages_publishing_exceptions.labels(
                    broker=messaging_system,
                    destination=destination_name,
                    exception_type=type(err).__name__,
                ).inc()

        return result


PROCESSING_STATUS_BY_HANDLER_EXCEPTION_MAP = {
    AckMessage: "acked",
    NackMessage: "nacked",
    RejectMessage: "rejected",
    SkipMessage: "skipped",
}


class BasePrometheusMiddleware:
    def __init__(
        self,
        *,
        settings_provider_factory: Callable[[Any], MetricsSettingsProvider[Any]],
        registry: "CollectorRegistry",
    ):
        self._metrics = _MetricsContainer(registry)
        self._settings_provider_factory = settings_provider_factory

    def __call__(self, msg: Optional[Any]) -> BaseMiddleware:
        return _PrometheusMiddleware(
            msg=msg,
            metrics_container=self._metrics,
            settings_provider_factory=self._settings_provider_factory,
        )

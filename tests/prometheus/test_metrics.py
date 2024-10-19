import random
from typing import List, Optional
from unittest.mock import ANY

import pytest
from dirty_equals import IsPositiveFloat, IsStr
from prometheus_client import CollectorRegistry, Histogram, Metric
from prometheus_client.samples import Sample

from faststream.prometheus.container import MetricsContainer
from faststream.prometheus.manager import MetricsManager
from faststream.prometheus.types import ProcessingStatus, PublishingStatus


class TestCaseMetrics:
    @staticmethod
    def create_metrics_manager(
        app_name: Optional[str] = None,
        metrics_prefix: Optional[str] = None,
        received_messages_size_buckets: Optional[List[float]] = None,
    ) -> MetricsManager:
        registry = CollectorRegistry()
        container = MetricsContainer(
            registry,
            metrics_prefix=metrics_prefix,
            received_messages_size_buckets=received_messages_size_buckets,
        )
        return MetricsManager(container, app_name=app_name)

    @pytest.fixture
    def app_name(self, request) -> str:
        return "youtube"

    @pytest.fixture
    def metrics_prefix(self, request) -> str:
        return "fs"

    @pytest.fixture
    def broker(self) -> str:
        return "rabbit"

    @pytest.fixture
    def queue(self) -> str:
        return "default.test"

    @pytest.fixture
    def messages_amount(self) -> int:
        return random.randint(1, 10)

    @pytest.fixture
    def exception_type(self) -> str:
        return Exception.__name__

    def test_add_received_message(
        self,
        app_name: str,
        metrics_prefix: str,
        queue: str,
        broker: str,
        messages_amount: int,
    ) -> None:
        manager = self.create_metrics_manager(
            app_name=app_name,
            metrics_prefix=metrics_prefix,
        )

        expected = Metric(
            name=f"{metrics_prefix}_received_messages",
            documentation="Count of received messages by broker and handler",
            unit="",
            typ="counter",
        )
        expected.samples = [
            Sample(
                name=f"{metrics_prefix}_received_messages_total",
                labels={"app_name": app_name, "broker": broker, "handler": queue},
                value=float(messages_amount),
                timestamp=None,
                exemplar=None,
            ),
            Sample(
                name=f"{metrics_prefix}_received_messages_created",
                labels={"app_name": app_name, "broker": broker, "handler": queue},
                value=IsPositiveFloat,
                timestamp=None,
                exemplar=None,
            ),
        ]

        manager.add_received_message(
            amount=messages_amount, broker=broker, handler=queue
        )

        metric_values = manager._container.received_messages_total.collect()

        assert metric_values == [expected]

    @pytest.mark.parametrize(
        "is_default_buckets",
        [
            pytest.param(True, id="with default buckets"),
            pytest.param(False, id="with custom buckets"),
        ],
    )
    def test_observe_received_messages_size(
        self,
        app_name: str,
        metrics_prefix: str,
        queue: str,
        broker: str,
        is_default_buckets: bool,
    ) -> None:
        manager_kwargs = {
            "app_name": app_name,
            "metrics_prefix": metrics_prefix,
        }

        custom_buckets = [1.0, 2.0, 3.0, float("inf")]

        if not is_default_buckets:
            manager_kwargs["received_messages_size_buckets"] = custom_buckets

        manager = self.create_metrics_manager(**manager_kwargs)

        size = 1
        buckets = (
            MetricsContainer.DEFAULT_SIZE_BUCKETS
            if is_default_buckets
            else custom_buckets
        )

        expected = Metric(
            name=f"{metrics_prefix}_received_messages_size_bytes",
            documentation="Histogram of received messages size in bytes by broker and handler",
            unit="",
            typ="histogram",
        )
        expected.samples = [
            *[
                Sample(
                    name=f"{metrics_prefix}_received_messages_size_bytes_bucket",
                    labels={
                        "app_name": app_name,
                        "broker": broker,
                        "handler": queue,
                        "le": IsStr,
                    },
                    value=1.0,
                    timestamp=None,
                    exemplar=None,
                )
                for _ in buckets
            ],
            Sample(
                name=f"{metrics_prefix}_received_messages_size_bytes_count",
                labels={"app_name": app_name, "broker": broker, "handler": queue},
                value=1.0,
                timestamp=None,
                exemplar=None,
            ),
            Sample(
                name=f"{metrics_prefix}_received_messages_size_bytes_sum",
                labels={"app_name": app_name, "broker": broker, "handler": queue},
                value=size,
                timestamp=None,
                exemplar=None,
            ),
            Sample(
                name=f"{metrics_prefix}_received_messages_size_bytes_created",
                labels={"app_name": app_name, "broker": broker, "handler": queue},
                value=ANY,
                timestamp=None,
                exemplar=None,
            ),
        ]

        manager.observe_received_messages_size(size=size, broker=broker, handler=queue)

        metric_values = manager._container.received_messages_size_bytes.collect()

        assert metric_values == [expected]

    def test_add_received_message_in_process(
        self,
        app_name: str,
        metrics_prefix: str,
        queue: str,
        broker: str,
        messages_amount: int,
    ) -> None:
        manager = self.create_metrics_manager(
            app_name=app_name,
            metrics_prefix=metrics_prefix,
        )

        expected = Metric(
            name=f"{metrics_prefix}_received_messages_in_process",
            documentation="Gauge of received messages in process by broker and handler",
            unit="",
            typ="gauge",
        )
        expected.samples = [
            Sample(
                name=f"{metrics_prefix}_received_messages_in_process",
                labels={"app_name": app_name, "broker": broker, "handler": queue},
                value=float(messages_amount),
                timestamp=None,
                exemplar=None,
            ),
        ]

        manager.add_received_message_in_process(
            amount=messages_amount, broker=broker, handler=queue
        )

        metric_values = manager._container.received_messages_in_process.collect()

        assert metric_values == [expected]

    def test_remove_received_message_in_process(
        self,
        app_name: str,
        metrics_prefix: str,
        queue: str,
        broker: str,
        messages_amount: int,
    ) -> None:
        manager = self.create_metrics_manager(
            app_name=app_name,
            metrics_prefix=metrics_prefix,
        )

        expected = Metric(
            name=f"{metrics_prefix}_received_messages_in_process",
            documentation="Gauge of received messages in process by broker and handler",
            unit="",
            typ="gauge",
        )
        expected.samples = [
            Sample(
                name=f"{metrics_prefix}_received_messages_in_process",
                labels={"app_name": app_name, "broker": broker, "handler": queue},
                value=float(messages_amount - 1),
                timestamp=None,
                exemplar=None,
            ),
        ]

        manager.add_received_message_in_process(
            amount=messages_amount, broker=broker, handler=queue
        )
        manager.remove_received_message_in_process(
            amount=1, broker=broker, handler=queue
        )

        metric_values = manager._container.received_messages_in_process.collect()

        assert metric_values == [expected]

    @pytest.mark.parametrize(
        "status",
        [
            pytest.param(ProcessingStatus.acked, id="acked status"),
            pytest.param(ProcessingStatus.nacked, id="nacked status"),
            pytest.param(ProcessingStatus.rejected, id="rejected status"),
            pytest.param(ProcessingStatus.skipped, id="skipped status"),
            pytest.param(ProcessingStatus.error, id="error status"),
        ],
    )
    def test_add_received_processed_message(
        self,
        app_name: str,
        metrics_prefix: str,
        queue: str,
        broker: str,
        messages_amount: int,
        status: ProcessingStatus,
    ) -> None:
        manager = self.create_metrics_manager(
            app_name=app_name,
            metrics_prefix=metrics_prefix,
        )

        expected = Metric(
            name=f"{metrics_prefix}_received_processed_messages",
            documentation="Count of received processed messages by broker, handler and status",
            unit="",
            typ="counter",
        )
        expected.samples = [
            Sample(
                name=f"{metrics_prefix}_received_processed_messages_total",
                labels={
                    "app_name": app_name,
                    "broker": broker,
                    "handler": queue,
                    "status": status.value,
                },
                value=float(messages_amount),
                timestamp=None,
                exemplar=None,
            ),
            Sample(
                name=f"{metrics_prefix}_received_processed_messages_created",
                labels={
                    "app_name": app_name,
                    "broker": broker,
                    "handler": queue,
                    "status": status.value,
                },
                value=IsPositiveFloat,
                timestamp=None,
                exemplar=None,
            ),
        ]

        manager.add_received_processed_message(
            amount=messages_amount,
            status=status,
            broker=broker,
            handler=queue,
        )

        metric_values = manager._container.received_processed_messages_total.collect()

        assert metric_values == [expected]

    def test_observe_received_processed_message_duration(
        self,
        app_name: str,
        metrics_prefix: str,
        queue: str,
        broker: str,
    ) -> None:
        manager = self.create_metrics_manager(
            app_name=app_name,
            metrics_prefix=metrics_prefix,
        )

        duration = 0.001

        expected = Metric(
            name=f"{metrics_prefix}_received_processed_messages_duration_seconds",
            documentation="Histogram of received processed messages duration in seconds by broker and handler",
            unit="",
            typ="histogram",
        )
        expected.samples = [
            *[
                Sample(
                    name=f"{metrics_prefix}_received_processed_messages_duration_seconds_bucket",
                    labels={
                        "app_name": app_name,
                        "broker": broker,
                        "handler": queue,
                        "le": IsStr,
                    },
                    value=1.0,
                    timestamp=None,
                    exemplar=None,
                )
                for _ in Histogram.DEFAULT_BUCKETS
            ],
            Sample(
                name=f"{metrics_prefix}_received_processed_messages_duration_seconds_count",
                labels={"app_name": app_name, "broker": broker, "handler": queue},
                value=1.0,
                timestamp=None,
                exemplar=None,
            ),
            Sample(
                name=f"{metrics_prefix}_received_processed_messages_duration_seconds_sum",
                labels={"app_name": app_name, "broker": broker, "handler": queue},
                value=duration,
                timestamp=None,
                exemplar=None,
            ),
            Sample(
                name=f"{metrics_prefix}_received_processed_messages_duration_seconds_created",
                labels={"app_name": app_name, "broker": broker, "handler": queue},
                value=ANY,
                timestamp=None,
                exemplar=None,
            ),
        ]

        manager.observe_received_processed_message_duration(
            duration=duration,
            broker=broker,
            handler=queue,
        )

        metric_values = (
            manager._container.received_processed_messages_duration_seconds.collect()
        )

        assert metric_values == [expected]

    def test_add_received_processed_message_exception(
        self,
        app_name: str,
        metrics_prefix: str,
        queue: str,
        broker: str,
        exception_type: str,
    ) -> None:
        manager = self.create_metrics_manager(
            app_name=app_name,
            metrics_prefix=metrics_prefix,
        )

        expected = Metric(
            name=f"{metrics_prefix}_received_processed_messages_exceptions",
            documentation="Count of received processed messages exceptions by broker, handler and exception_type",
            unit="",
            typ="counter",
        )
        expected.samples = [
            Sample(
                name=f"{metrics_prefix}_received_processed_messages_exceptions_total",
                labels={
                    "app_name": app_name,
                    "broker": broker,
                    "handler": queue,
                    "exception_type": exception_type,
                },
                value=1.0,
                timestamp=None,
                exemplar=None,
            ),
            Sample(
                name=f"{metrics_prefix}_received_processed_messages_exceptions_created",
                labels={
                    "app_name": app_name,
                    "broker": broker,
                    "handler": queue,
                    "exception_type": exception_type,
                },
                value=IsPositiveFloat,
                timestamp=None,
                exemplar=None,
            ),
        ]

        manager.add_received_processed_message_exception(
            exception_type=exception_type,
            broker=broker,
            handler=queue,
        )

        metric_values = (
            manager._container.received_processed_messages_exceptions_total.collect()
        )

        assert metric_values == [expected]

    @pytest.mark.parametrize(
        "status",
        [
            pytest.param(PublishingStatus.success, id="success status"),
            pytest.param(PublishingStatus.error, id="error status"),
        ],
    )
    def test_add_published_message(
        self,
        app_name: str,
        metrics_prefix: str,
        queue: str,
        broker: str,
        messages_amount: int,
        status: PublishingStatus,
    ) -> None:
        manager = self.create_metrics_manager(
            app_name=app_name,
            metrics_prefix=metrics_prefix,
        )

        expected = Metric(
            name=f"{metrics_prefix}_published_messages",
            documentation="Count of published messages by destination and status",
            unit="",
            typ="counter",
        )
        expected.samples = [
            Sample(
                name=f"{metrics_prefix}_published_messages_total",
                labels={
                    "app_name": app_name,
                    "broker": broker,
                    "destination": queue,
                    "status": status.value,
                },
                value=1.0,
                timestamp=None,
                exemplar=None,
            ),
            Sample(
                name=f"{metrics_prefix}_published_messages_created",
                labels={
                    "app_name": app_name,
                    "broker": broker,
                    "destination": queue,
                    "status": status.value,
                },
                value=IsPositiveFloat,
                timestamp=None,
                exemplar=None,
            ),
        ]

        manager.add_published_message(
            status=status,
            broker=broker,
            destination=queue,
        )

        metric_values = manager._container.published_messages_total.collect()

        assert metric_values == [expected]

    def test_observe_published_message_duration(
        self,
        app_name: str,
        metrics_prefix: str,
        queue: str,
        broker: str,
    ) -> None:
        manager = self.create_metrics_manager(
            app_name=app_name,
            metrics_prefix=metrics_prefix,
        )

        duration = 0.001

        expected = Metric(
            name=f"{metrics_prefix}_published_messages_duration_seconds",
            documentation="Histogram of published messages duration in seconds by broker and destination",
            unit="",
            typ="histogram",
        )
        expected.samples = [
            *[
                Sample(
                    name=f"{metrics_prefix}_published_messages_duration_seconds_bucket",
                    labels={
                        "app_name": app_name,
                        "broker": broker,
                        "destination": queue,
                        "le": IsStr,
                    },
                    value=1.0,
                    timestamp=None,
                    exemplar=None,
                )
                for _ in Histogram.DEFAULT_BUCKETS
            ],
            Sample(
                name=f"{metrics_prefix}_published_messages_duration_seconds_count",
                labels={"app_name": app_name, "broker": broker, "destination": queue},
                value=1.0,
                timestamp=None,
                exemplar=None,
            ),
            Sample(
                name=f"{metrics_prefix}_published_messages_duration_seconds_sum",
                labels={"app_name": app_name, "broker": broker, "destination": queue},
                value=duration,
                timestamp=None,
                exemplar=None,
            ),
            Sample(
                name=f"{metrics_prefix}_published_messages_duration_seconds_created",
                labels={"app_name": app_name, "broker": broker, "destination": queue},
                value=IsPositiveFloat,
                timestamp=None,
                exemplar=None,
            ),
        ]

        manager.observe_published_message_duration(
            duration=duration,
            broker=broker,
            destination=queue,
        )

        metric_values = manager._container.published_messages_duration_seconds.collect()

        assert metric_values == [expected]

    def test_add_published_message_exception(
        self,
        app_name: str,
        metrics_prefix: str,
        queue: str,
        broker: str,
        exception_type: str,
    ) -> None:
        manager = self.create_metrics_manager(
            app_name=app_name,
            metrics_prefix=metrics_prefix,
        )

        expected = Metric(
            name=f"{metrics_prefix}_published_messages_exceptions",
            documentation="Count of published messages exceptions by broker, destination and exception_type",
            unit="",
            typ="counter",
        )
        expected.samples = [
            Sample(
                name=f"{metrics_prefix}_published_messages_exceptions_total",
                labels={
                    "app_name": app_name,
                    "broker": broker,
                    "destination": queue,
                    "exception_type": exception_type,
                },
                value=1.0,
                timestamp=None,
                exemplar=None,
            ),
            Sample(
                name=f"{metrics_prefix}_published_messages_exceptions_created",
                labels={
                    "app_name": app_name,
                    "broker": broker,
                    "destination": queue,
                    "exception_type": exception_type,
                },
                value=IsPositiveFloat,
                timestamp=None,
                exemplar=None,
            ),
        ]

        manager.add_published_message_exception(
            exception_type=exception_type,
            broker=broker,
            destination=queue,
        )

        metric_values = manager._container.published_messages_exceptions_total.collect()

        assert metric_values == [expected]

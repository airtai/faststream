from types import SimpleNamespace

import pytest

from faststream.prometheus import MetricsSettingsProvider
from faststream.redis.prometheus.provider import (
    BatchRedisMetricsSettingsProvider,
    RedisMetricsSettingsProvider,
    settings_provider_factory,
)
from tests.prometheus.basic import LocalMetricsSettingsProviderTestcase


class LocalBaseRedisMetricsSettingsProviderTestcase(
    LocalMetricsSettingsProviderTestcase
):
    messaging_system = "redis"

    def test_get_publish_destination_name_from_cmd(self, queue: str) -> None:
        expected_destination_name = queue
        provider = self.get_provider()
        command = SimpleNamespace(destination=queue)

        destination_name = provider.get_publish_destination_name_from_cmd(command)

        assert destination_name == expected_destination_name


class TestRedisMetricsSettingsProvider(LocalBaseRedisMetricsSettingsProviderTestcase):
    @staticmethod
    def get_provider() -> MetricsSettingsProvider:
        return RedisMetricsSettingsProvider()

    @pytest.mark.parametrize(
        "destination",
        (
            pytest.param("channel", id="destination is channel"),
            pytest.param("list", id="destination is list"),
            pytest.param("stream", id="destination is stream"),
            pytest.param("", id="destination is blank"),
        ),
    )
    def test_get_consume_attrs_from_message(self, queue: str, destination: str) -> None:
        body = b"Hello"
        expected_attrs = {
            "destination_name": queue if destination else "",
            "message_size": len(body),
            "messages_count": 1,
        }
        raw_message = {}

        if destination:
            raw_message[destination] = queue

        message = SimpleNamespace(body=body, raw_message=raw_message)

        provider = self.get_provider()
        attrs = provider.get_consume_attrs_from_message(message)

        assert attrs == expected_attrs


class TestBatchRedisMetricsSettingsProvider(
    LocalBaseRedisMetricsSettingsProviderTestcase
):
    @staticmethod
    def get_provider() -> MetricsSettingsProvider:
        return BatchRedisMetricsSettingsProvider()

    @pytest.mark.parametrize(
        "destination",
        (
            pytest.param("channel", id="destination is channel"),
            pytest.param("list", id="destination is list"),
            pytest.param("stream", id="destination is stream"),
            pytest.param("", id="destination is blank"),
        ),
    )
    def test_get_consume_attrs_from_message(self, queue: str, destination: str) -> None:
        decoded_body = ["Hi ", "again, ", "FastStream!"]
        body = str(decoded_body).encode()
        expected_attrs = {
            "destination_name": queue if destination else "",
            "message_size": len(body),
            "messages_count": len(decoded_body),
        }
        raw_message = {}

        if destination:
            raw_message[destination] = queue

        message = SimpleNamespace(
            body=body, _decoded_body=decoded_body, raw_message=raw_message
        )

        provider = self.get_provider()
        attrs = provider.get_consume_attrs_from_message(message)

        assert attrs == expected_attrs


@pytest.mark.parametrize(
    ("msg", "expected_provider"),
    (
        pytest.param(
            {"type": "blist"},
            BatchRedisMetricsSettingsProvider(),
            id="batch message",
        ),
        pytest.param(
            {"type": "not_blist"},
            RedisMetricsSettingsProvider(),
            id="single message",
        ),
        pytest.param(
            None,
            RedisMetricsSettingsProvider(),
            id="None message",
        ),
    ),
)
def test_settings_provider_factory(msg, expected_provider) -> None:
    provider = settings_provider_factory(msg)

    assert isinstance(provider, type(expected_provider))

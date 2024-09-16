from typing import TYPE_CHECKING, Optional, Union

from faststream.prometheus.provider import (
    ConsumeAttrs,
    MetricsSettingsProvider,
)

if TYPE_CHECKING:
    from faststream.broker.message import StreamMessage
    from faststream.types import AnyDict


class BaseRedisMetricsSettingsProvider(MetricsSettingsProvider["AnyDict"]):
    def __init__(self):
        self.messaging_system = "redis"

    def get_publish_destination_name_from_kwargs(
        self,
        kwargs: "AnyDict",
    ) -> str:
        return self._get_destination(kwargs)

    @staticmethod
    def _get_destination(kwargs: "AnyDict") -> str:
        return kwargs.get("channel") or kwargs.get("list") or kwargs.get("stream") or ""


class RedisMetricsSettingsProvider(BaseRedisMetricsSettingsProvider):
    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[AnyDict]",
    ) -> ConsumeAttrs:
        return {
            "destination_name": self._get_destination(msg.raw_message),
            "message_size": len(msg.body),
            "messages_count": 1,
        }


class BatchRedisMetricsSettingsProvider(BaseRedisMetricsSettingsProvider):
    def get_consume_attrs_from_message(
        self,
        msg: "StreamMessage[AnyDict]",
    ) -> ConsumeAttrs:
        return {
            "destination_name": self._get_destination(msg.raw_message),
            "message_size": len(msg.body),
            "messages_count": len(msg._decoded_body),
        }


def settings_provider_factory(
    msg: Optional["AnyDict"],
) -> Union[
    RedisMetricsSettingsProvider,
    BatchRedisMetricsSettingsProvider,
]:
    if msg is not None and msg.get("type", "").startswith("b"):
        return BatchRedisMetricsSettingsProvider()
    else:
        return RedisMetricsSettingsProvider()

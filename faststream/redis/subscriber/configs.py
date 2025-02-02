from dataclasses import dataclass

from faststream._internal.subscriber.configs import SubscriberUsecaseOptions


@dataclass
class RedisSubscriberBaseConfigs:
    internal_configs: SubscriberUsecaseOptions

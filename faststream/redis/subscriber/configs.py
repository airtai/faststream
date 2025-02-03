from dataclasses import dataclass

from faststream._internal.subscriber.configs import SubscriberUseCaseConfigs


@dataclass
class RedisSubscriberBaseConfigs:
    internal_configs: SubscriberUseCaseConfigs

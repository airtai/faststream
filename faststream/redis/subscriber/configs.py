from dataclasses import dataclass

from faststream._internal.subscriber.configs import SubscriberUsecaseOptions


@dataclass
class RedisSubscriberBaseOptions:
    internal_options: SubscriberUsecaseOptions

from dataclasses import dataclass

from faststream._internal.subscriber.schemas import SubscriberUsecaseOptions


@dataclass
class RedisSubscriberBaseOptions:
    internal_options: SubscriberUsecaseOptions

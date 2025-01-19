from dataclasses import dataclass

from faststream._internal.subscriber.schemas import SubscriberUsecaseOptions


@dataclass
class RedisLogicSubscriberOptions:
    internal_options: SubscriberUsecaseOptions

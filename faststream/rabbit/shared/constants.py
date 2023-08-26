from enum import Enum, unique

RABBIT_REPLY = "amq.rabbitmq.reply-to"


@unique
class ExchangeType(str, Enum):
    FANOUT = "fanout"
    DIRECT = "direct"
    TOPIC = "topic"
    HEADERS = "headers"
    X_DELAYED_MESSAGE = "x-delayed-message"
    X_CONSISTENT_HASH = "x-consistent-hash"
    X_MODULUS_HASH = "x-modulus-hash"

from enum import Enum


class AckPolicy(str, Enum):
    ACK_FIRST = "ack_first"
    ACK = "ack"
    REJECT_ON_ERROR = "reject_on_error"
    NACK_ON_ERROR = "nack_on_error"
    DO_NOTHING = "do_nothing"

from faststream.broker.message import AckStatus
from faststream.exceptions import AckMessage, NackMessage, RejectMessage, SkipMessage
from faststream.prometheus.types import ProcessingStatus

PROCESSING_STATUS_BY_HANDLER_EXCEPTION_MAP = {
    AckMessage: ProcessingStatus.acked,
    NackMessage: ProcessingStatus.nacked,
    RejectMessage: ProcessingStatus.rejected,
    SkipMessage: ProcessingStatus.skipped,
}


PROCESSING_STATUS_BY_ACK_STATUS = {
    AckStatus.acked: ProcessingStatus.acked,
    AckStatus.nacked: ProcessingStatus.nacked,
    AckStatus.rejected: ProcessingStatus.rejected,
}

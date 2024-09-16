from enum import StrEnum


class ProcessingStatus(StrEnum):
    acked = "acked"
    nacked = "nacked"
    rejected = "rejected"
    skipped = "skipped"
    error = "error"


class PublishingStatus(StrEnum):
    success = "success"
    error = "error"

from typing_extensions import Annotated, Doc


class ObjWatch:
    """A class to represent a NATS obj watch subscription."""

    __slots__ = (
        "bucket",
        "ignore_deletes",
        "include_history",
        "meta_only",
        "timeout",
    )

    def __init__(
        self,
        bucket: Annotated[str, Doc("The name of the bucket to watch.")],
        ignore_deletes: Annotated[bool, Doc("Ignore delete events.")] = False,
        include_history: Annotated[bool, Doc("Include history.")] = False,
        meta_only: Annotated[bool, Doc("Only metadata.")] = False,
        timeout: Annotated[float, Doc("The timeout for the watch.")] = 5.0,
    ) -> None:
        self.bucket = bucket
        self.ignore_deletes = ignore_deletes
        self.include_history = include_history
        self.meta_only = meta_only
        self.timeout = timeout

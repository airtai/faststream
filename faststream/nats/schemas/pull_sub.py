from typing import Literal, Optional, Union, overload

from typing_extensions import Annotated, Doc


class PullSub:
    """A class to represent a NATS pull subscription."""

    __slots__ = (
        "batch",
        "batch_size",
        "timeout",
    )

    def __init__(
        self,
        batch_size: Annotated[
            int,
            Doc("Consuming messages batch size."),
        ] = 1,
        timeout: Annotated[
            Optional[float],
            Doc(
                "Wait this time for required batch size will be accumulated in stream."
            ),
        ] = 5.0,
        batch: Annotated[
            bool,
            Doc(
                "Whether to propagate consuming batch as iterable object to your handler."
            ),
        ] = False,
    ) -> None:
        self.batch_size = batch_size
        self.batch = batch
        self.timeout = timeout

    @overload
    @classmethod
    def validate(cls, value: Literal[True]) -> "PullSub": ...

    @overload
    @classmethod
    def validate(cls, value: Literal[False]) -> None: ...

    @overload
    @classmethod
    def validate(cls, value: "PullSub") -> "PullSub": ...

    @overload
    @classmethod
    def validate(cls, value: Union[bool, "PullSub"]) -> Optional["PullSub"]: ...

    @classmethod
    def validate(cls, value: Union[bool, "PullSub"]) -> Optional["PullSub"]:
        if value is True:
            return PullSub()
        elif value is False:
            return None
        else:
            return value

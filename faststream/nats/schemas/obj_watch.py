from typing import Literal, Optional, Union, overload

from typing_extensions import Annotated, Doc


class ObjWatch:
    """A class to represent a NATS object storage watch subscription."""

    __slots__ = (
        "ignore_deletes",
        "include_history",
        "meta_only",
        "timeout",
        "declare",
    )

    def __init__(
        self,
        ignore_deletes: Annotated[
            bool,
            Doc("Ignore delete events."),
        ] = False,
        include_history: Annotated[
            bool,
            Doc("Include history."),
        ] = False,
        meta_only: Annotated[
            bool,
            Doc("Only metadata."),
        ] = False,
        timeout: Annotated[
            float,
            Doc("The timeout for the watch."),
        ] = 5.0,
        # custom
        declare: Annotated[
            bool,
            Doc(
                "Whether to create object storage automatically or just connect to it."
            ),
        ] = True,
    ) -> None:
        self.ignore_deletes = ignore_deletes
        self.include_history = include_history
        self.meta_only = meta_only
        self.timeout = timeout

        self.declare = declare

    @overload
    @classmethod
    def validate(cls, value: Literal[True]) -> "ObjWatch": ...

    @overload
    @classmethod
    def validate(cls, value: Literal[False]) -> None: ...

    @overload
    @classmethod
    def validate(cls, value: "ObjWatch") -> "ObjWatch": ...

    @overload
    @classmethod
    def validate(cls, value: Union[bool, "ObjWatch"]) -> Optional["ObjWatch"]: ...

    @classmethod
    def validate(cls, value: Union[bool, "ObjWatch"]) -> Optional["ObjWatch"]:
        if value is True:
            return ObjWatch()
        elif value is False:
            return None
        else:
            return value

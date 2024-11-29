from typing import Dict

from typing_extensions import Annotated, Doc


class ReplyConfig:
    """Class to store a config for subscribers' replies."""

    __slots__ = (
        "immediate",
        "mandatory",
        "persist",
    )

    def __init__(
        self,
        mandatory: Annotated[
            bool,
            Doc(
                "Client waits for confirmation that the message is placed to some queue. "
                "RabbitMQ returns message to client if there is no suitable queue."
            ),
        ] = True,
        immediate: Annotated[
            bool,
            Doc(
                "Client expects that there is consumer ready to take the message to work. "
                "RabbitMQ returns message to client if there is no suitable consumer."
            ),
        ] = False,
        persist: Annotated[
            bool,
            Doc("Restore the message on RabbitMQ reboot."),
        ] = False,
    ) -> None:
        self.mandatory = mandatory
        self.immediate = immediate
        self.persist = persist

    def to_dict(self) -> Dict[str, bool]:
        """Convert object to options dict."""
        return {
            "mandatory": self.mandatory,
            "immediate": self.immediate,
            "persist": self.persist,
        }

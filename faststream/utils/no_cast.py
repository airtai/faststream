from typing import Any

from fast_depends.library import CustomField

from faststream.types import AnyDict


class NoCast(CustomField):
    """A class that represents a custom field without casting.

    Methods:
        __init__ : Initializes the NoCast object.
        use : Returns the provided keyword arguments as a dictionary.
    """

    def __init__(self) -> None:
        """Initialize the NoCast object."""
        super().__init__(cast=False)

    def use(self, **kwargs: Any) -> AnyDict:
        """Return a dictionary containing the keyword arguments passed to the function.

        Args:
            **kwargs: Keyword arguments

        Returns:
            Dictionary containing the keyword arguments
        """
        return kwargs

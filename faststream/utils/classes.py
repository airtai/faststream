from typing import Any, ClassVar


class Singleton:
    """A class to implement the Singleton design pattern.

    Attributes:
        _instance : the single instance of the class

    Methods:
        __new__ : creates a new instance of the class if it doesn't exist, otherwise returns the existing instance
        _drop : sets the instance to None, allowing a new instance to be created
    """

    _instance: ClassVar[Any] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        """Create a singleton instance of a class.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            The singleton instance of the class
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def _drop(cls) -> None:
        """Drop the instance of a class.

        Returns:
            None
        """
        cls._instance = None

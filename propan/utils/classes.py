from typing import Any


class Singleton:
    _instance = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "Singleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def _drop(cls) -> None:
        cls._instance = None

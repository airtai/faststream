from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any, Dict, Iterator, TypeVar

from faststream.types import AnyDict
from faststream.utils.classes import Singleton

T = TypeVar("T")


class ContextRepo(Singleton):
    _global_context: AnyDict
    _scope_context: Dict[str, ContextVar[Any]]

    def __init__(self) -> None:
        self._global_context = {"context": self}
        self._scope_context = {}

    def set_global(self, key: str, v: Any) -> None:
        self._global_context[key] = v

    def reset_global(self, key: str) -> None:
        self._global_context.pop(key, None)

    def set_local(self, key: str, value: T) -> "Token[T]":
        context_var = self._scope_context.get(key)
        if context_var is None:
            context_var = ContextVar(key, default=None)
            self._scope_context[key] = context_var
        return context_var.set(value)

    def reset_local(self, key: str, tag: "Token[Any]") -> None:
        self._scope_context[key].reset(tag)

    def get_local(self, key: str) -> Any:
        context_var = self._scope_context.get(key)
        if context_var is not None:  # pragma: no branch
            return context_var.get()

    def clear(self) -> None:
        self._global_context = {"context": self}
        self._scope_context = {}

    def get(self, key: str) -> Any:
        return self._global_context.get(key, self.get_local(key))

    def __getattr__(self, __name: str) -> Any:
        return self.get(__name)

    @property
    def context(self) -> AnyDict:
        return {
            **self._global_context,
            **{i: j.get() for i, j in self._scope_context.items()},
        }

    @contextmanager
    def scope(self, key: str, value: Any) -> Iterator[None]:
        token = self.set_local(key, value)
        try:
            yield
        finally:
            self.reset_local(key, token)


context: ContextRepo = ContextRepo()

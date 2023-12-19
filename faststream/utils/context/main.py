from contextlib import contextmanager
from contextvars import ContextVar, Token
from inspect import _empty
from typing import Any, Dict, Iterator, Mapping, TypeVar

from faststream.types import AnyDict
from faststream.utils.classes import Singleton

T = TypeVar("T")


class ContextRepo(Singleton):
    """A class to represent a context repository.

    Attributes:
        _global_context : dictionary representing the global context
        _scope_context : dictionary representing the scope context

    Methods:
        __init__ : initializes the ContextRepo object
        set_global : sets a global context variable
        reset_global : resets a global context variable
        set_local : sets a local context variable
        reset_local : resets a local context variable
        get_local : gets the value of a local context variable
        clear : clears the global and scope context
        get : gets the value of a context variable
        __getattr__ : gets the value of a context variable using attribute access
        context : gets the current context as a dictionary
        scope : creates a context scope for a specific key and value
    """

    _global_context: AnyDict
    _scope_context: Dict[str, ContextVar[Any]]

    def __init__(self) -> None:
        """Initialize the class.

        Attributes:
            _global_context : a dictionary representing the global context
            _scope_context : a dictionary representing the scope context
        """
        self._global_context = {"context": self}
        self._scope_context = {}

    def set_global(self, key: str, v: Any) -> None:
        """Sets a value in the global context.

        Args:
            key: The key to set in the global context.
            v: The value to set.

        Returns:
            None.
        """
        self._global_context[key] = v

    def reset_global(self, key: str) -> None:
        """Resets a key in the global context.

        Args:
            key (str): The key to reset in the global context.

        Returns:
            None
        """
        self._global_context.pop(key, None)

    def set_local(self, key: str, value: T) -> "Token[T]":
        """Set a local context variable.

        Args:
            key (str): The key for the context variable.
            value (T): The value to set for the context variable.

        Returns:
            Token[T]: A token representing the context variable.
        """
        context_var = self._scope_context.get(key)
        if context_var is None:
            context_var = ContextVar(key, default=None)
            self._scope_context[key] = context_var
        return context_var.set(value)

    def reset_local(self, key: str, tag: "Token[Any]") -> None:
        """Resets the local context for a given key.

        Args:
            key (str): The key to reset the local context for.
            tag (Token[Any]): The tag associated with the local context.

        Returns:
            None
        """
        self._scope_context[key].reset(tag)

    def get_local(self, key: str, default: Any = None) -> Any:
        """Get the value of a local variable.

        Args:
            key: The key of the local variable to retrieve.
            default: The default value to return if the local variable is not found.

        Returns:
            The value of the local variable.
        """
        context_var = self._scope_context.get(key)
        if context_var is not None:  # pragma: no branch
            return context_var.get()
        else:
            return default

    def clear(self) -> None:
        self._global_context = {"context": self}
        self._scope_context = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get the value associated with a key.

        Args:
            key: The key to retrieve the value for.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key.
        """
        return self._global_context.get(key, self.get_local(key, default))

    def resolve(self, argument: str) -> Any:
        """Resolve the context of an argument.

        Args:
            argument: A string representing the argument.

        Returns:
            The resolved context of the argument.

        Raises:
            AttributeError: If the attribute does not exist in the context.
        """
        first, *keys = argument.split(".")

        if (v := self.get(first, _empty)) is _empty:
            raise KeyError(f"`{self.context}` does not contains `{first}` key")

        for i in keys:
            v = v[i] if isinstance(v, Mapping) else getattr(v, i)
        return v

    def __getattr__(self, __name: str) -> Any:
        """This is a function that is part of a class. It is used to get an attribute value using the `__getattr__` method.

        Args:
            __name: The name of the attribute to get.

        Returns:
            The value of the attribute.
        """
        return self.get(__name)

    @property
    def context(self) -> AnyDict:
        return {
            **self._global_context,
            **{i: j.get() for i, j in self._scope_context.items()},
        }

    @contextmanager
    def scope(self, key: str, value: Any) -> Iterator[None]:
        """Sets a local variable and yields control to the caller. After the caller is done, the local variable is reset.

        Args:
            key: The key of the local variable
            value: The value to set the local variable to

        Yields:
            None

        Returns:
            An iterator that yields None
        """
        token = self.set_local(key, value)
        try:
            yield
        finally:
            self.reset_local(key, token)


context: ContextRepo = ContextRepo()

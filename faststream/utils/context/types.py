from inspect import Parameter
from typing import Any, Callable, Optional

from fast_depends.library import CustomField

from faststream.types import AnyDict
from faststream.utils.context.repository import context


class Context(CustomField):
    """A class to represent a context.

    Attributes:
        param_name : name of the parameter

    Methods:
        __init__ : constructor method
        use : method to use the context
    """

    param_name: str

    def __init__(
        self,
        real_name: str = "",
        *,
        default: Any = Parameter.empty,
        initial: Optional[Callable[..., Any]] = None,
        cast: bool = False,
        prefix: str = "",
    ) -> None:
        """Initialize the object.

        Args:
            real_name: The real name of the object.
            default: The default value of the object.
            initial: The initial value builder.
            cast: Whether to cast the object.
            prefix: The prefix to be added to the name of the object.

        Raises:
            TypeError: If the default value is not provided.
        """
        self.name = real_name
        self.default = default
        self.prefix = prefix
        self.initial = initial
        super().__init__(
            cast=cast,
            required=(default is Parameter.empty),
        )

    def use(self, /, **kwargs: Any) -> AnyDict:
        """Use the given keyword arguments.

        Args:
            **kwargs: Keyword arguments to be used

        Returns:
            A dictionary containing the updated keyword arguments

        Raises:
            KeyError: If the parameter name is not found in the keyword arguments
            AttributeError: If the parameter name is not a valid attribute
        """
        name = f"{self.prefix}{self.name or self.param_name}"

        if (
            v := resolve_context_by_name(
                name=name,
                default=self.default,
                initial=self.initial,
            )
        ) is not Parameter.empty:
            kwargs[self.param_name] = v

        return kwargs


def resolve_context_by_name(
    name: str,
    default: Any,
    initial: Optional[Callable[..., Any]],
) -> Any:
    value: Any = Parameter.empty

    try:
        value = context.resolve(name)

    except (KeyError, AttributeError):
        if default is not Parameter.empty:
            value = default

        elif initial is not None:
            value = initial()
            context.set_global(name, value)

    return value

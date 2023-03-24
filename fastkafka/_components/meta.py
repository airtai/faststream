# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/095_Fastcore_Meta_Deps.ipynb.

# %% auto 0
__all__ = ['F', 'TorF', 'combine_params', 'delegates', 'use_parameters_of', 'filter_using_signature', 'export']

# %% ../../nbs/095_Fastcore_Meta_Deps.ipynb 1
import inspect
from types import FunctionType
from typing import *
from functools import wraps

import docstring_parser

# %% ../../nbs/095_Fastcore_Meta_Deps.ipynb 5
F = TypeVar("F", bound=Callable[..., Any])

# %% ../../nbs/095_Fastcore_Meta_Deps.ipynb 6
def _delegates_without_docs(
    to: Optional[FunctionType] = None,  # Delegatee
    keep: bool = False,  # Keep `kwargs` in decorated function?
    but: Optional[List[str]] = None,
) -> FunctionType:  # Exclude these parameters from signature
    "Decorator: replace `**kwargs` in signature with params from `to`"
    if but is None:
        but = []

    def _f(f: FunctionType) -> Callable[[FunctionType], FunctionType]:
        if to is None:
            to_f, from_f = f.__base__.__init__, f.__init__
        else:
            to_f, from_f = to.__init__ if isinstance(to, type) else to, f
        from_f = getattr(from_f, "__func__", from_f)
        to_f = getattr(to_f, "__func__", to_f)
        if hasattr(from_f, "__delwrap__"):
            return f
        sig = inspect.signature(from_f)
        sigd = dict(sig.parameters)
        k = sigd.pop("kwargs")
        s2 = {
            k: v.replace(kind=inspect.Parameter.KEYWORD_ONLY)
            for k, v in inspect.signature(to_f).parameters.items()
            if v.default != inspect.Parameter.empty and k not in sigd and k not in but
        }
        anno = {
            k: v
            for k, v in getattr(to_f, "__annotations__", {}).items()
            if k not in sigd and k not in but
        }
        sigd.update(s2)
        if keep:
            sigd["kwargs"] = k
        else:
            from_f.__delwrap__ = to_f
        from_f.__signature__ = sig.replace(parameters=sigd.values())
        if hasattr(from_f, "__annotations__"):
            from_f.__annotations__.update(anno)
        return f

    return _f

# %% ../../nbs/095_Fastcore_Meta_Deps.ipynb 16
def _format_args(xs: List[docstring_parser.DocstringParam]) -> str:
    return "\nArgs:\n - " + "\n - ".join(
        [f"{x.arg_name} ({x.type_name}): {x.description}" for x in xs]
    )


def combine_params(f: F, o: Union[Type, Callable[..., Any]]) -> F:
    """Combines docstring arguments of a function and another object or function

    Args:
        f: destination functions where combined arguments will end up
        o: source function from which arguments are taken from

    Returns:
        Function f with augumented docstring including arguments from both functions/objects
    """
    src_params = docstring_parser.parse_from_object(o).params
    #     logger.info(f"combine_params(): source:{_format_args(src_params)}")
    docs = docstring_parser.parse_from_object(f)
    #     logger.info(f"combine_params(): destination:{_format_args(docs.params)}")
    dst_params_names = [p.arg_name for p in docs.params]

    combined_params = docs.params + [
        x for x in src_params if not x.arg_name in dst_params_names
    ]
    #     logger.info(f"combine_params(): combined:{_format_args(combined_params)}")

    docs.meta = [
        x for x in docs.meta if not isinstance(x, docstring_parser.DocstringParam)
    ] + combined_params  # type: ignore

    f.__doc__ = docstring_parser.compose(
        docs, style=docstring_parser.DocstringStyle.GOOGLE
    )
    return f

# %% ../../nbs/095_Fastcore_Meta_Deps.ipynb 18
def delegates(
    o: Union[Type, Callable[..., Any]],
    keep: bool = False,
    but: Optional[List[str]] = None,
) -> Callable[[F], F]:
    """Delegates keyword agruments from o to the function the decorator is applied to

    Args:
        o: object (class or function) with default kwargs
        keep: Keep `kwargs` in decorated function?
        but: argument names not to include
    """

    def _inner(f: F, keep: bool = keep, but: Optional[List[str]] = but) -> F:
        def _combine_params(o: Union[Type, Callable[..., Any]]) -> Callable[[F], F]:
            def __combine_params(f: F, o: Union[Type, Callable[..., Any]] = o) -> F:
                return combine_params(f=f, o=o)

            return __combine_params

        @_combine_params(o)
        @_delegates_without_docs(o, keep=keep, but=but)  # type: ignore
        @wraps(f)
        def _f(*args: Any, **kwargs: Any) -> Any:
            return f(*args, **kwargs)

        return _f

    return _inner

# %% ../../nbs/095_Fastcore_Meta_Deps.ipynb 35
def use_parameters_of(
    o: Union[Type, Callable[..., Any]], **kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    """Restrict parameters passwed as keyword arguments to parameters from the signature of ``o``

    Args:
        o: object or callable which signature is used for restricting keyword arguments
        kwargs: keyword arguments

    Returns:
        restricted keyword arguments

    """
    allowed_keys = set(inspect.signature(o).parameters.keys())
    return {k: v for k, v in kwargs.items() if k in allowed_keys}

# %% ../../nbs/095_Fastcore_Meta_Deps.ipynb 37
def filter_using_signature(f: Callable, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """todo: write docs"""
    param_names = list(inspect.signature(f).parameters.keys())
    return {k: v for k, v in kwargs.items() if k in param_names}

# %% ../../nbs/095_Fastcore_Meta_Deps.ipynb 39
TorF = TypeVar("TorF", Type, Callable[..., Any])


def export(module_name: str) -> Callable[[TorF], TorF]:
    def _inner(o: TorF, module_name: str = module_name) -> TorF:
        o.__module__ = module_name
        return o

    return _inner

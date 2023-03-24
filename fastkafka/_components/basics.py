# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/096_Fastcore_Basics_Deps.ipynb.

# %% auto 0
__all__ = ['patch']

# %% ../../nbs/096_Fastcore_Basics_Deps.ipynb 1
import builtins
import copy as cp
import functools
import types

from types import FunctionType, MethodType, UnionType
from typing import Union
from functools import partial

# %% ../../nbs/096_Fastcore_Basics_Deps.ipynb 4
def test_eq(a, b):
    "`test` that `a==b`"
    if a != b:
        raise ValueError(f"{a} != {b}")

# %% ../../nbs/096_Fastcore_Basics_Deps.ipynb 6
def copy_func(f):
    "Copy a non-builtin function (NB `copy.copy` does not work for this)"
    if not isinstance(f, FunctionType):
        return cp.copy(f)
    fn = FunctionType(
        f.__code__, f.__globals__, f.__name__, f.__defaults__, f.__closure__
    )
    fn.__kwdefaults__ = f.__kwdefaults__
    fn.__dict__.update(f.__dict__)
    fn.__annotations__.update(f.__annotations__)
    fn.__qualname__ = f.__qualname__
    return fn

# %% ../../nbs/096_Fastcore_Basics_Deps.ipynb 12
def patch_to(cls, as_prop=False, cls_method=False):
    "Decorator: add `f` to `cls`"
    if not isinstance(cls, (tuple, list)):
        cls = (cls,)

    def _inner(f):
        for c_ in cls:
            nf = copy_func(f)
            nm = f.__name__
            # `functools.update_wrapper` when passing patched function to `Pipeline`, so we do it manually
            for o in functools.WRAPPER_ASSIGNMENTS:
                setattr(nf, o, getattr(f, o))
            nf.__qualname__ = f"{c_.__name__}.{nm}"
            if cls_method:
                setattr(c_, nm, MethodType(nf, c_))
            else:
                setattr(c_, nm, property(nf) if as_prop else nf)
        # Avoid clobbering existing functions
        existing_func = globals().get(nm, builtins.__dict__.get(nm, None))
        return existing_func

    return _inner

# %% ../../nbs/096_Fastcore_Basics_Deps.ipynb 23
def eval_type(t, glb, loc):
    "`eval` a type or collection of types, if needed, for annotations in py3.10+"
    if isinstance(t, str):
        if "|" in t:
            return Union[eval_type(tuple(t.split("|")), glb, loc)]
        return eval(t, glb, loc)
    if isinstance(t, (tuple, list)):
        return type(t)([eval_type(c, glb, loc) for c in t])
    return t


def union2tuple(t):
    if getattr(t, "__origin__", None) is Union or (
        UnionType and isinstance(t, UnionType)
    ):
        return t.__args__
    return t


def get_annotations_ex(obj, *, globals=None, locals=None):
    "Backport of py3.10 `get_annotations` that returns globals/locals"
    if isinstance(obj, type):
        obj_dict = getattr(obj, "__dict__", None)
        if obj_dict and hasattr(obj_dict, "get"):
            ann = obj_dict.get("__annotations__", None)
            if isinstance(ann, types.GetSetDescriptorType):
                ann = None
        else:
            ann = None

        obj_globals = None
        module_name = getattr(obj, "__module__", None)
        if module_name:
            module = sys.modules.get(module_name, None)
            if module:
                obj_globals = getattr(module, "__dict__", None)
        obj_locals = dict(vars(obj))
        unwrap = obj
    elif isinstance(obj, types.ModuleType):
        ann = getattr(obj, "__annotations__", None)
        obj_globals = getattr(obj, "__dict__")
        obj_locals, unwrap = None, None
    elif callable(obj):
        ann = getattr(obj, "__annotations__", None)
        obj_globals = getattr(obj, "__globals__", None)
        obj_locals, unwrap = None, obj
    else:
        raise TypeError(f"{obj!r} is not a module, class, or callable.")

    if ann is None:
        ann = {}
    if not isinstance(ann, dict):
        raise ValueError(f"{obj!r}.__annotations__ is neither a dict nor None")
    if not ann:
        ann = {}

    if unwrap is not None:
        while True:
            if hasattr(unwrap, "__wrapped__"):
                unwrap = unwrap.__wrapped__
                continue
            if isinstance(unwrap, functools.partial):
                unwrap = unwrap.func
                continue
            break
        if hasattr(unwrap, "__globals__"):
            obj_globals = unwrap.__globals__

    if globals is None:
        globals = obj_globals
    if locals is None:
        locals = obj_locals

    return dict(ann), globals, locals

# %% ../../nbs/096_Fastcore_Basics_Deps.ipynb 24
def patch(f=None, *, as_prop=False, cls_method=False):
    "Decorator: add `f` to the first parameter's class (based on f's type annotations)"
    if f is None:
        return partial(patch, as_prop=as_prop, cls_method=cls_method)
    ann, glb, loc = get_annotations_ex(f)
    cls = union2tuple(
        eval_type(ann.pop("cls") if cls_method else next(iter(ann.values())), glb, loc)
    )
    return patch_to(cls, as_prop=as_prop, cls_method=cls_method)(f)

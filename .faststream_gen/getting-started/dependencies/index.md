---
nested: A nested dependency is called here
---

# Dependencies

**FastStream** uses the secondary library [**FastDepends**](https://lancetnik.github.io/FastDepends/){.external-link target="_blank"} for dependency management.
This dependency system is literally borrowed from **FastAPI**, so if you know how to work with this framework, you know how to work with dependencies in **FastStream**.

You can go to the [**FastDepends**](https://lancetnik.github.io/FastDepends/){.external-link target="_blank"} documentation if you want to get more details, however, the key points and **additions** will be covered here.

## Type casting

The key function in the dependency management and type conversion system in **FastStream** is the decorator `#!python @apply_types` (`#!python @inject` in **FastDepends**).

By default, it applies to all event handlers, unless you disabled the same option at a broker creation.

{! includes/getting_started/dependencies/1.md !}

!!! warning
    By setting the `apply_types=False` flag, you disable not only type casting, but also `Depends` and `Context`.

This flag can be useful if you are using **FastStream** within another framework and you do not need to use
a native dependency system.

## Dependency Injection

To implement dependencies in **FastStream**, a special class **Depends** is used

{! includes/getting_started/dependencies/2.md !}

**The first step**: we need to declare a dependency - it can be any `Callable` object.

??? note "Callable"
    "Callable" is an object that can be "called". It can be a function, a class, or a class method.

    In other words: if you can write such code `my_object()` - `my_object` will be `Callable`

{! includes/getting_started/dependencies/3.md !}

**Second step**: Declare which dependencies you need using `Depends`

{! includes/getting_started/dependencies/4.md !}

**The last step**: Just use the result of executing your dependency!

It's easy, isn't it?

!!! tip "Auto `#!python @apply_types`"
    In the code above, we didn't use this decorator for our dependencies. However, it still applies
    to all functions used as dependencies. Keep this in your mind.

## Top-level dependencies

If you don't need a dependency result you can use the following code:

```python
@broker.subscriber("test")
def method(_ = Depends(...)): ...
```

But, using a special `subscriber` parameter is much suitable:

```python
@broker.subscriber("test", dependencies=[Depends(...)])
def method(): ...
```

Also, you are able to declare broker-level dependencies: they will be applied to all brokers' handlers.

```python
broker = RabbitBroker(dependencies=[Depends(...)])
```

## Nested dependencies

Dependencies can also contain other dependencies. This works in a very predictable way: just declare
`Depends` in the dependent function.

{% import 'getting_started/dependencies/5.md' as includes with context %}
{{ includes }}

!!! Tip "Caching"
    In the example above, the `another_dependency` function will be called at **ONCE!**.
    **FastDepends** caches all dependency execution results within **ONE** `#!python @apply_types` call stack.
    This means that all nested dependencies will receive the cached result of dependency execution.
    But, between different calls of the main function, these results will be different.

    To prevent this behavior, just use `#!python Depends(..., cache=False)`. In this case, the dependency will be used for each function
    in the call stack where it is used.

## Use with regular functions

You can use the decorator `#!python @apply_types` not only together with your `#!python @broker.subscriber(...)`, but also with the usual functions: both synchronous and asynchronous.

=== "Sync"
    ```python hl_lines="3-4" linenums="1"
from faststream import Depends, apply_types

def simple_dependency(a: int, b: int = 3):
    return a + b

@apply_types
def method(a: int, d: int = Depends(simple_dependency)):
    return a + d

assert method("1") == 5
    ```

=== "Async"
    ```python hl_lines="4-5 7-8" linenums="1"
import asyncio
from faststream import Depends, apply_types

async def simple_dependency(a: int, b: int = 3):
    return a + b

def another_dependency(a: int):
    return a

@apply_types
async def method(
    a: int,
    b: int = Depends(simple_dependency),
    c: int = Depends(another_dependency),
):
    return a + b + c

assert asyncio.run(method("1")) == 6
    ```

    !!! tip "Be careful"
        In asynchronous code, you can use both synchronous and asynchronous dependencies.
        But in synchronous code, only synchronous dependencies are available to you.

## Casting dependency types

**FastDepends**, used by **FastStream**, also gives the type `return`. This means that the value returned by the dependency will be
be cast to the type twice: as `return` these are dependencies and as the input argument of the main function. This does not incur additional costs if
these types have the same annotation. Just keep it in mind. Or not... Anyway, I've warned you.

```python linenums="1"
from faststream import Depends, apply_types

def simple_dependency(a: int, b: int = 3) -> str:
    return a + b  # 'return' is cast to `str` for the first time

@inject
def method(a: int, d: int = Depends(simple_dependency)):
    # 'd' is cast to `int` for the second time
    return a + d

assert method("1") == 5
```

Also, the result of executing the dependency is cached. If you use this dependency in `N` functions,
this cached result will be converted to type `N` times (at the input to the function being used).

To avoid problems with this, use [mypy](https://www.mypy-lang.org){.external-link target="_blank"} or just be careful with the annotation
of types in your project.

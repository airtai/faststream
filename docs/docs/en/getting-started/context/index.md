# Application Context

**FastStreams** has its own Dependency Injection container - **Context**, used to store application runtime objects and variables.

With this container, you can access both application scope and message processing scope objects. This functionality is similar to [`Depends`](../dependencies/index.md){.internal-link} usage.

{!> includes/getting_started/context/base.md !}

But, with the [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated){.external-docs target="_blank"} Python feature usage, it is much closer to `#!python @pytest.fixture`.

{!> includes/getting_started/context/annotated.md !}

## Usages

By default, the context is available in the same place as `Depends`:

* at lifespan hooks
* message subscribers
* nested dependencies

!!! tip
    Fields obtained from the `Context` are editable, so editing them in a function means editing them everywhere.

## Compatibility with Regular Functions

To use context in other functions, use the `#!python @apply_types` decorator. In this case, the context of the called function will correspond to the context of the event handler from which it was called.

```python linenums="1" hl_lines="6 9-10"
{!> docs_src/getting_started/context/nested.py [ln:1,9-16] !}
```

In the example above, we did not pass the `logger` function at calling it; it was placed outside of context.

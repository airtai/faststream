# Application Context

**FastStreams** has it's own Dependency Injection container - **Context**, using to store application runtime object and variables.

With this container you are able to get access to application scope or message processing scope objects both. This functionality is pretty close to [`Depends`](../dependencies/index.md){.internal-link} usage.

{!> includes/getting_started/context/base.md !}

But, with the [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated){.external-docs target="_blank"} python feature usage it is much closer to `#!python @pytest.fixture`.

{!> includes/getting_started/context/annotated.md !}

## Usages

By default, the context is available in the same place as `Depends`:

* at lifespan hooks
* message subscribers
* nested dependencies

!!! tip
    Fields getting from the `Context` are editable, so editing them in the function, you are editing them everywhere.

## Regular functions compatibility

<<<<<<< HEAD
To use context at other functions use the decorator `#!python @apply_types`. This case, the called function context will correspond to the context of the event handler from which it was called.
=======
To use context at other functions use the decorator `@apply_types`. In this case, the called function context will correspond to the context of the event handler from which it was called.
>>>>>>> 615edfb2ce0cb805ee6e4c799651bd8cc5cdbec5

```python linenums="1" hl_lines="6 8 11"
{!> docs_src/getting_started/context/nested.py !}
```

In the example above, we did not pass the `logger` function at calling, it was placed out of context.

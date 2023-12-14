---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Context Fields Declaration

You can also store your own objects in the `Context`.

## Global

To declare an application-level context field, you need to call the `context.set_global` method with with a key to indicate where the object will be placed in the context.

{! includes/getting_started/context/custom_global.md !}

Afterward, you can access your `secret` field in the usual way:

{! includes/getting_started/context/custom_global_2.md !}

In this case, the field becomes a global context field: it does not depend on the current message handler (unlike `message`)

To remove a field from the context use the `reset_global` method:

```python
context.reset_global("my_key")
```

## Local

To set a local context (available only within the message processing scope), use the context manager `scope`

{! includes/getting_started/context/custom_local.md !}

You can also set the context by yourself, and it will remain within the current call stack until you clear it.

{! includes/getting_started/context/manual_local.md !}

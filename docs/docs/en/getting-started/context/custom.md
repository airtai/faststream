# Context fields Declaration

Also, you are able to store your own objects in the `Context`.

## Global

To declare an Application-level context fields, you need to call the `context.set_global` method with an indication of the key by which the object will be placed in the context.

{!> includes/getting_started/context/custom_global.md !}

After you can get access to your `secret` fields in a regular way:

{!> includes/getting_started/context/custom_global_2.md !}

In this case, the field becomes a global context field: it does not depend on the current message handler (unlike `message`)

To remove a field from the context use the `reset_global` method

```python
context.reset_global("my_key")
```

## Local

To set the local context (it will be available at the message processing scope), use the context manager `scope`

{!> includes/getting_started/context/custom_local.md !}

Also, you can set the context yourself: then it will act within the current call stack until you clear it.

{!> includes/getting_started/context/manual_local.md !}

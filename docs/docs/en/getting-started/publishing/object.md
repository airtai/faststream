---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Publisher Object

The Publisher Object provides a full-featured way to publish messages. It has an [**AsyncAPI**](../asyncapi/custom.md){.internal-link} representation and includes [testability](./test.md){.internal-link} features. This method creates a reusable Publisher object.

Additionally, this object can be used as a decorator. The order of Subscriber and Publisher decorators doesn't matter, but `#!python @publisher` can be used only with functions already decorated by a `#!python @broker.subscriber(...)`.

!!! note
    It uses the handler function's return type annotation to cast the function's return value before sending, so be accurate with it.

---

:material-checkbox-marked:{.checked_mark} ```AsyncAPI``` support

:material-checkbox-marked:{.checked_mark} Testing support

:material-checkbox-marked:{.checked_mark} Can be reused

:fontawesome-solid-triangle-exclamation:{.warning_mark} More verbose way

:fontawesome-solid-triangle-exclamation:{.warning_mark} The message will **always** be published

---

{! includes/getting_started/publishing/object/1.md !}

## Message Broadcasting

The decorator can be used multiple times with one function to broadcast the function's return:

```python hl_lines="1-2"
@publisher1
@publisher2
@broker.subscriber("in")
async def handle(msg) -> str:
    return "Response"
```

This way, you will send a copy of your return to all output topics.

!!! note
    Also, if this subscriber consumes a message with **RPC** mode, it sends a reply not only to the **RPC** channel but also to all publishers as well.

## Details

Additionally, `#!python @publisher` automatically sends a message with the same `correlation_id` as the incoming message. This way, you get the same `correlation_id` for the entire message pipeline process across all services, allowing you to collect a trace.

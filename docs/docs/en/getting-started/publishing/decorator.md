---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Publisher Decorator

The second easiest way to publish messages is by using the Publisher Decorator. This method has an [**AsyncAPI**](../asyncapi/custom.md){.internal-link} representation and is suitable for quickly creating applications. However, it doesn't provide all testing features.

It creates a structured DataPipeline unit with an input and output. The order of Subscriber and Publisher decorators doesn't matter, but `#!python @broker.publisher(...)` can be used only with functions already decorated by a `#!python @broker.subscriber(...)`.

!!! note
    It uses the handler function's return type annotation to cast the function's return value before sending, so be accurate with it.

---

:material-checkbox-marked:{.checked_mark} Easy to use  

:material-checkbox-marked:{.checked_mark} Availability from ```Context```  

:fontawesome-solid-square-xmark:{.x_mark} ```AsyncAPI``` support  

:fontawesome-solid-square-xmark:{.x_mark} Testing support  

:fontawesome-solid-square-xmark:{.x_mark} Can be reused  

:fontawesome-solid-triangle-exclamation:{.warning_mark} The message will **always** be published  

---

{! includes/getting_started/publishing/decorator/1.md !}

## Message Broadcasting

The decorator can be used multiple times with one function to broadcast the function's return:

```python hl_lines="2-3"
@broker.subscriber("in")
@broker.publisher("first-out")
@broker.publisher("second-out")
async def handle(msg) -> str:
    return "Response"
```

This way you will send a copy of your return to the all output topics.

!!! note
    Also, if this subscriber consumes a message with **RPC** mode, it sends a reply not only to the **RPC** channel but also to all publishers as well.

## Details

Additionally, `#!python @broker.publisher(...)` automatically sends a message with the same `correlation_id` as the incoming message. This way, you get the same `correlation_id` for the entire message pipeline process across all services, allowing you to collect a trace.

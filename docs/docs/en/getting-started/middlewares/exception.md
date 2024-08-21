---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Exception Middleware

Sometimes you need to register exception processors at top level of your application instead of each message handler.

For this case, **FastStream** has a special `ExceptionMiddleware`. You just need to create it, register handlers and add to broker / router / subscribers you want (as a [regular middleware](index.md){.internal-link}).

```python linenums="1"
from faststream. import ExceptionMiddleware

exception_middleware = ExceptionMiddleware()

Broker(middlewares=[exception_middleware])
```

This middleware can be used in a two ways we discuss further.

## General Exceptions processing

The first way - general exceptions processing. It is a default case, that can be used to log exceptions correctly / clear / etc. This type of handlers processes all sources of errors: message handler, parser/decoder, another middlewares, publishing. But, it **can't be used to publish** something as a default value to request.

You can register such handlers in a two ways:

1. By middleware `#!python @add_handler(...)` decorator:
    ```python linenums="1" hl_lines="3"
    exc_middleware = ExceptionMiddleware()

    @exc_middleware.add_handler(Exception)
    def error_handler(exc: Exception) -> None:
        print(repr(exc))
    ```

2. By middleware `handlers` initial option
    ```python  linenums="1" hl_lines="5-7"
    def error_handler(exc: Exception) -> None:
        print(repr(exc))

    exc_middleware = ExceptionMiddleware(
        handlers={
            Exception: error_handler
        }
    )
    ```

## Publishing Exceptions Handlers

The first way to process messages - fallback to default result, that should be published at error. Such handlers are able to process errors in your message handler (or serialization) function only.

They can be registered the same two ways as a previous one, but with a little difference:

1. By middleware `#!python @add_handler(..., publish=True)` decorator:
    ```python linenums="1" hl_lines="3"
    exc_middleware = ExceptionMiddleware()

    @exc_middleware.add_handler(Exception, publish=True)
    def error_handler(exc: Exception) -> str:
        print(repr(exc))
        return "error occurred"
    ```

2. By middleware `publish_handlers` initial option
    ```python  linenums="1" hl_lines="6-8"
    def error_handler(exc: Exception) -> str:
        print(repr(exc))
        return "error occurred"

    exc_middleware = ExceptionMiddleware(
        publish_handlers={
            Exception: error_handler
        }
    )
    ```

## Handlers requirements

Your registered exception handlers are also wrapped by **FastDepends** serialization mechanism, so they can be

* sync/async both
* ask for [Context](../context/index.md){.internal-link} feature

As a regular message handler does.

As an example - you can get a consumed message in your handler in a regular way:

```python linenums="1" hl_lines="8"
from faststream import ExceptionMiddleware, Context

exc_middleware = ExceptionMiddleware()

@exc_middleware.add_handler(Exception, publish=True)
def base_exc_handler(
    exc: Exception,
    message = Context(),
) -> str:
    print(exc, msg)
    return "default"
```
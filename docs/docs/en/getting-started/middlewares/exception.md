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
Base usage

```python linenums="1"
from pydantic import ValidationError

from faststream.broker.middlewares import ExceptionMiddleware

exception_middleware = ExceptionMiddleware()


@exception_middleware.add_handler(ZeroDivisionError)
async def handle_type_exception(exc: ZeroDivisionError): ...


@exception_middleware.add_handler(ValidationError)
async def handle_validation_error(exc: ValidationError): ...


Broker( middlewares=(exception_middleware,))
```


```python linenums="1"
from pydantic import ValidationError

from faststream.broker.middlewares import ExceptionMiddleware


async def handle_zero_division_error(exc: ZeroDivisionError): ...


async def handle_validation_error(exc: ValidationError): ...

exception_middleware = ExceptionMiddleware(
    {
        ZeroDivisionError: handle_zero_division_error,
        ValidationError: handle_validation_error,
    }
)


Broker(middlewares=(exception_middleware,))
```
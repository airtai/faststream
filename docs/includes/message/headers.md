## Headers Access

Sure, you can get access to a raw message and get headers dict itself, but more often you just need a single header field. So, you can easely access to it usign the `Context`

```python hl_lines="6"
from faststream import Context

@broker.subscriber("test")
async def base_handler(
    body: str,
    user: str = Context("message.headers.user"),
):
    ...
```

But using special `Header` class is much comfortable (also it validates header value by pydantic). It works the same way with `Context`. To be honest, it just a shorcut to `Context` with a default setup. So, you are already known how to use it:

```python hl_lines="6"
from faststream import Header

@broker.subscriber("test")
async def base_handler(
    body: str,
    user: str = Header(),
):
    ...
```
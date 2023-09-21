# **FastAPI** Plugin

## Handling messages

**FastStream** can be used as a part of **FastAPI**.

Just import a **StreamRouter** you need and declare the message handler in the same way as with a regular **FastStream** application.

!!! tip
    When used in this way, **FastStream** does not use its own dependency system but integrates into **FastAPI**.
    That is, you can use `Depends`, `BackgroundTasks` and other original **FastAPI** features as if it were a regular HTTP endpoint, but you can't use `faststream.Context` and `faststream.Depends`.

    Note that the code below uses `fastapi.Depends`, not `faststream.Depends`.

{! includes/getting_started/integrations/fastapi/1.md !}

When processing a message from a broker, the entire message body is placed simultaneously in both the `body` and `path` request parameters. You can access them in any way convenient for you. The message header is placed in `headers`.

Also, this router can be fully used as an `HttpRouter` (of which it is the inheritor). So, you can
use it to declare any `get`, `post`, `put` and other HTTP methods. For example, this is done at **line 19**.

!!! warning
    If your **ASGI** server does not support installing **state** inside **lifespan**, you can disable this behavior as follows:

    ```python
    router = StreamRouter(..., setup_state=False)
    ```

    However, after that, you will not be able to access the broker from your application's **state** (but it is still available as the `router.broker`).

## Accessing the Broker Object

Inside each router, there is a broker. You can easily access it if you need to send a message to MQ:

{! includes/getting_started/integrations/fastapi/2.md !}

You can use the following `Depends` to access the broker if you want to use it at different parts of your program:

{! includes/getting_started/integrations/fastapi/3.md !}

Or you can access the broker from a **FastAPI** application state:

```python
from fastapi import Request

@app.get("/")
def main(request: Request):
    broker = request.state.broker
```

## `@after_startup`

The `FastStream` application has the `#!python @after_startup` hook, which allows you to perform operations with your message broker after the connection is established. This can be extremely convenient for managing your brokers' objects and/or sending messages. This hook is also available for your **FastAPI StreamRouter**

{! includes/getting_started/integrations/fastapi/4.md !}

## Documentation

When using **FastStream** as a router for **FastAPI**, the framework automatically registers endpoints for hosting **AsyncAPI** documentation into your application with the following default values:

{! includes/getting_started/integrations/fastapi/5.md !}

This way, you will have three routes to interact with your application's **AsyncAPI** schema:

* `/asyncapi` - the same as the [CLI created page](../../../getting-started/asyncapi/hosting.md){.internal-link}
* `/asyncapi.json` - download the **JSON** schema representation
* `/asyncapi.yaml` - download the **YAML** schema representation

## Testing

To test your **FastAPI StreamRouter**, you can still use it with the *TestClient*:

{! includes/getting_started/integrations/fastapi/6.md !}

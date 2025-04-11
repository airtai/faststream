---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Serving the AsyncAPI Documentation

## Built-in ASGI for FastStream Applications

FastStream includes a lightweight ASGI server that you can use to serve both your application and AsyncAPI documentation.

```python linenums="1"
import uvicorn
from faststream import FastStream
from faststream.kafka import KafkaBroker
from pydantic import BaseModel, Field, NonNegativeFloat

broker = KafkaBroker("localhost:9092")


class DataBasic(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )

@broker.subscriber('topic')
async def my_handler(msg: DataBasic) -> None:
    print(msg.data + 1.0)


app = FastStream(broker).as_asgi(
    asyncapi_path="/docs/asyncapi",
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

After running the script, AsyncAPI docs will be available at: <http://localhost:8000/docs/asyncapi>

## Integration with different http framework (FastAPI)

FastStream provides two robust approaches to combine your message broker documentation with FastAPI's web framework.
You may choose the method that best fits with your application architecture.

=== "Option 1"
    ```python linenums="1"
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel, Field, NonNegativeFloat

    from faststream import FastStream
    from faststream.asyncapi import get_asyncapi_html
    from faststream.asyncapi.generate import get_app_schema
    from faststream.kafka import KafkaBroker

    broker = KafkaBroker("localhost:9092")
    app = FastAPI(
        on_startup=[broker.start],
        on_shutdown=[broker.close],
    )


    class DataBasic(BaseModel):
        data: NonNegativeFloat = Field(
            ..., examples=[0.5], description="Float data example"
        )


    @broker.subscriber('topic')
    async def my_handler(msg: DataBasic) -> None:
        print(msg.data + 1.0)


    @app.get('/')
    async def index() -> str:
        return "index page"


    @app.get('/docs/asyncapi')
    async def asyncapi() -> HTMLResponse:
        schema = get_app_schema(FastStream(broker))
        return HTMLResponse(get_asyncapi_html(schema))


    if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000)

    ```

=== "Option 2"
    ```python linenums="1"
    import uvicorn
    from fastapi import FastAPI
    from pydantic import BaseModel, Field, NonNegativeFloat

    from faststream import FastStream
    from faststream.asgi import make_asyncapi_asgi
    from faststream.kafka import KafkaBroker

    broker = KafkaBroker("localhost:9092")
    fs_app = FastStream(broker)
    app = FastAPI(
        on_startup=[broker.start],
        on_shutdown=[broker.close]
    )


    class DataBasic(BaseModel):
        data: NonNegativeFloat = Field(
            ..., examples=[0.5], description="Float data example"
        )


    @broker.subscriber('topic')
    async def my_handler(msg: DataBasic) -> None:
        print(msg.data + 1.0)

    @app.get('/')
    async def index() -> str:
        return "index page"


    app.mount("/docs/asyncapi", make_asyncapi_asgi(fs_app))

    if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000)

    ```
After running the script docs will be available at:

* OpenAPI Docs: <http://localhost:8000/docs>
* AsyncAPI Docs: <http://localhost:8000/docs/asyncapi>

## Using CLI and http.server

FastStream provides a command to serve the AsyncAPI documentation.

!!! note
    This feature requires an Internet connection to obtain the **AsyncAPI HTML** via **CDN**.

```shell
{! docs_src/getting_started/asyncapi/serve.py [ln:17] !}
```

In the above command, we are providing the path in the format of `python_module:FastStream`. Alternatively, you can also specify `asyncapi.json` or `asyncapi.yaml` to serve the AsyncAPI documentation.

=== "JSON"
    ```shell
    {!> docs_src/getting_started/asyncapi/serve.py [ln:21] !}
    ```

=== "YAML"
    ```shell
    {!> docs_src/getting_started/asyncapi/serve.py [ln:25] !}
    ```

After running the command, it should serve the AsyncAPI documentation on port **8000** and display the following logs in the terminal.

```{.shell .no-copy}
INFO:     Started server process [2364992]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
```
{ data-search-exclude }

And you should be able to see the following page in your browser:

=== "Short"
    ![HTML-page](../../../assets/img/AsyncAPI-basic-html-short.png){ .on-glb loading=lazy }

=== "Expand"
    ![HTML-page](../../../assets/img/AsyncAPI-basic-html-full.png){ .on-glb loading=lazy }

!!! tip
    The command also offers options to serve the documentation on a different host and port.

## Customizing AsyncAPI Documentation

FastStream also provides query parameters to show and hide specific sections of AsyncAPI documentation.

You can use the following parameters control the visibility of relevant sections:

1. `sidebar`: Whether to include the sidebar. Default is true.
1. `info`: Whether to include the info section. Default is true.
1. `servers`: Whether to include the servers section. Default is true.
1. `operations`: Whether to include the operations section. Default is true.
1. `messages`: Whether to include the messages section. Default is true.
1. `schemas`: Whether to include the schemas section. Default is true.
1. `errors`: Whether to include the errors section. Default is true.
1. `expandMessageExamples`: Whether to expand message examples. Default is true.

For example, to hide the entire `Servers` section of the documentation, simply add `servers=false` as a query parameter, i.e., <http://localhost:8000?servers=false>. The resulting page would look like the image below:

![HTML-page](../../../assets/img/AsyncAPI-hidden-servers.png){ .on-glb loading=lazy }

Please use the above-listed query parameters to show and hide sections of the AsyncAPI documentation.

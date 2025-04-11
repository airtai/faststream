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

## Manual AsyncAPI Hosting

While the CLI is convenient for most cases, you may need to integrate AsyncAPI documentation into your existing application or customize the hosting behavior. FastStream provides public API functions for manual AsyncAPI hosting.

### Using the Public API

FastStream exposes two key functions in the `faststream.asyncapi` module:

```python
from faststream.asyncapi import get_app_schema, get_asyncapi_html
```

- `get_app_schema`: Generates the AsyncAPI schema from a FastStream application
- `get_asyncapi_html`: Converts the schema to HTML for browser viewing

Here's an example of how to use these functions:

```python
from contextlib import asynccontextmanager
import asyncio
from faststream import FastStream
from faststream.nats import NatsBroker
from faststream.asyncapi import get_app_schema, get_asyncapi_html
import http.server
import socketserver
from threading import Thread

# Create your FastStream application
broker = NatsBroker()
app = FastStream(broker)

# Add your subscribers and publishers
@broker.subscriber("test.subject")
async def handle_message(msg: str):
    return f"Processed: {msg}"

# Generate the AsyncAPI schema before starting the application
schema = get_app_schema(app)

# Convert the schema to HTML
html_content = get_asyncapi_html(
    schema=schema,
    title="My Custom API Docs",
    # Optional: customize display options
    sidebar=True,
    operations=True,
    messages=True,
    schemas=True,
)

# Create a simple HTTP server to serve the documentation
class AsyncAPIHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    # Make the server quieter by overriding log_message
    def log_message(self, format, *args):
        pass

# Start the HTTP server in a separate thread
def run_http_server():
    with socketserver.TCPServer(("localhost", 8000), AsyncAPIHandler) as httpd:
        print("AsyncAPI docs available at http://localhost:8000")
        httpd.serve_forever()

http_thread = Thread(target=run_http_server, daemon=True)
http_thread.start()

# Start the FastStream application
async def main():
    async with broker:
        # Start the broker
        await broker.start()
        print("FastStream application is running. Press Ctrl+C to stop.")
        
        try:
            # Keep the application running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
```

This example demonstrates:
1. Generating the AsyncAPI schema documentation
2. Converting it to HTML
3. Serving the HTML via a simple HTTP server in a separate thread
4. Running the FastStream application in the main thread

For a production environment, you might want to use a more robust web server like FastAPI, Starlette, or any other ASGI-compatible framework.

### Integration with ASGI Frameworks

For more advanced use cases, you may want to integrate AsyncAPI documentation with your existing ASGI application. FastStream provides built-in support for this via the `make_asyncapi_asgi` function.

For details and examples on how to mount AsyncAPI documentation in ASGI applications, refer to the [FastStream Object Reuse](../asgi/#faststream-object-reuse) section in the ASGI documentation.

Here's a simple example of how to integrate AsyncAPI documentation with FastAPI:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from faststream import FastStream
from faststream.nats import NatsBroker
from faststream.asgi import make_asyncapi_asgi

# Create a broker and FastStream application
broker = NatsBroker()

@broker.subscriber("test.subject")
async def handle_message(msg: str):
    return f"Processed: {msg}"

app_stream = FastStream(broker)

# Create a lifespan context manager for the FastAPI app
@asynccontextmanager
async def lifespan(app):
    # Start the broker
    async with broker:
        await broker.start()
        yield
        # Shutdown will be handled by the context manager

# Create a FastAPI application with the lifespan
app = FastAPI(lifespan=lifespan)

# Mount the AsyncAPI documentation at the /asyncapi path
app.mount("/asyncapi", make_asyncapi_asgi(app_stream))

# Add your FastAPI routes
@app.get("/")
async def root():
    return {"message": "Hello World"}
```

You can then run this application with any ASGI server:

```shell
uvicorn main:app
```

The AsyncAPI documentation will be available at `http://localhost:8000/asyncapi`.

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

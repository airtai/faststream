# Serving the AsyncAPI Documentation

FastStream provides a separate command to serve the AsyncAPI documentation.

``` shell
{!> docs_src/getting_started/asyncapi/serve.py[ln:17]!}
```

In the above command, we are providing the path in the format of `python_module:FastStream`. Alternatively, you can also specify `asyncapi.json` or `asyncapi.yaml` to serve the AsyncAPI documentation.

``` shell
{!> docs_src/getting_started/asyncapi/serve.py[ln:21]!}
# or
{!> docs_src/getting_started/asyncapi/serve.py[ln:25]!}
```

After running the command, it should serve AsyncAPI documentation on port **8000** and display the following logs in the terminal.

``` shell
INFO:     Started server process [2364992]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
```

And see the following page at your browser

=== "Short"
    ![HTML-page](/assets/img/AsyncAPI-basic-html-short.png){ loading=lazy }

=== "Expand"
    ![HTML-page](/assets/img/AsyncAPI-basic-html-full.png){ loading=lazy }

!!! tip
    The command also offers options to serve the documentation on a different host and port.

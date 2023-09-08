# Serving the AsyncAPI Documentation

FastStream provides a separate command to serve the AsyncAPI documentation.

``` shell
faststream docs serve basic:app
```

In the above command, we are providing the path in the format of `python_module:FastStream`. Alternatively, you can also specify `asyncapi.json` or `asyncapi.yaml` to serve the AsyncAPI documentation.

After running the command, it should serve AsyncAPI documentation on port 8000 and display the following logs in the terminal.

``` shell
INFO:     Started server process [2364992]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
```

The command also offers options to serve the documentation on a different port.

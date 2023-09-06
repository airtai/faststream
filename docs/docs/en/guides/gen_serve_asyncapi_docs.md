# How to Generate and Serve AsyncAPI Documentation

In this guide, let's explore how to generate and serve AsyncAPI documentation for our FastStream application.

## Writing the FastStream Application

Based on [tutorial](/#writing-app-code), here's an example Python application using FastStream that consumes data from a
topic, increments the value, and outputs the data to another topic.
Save it in a file called `basic.py`.

``` python
{!> docs_src/kafka/basic/basic.py!}
```

## Generating the AsyncAPI Specification

Now that we have a FastStream application, we can proceed with generating the AsyncAPI specification using a CLI command.

``` shell
{!> docs_src/kafka/basic/test_docs_cmd.py[ln:13]!}
```

The above command will generate the AsyncAPI specification and save it in a file called `asyncapi.json`.

If you prefer `yaml` instead of `json`, please run the following command to generate `asyncapi.yaml`.

``` shell
{!> docs_src/kafka/basic/test_docs_cmd.py[ln:17]!}
```

## Serving the AsyncAPI Documentation

FastStream provides a separate command to serve the AsyncAPI documentation.

``` shell
{!> docs_src/kafka/basic/test_docs_cmd.py[ln:21]!}
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

# How to Generate and Serve AsyncAPI Documentation

In this guide, let's explore how to generate and serve AsyncAPI documentation for our FastStream application.

## Writing the FastStream Application

Based on [tutorial]('../../../getting-started/index.md'), here's an example Python application using FastStream that consumes data from a
topic, increments the value, and outputs the data to another topic.
Save it in a file called `basic.py`.

``` python
{!> docs_src/kafka/basic/basic.py!}
```

## Generating the AsyncAPI Specification

Now that we have a FastStream application, we can proceed with generating the AsyncAPI specification using a CLI command.

``` shell
{!> docs_src/kafka/basic/test_docs_cmd.py[ln:9]!}
```

The above command will generate the AsyncAPI specification and save it in a file called `asyncapi.json`.

If you prefer `yaml` instead of `json`, please run the following command to generate `asyncapi.yaml`.

``` shell
{!> docs_src/kafka/basic/test_docs_cmd.py[ln:13]!}
```

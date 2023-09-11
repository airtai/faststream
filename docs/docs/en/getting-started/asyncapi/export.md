# How to Generate and Serve AsyncAPI Documentation

In this guide, let's explore how to generate and serve [**AsyncAPI**](https://www.asyncapi.com/){.external-link target="_blank"} documentation for our FastStream application.

## Writing the FastStream Application

Here's an example Python application using **FastStream** that consumes data from a
topic, increments the value, and outputs the data to another topic.
Save it in a file called `basic.py`.

``` python
{!> docs_src/kafka/basic/basic.py!}
```

## Generating the AsyncAPI Specification

Now that we have a FastStream application, we can proceed with generating the AsyncAPI specification using a CLI command.

``` shell
{!> docs_src/getting_started/asyncapi/serve.py[ln:9]!}
```

The above command will generate the AsyncAPI specification and save it in a file called `asyncapi.json`.

If you prefer `yaml` instead of `json`, please run the following command to generate `asyncapi.yaml`.

!!! note
    This case, please install dependency to work with **YAML** file format at first

    ``` shell
    pip install PyYAML
    ```

``` shell
{!> docs_src/getting_started/asyncapi/serve.py[ln:13]!}
```

# How to Generate and Serve AsyncAPI Documentation

In this guide, let's explore how to generate and serve [**AsyncAPI**](https://www.asyncapi.com/){.external-link target="_blank"} documentation for our FastStream application.

## Writing the FastStream Application

Here's an example Python application using **FastStream** that consumes data from a
topic, increments the value, and outputs the data to another topic.
Save it in a file called `basic.py`.

``` python
from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class DataBasic(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.publisher("output_data")
@broker.subscriber("input_data")
async def on_input_data(msg: DataBasic, logger: Logger) -> DataBasic:
    logger.info(msg)
    return DataBasic(data=msg.data + 1.0)
```

## Generating the AsyncAPI Specification

Now that we have a FastStream application, we can proceed with generating the AsyncAPI specification using a CLI command.

``` shell
faststream docs gen basic:app
```

The above command will generate the AsyncAPI specification and save it in a file called `asyncapi.json`.

If you prefer `yaml` instead of `json`, please run the following command to generate `asyncapi.yaml`.

!!! note
    This case, please install dependency to work with **YAML** file format at first

    ``` shell
    pip install PyYAML
    ```

``` shell
faststream docs gen --yaml basic:app
```

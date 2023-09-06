# How to Generate and Serve AsyncAPI Documentation

In this guide, let's explore how to generate and serve AsyncAPI documentation for our FastStream application.

## Writing the FastStream Application

Based on [tutorial](/#writing-app-code), here's an example Python application using FastStream that consumes data from a
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

``` shell
faststream docs gen --yaml basic:app
```

## Serving the AsyncAPI Documentation

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

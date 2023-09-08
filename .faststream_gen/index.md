---
hide:
  - navigation
  - footer
---

FastStream
================

<b>Effortless Event Stream integration for your services</b>

------------------------------------------------------------------------

![PyPI](https://img.shields.io/pypi/v/fastkafka.png) ![PyPI -
Downloads](https://img.shields.io/pypi/dm/fastkafka.png) ![PyPI - Python
Version](https://img.shields.io/pypi/pyversions/fastkafka.png)

![GitHub Workflow
Status](https://img.shields.io/github/actions/workflow/status/airtai/fastkafka/test.yaml)
![CodeQL](https://github.com/airtai/fastkafka//actions/workflows/codeql.yml/badge.svg)
![Dependency
Review](https://github.com/airtai/fastkafka//actions/workflows/dependency-review.yml/badge.svg)

![GitHub](https://img.shields.io/github/license/airtai/fastkafka.png)

------------------------------------------------------------------------

[FastStream](https://fastkafka.airt.ai/) is a powerful and easy-to-use Python
library for building asynchronous services that interact with Event streams
topics. Built on top of [Pydantic](https://docs.pydantic.dev/) and
[AsyncAPI](https://www.asyncapi.com/), FastStream simplifies the process
of writing producers and consumers for Message Queues, handling all the
parsing, networking, task scheduling and data generation automatically.
With FastStream, you can quickly prototype and develop high-performance
Event-based services with minimal code, making it an ideal choice for
developers looking to streamline their workflow and accelerate their
projects.

## Install

FastStream works on macOS, Linux, and most Unix-style operating systems.
You can install it with `pip` as usual:

``` sh
pip install faststream
```

## Writing app code

Here is an example python app using FastStream that consumes data from a
topic, increments the value, and outputs the data to another topic.

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

### Messages

FastStream uses [Pydantic](https://docs.pydantic.dev/) to parse input
JSON-encoded data into Python objects, making it easy to work with
structured data in your Kafka-based applications. Pydantic’s
[`BaseModel`](https://docs.pydantic.dev/usage/models/) class allows you
to define messages using a declarative syntax, making it easy to specify
the fields and types of your messages.

This example defines one message class for use in a FastStream
application, `Data`.

``` python hl_lines="1 7-10"
from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream, Logger
from faststream.kafka import KafkaBroker


class DataBasic(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )

# Code below omitted 👇
```

<details>
<summary>👀 Full file preview</summary>

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

</details>

These message class will be used to parse and validate incoming data
when consuming and to produce a JSON-encoded message when producing.
Using Pydantic’s BaseModel in combination with FastStream makes it easy
to work with structured data in your Event-based applications.

### Application

This example shows how to initialize a FastStream application.

It starts by initialising a `Broker` object with the address of the Message broker.

Next, an object of the `FastStream` class is created and a `Broker` object is passed to it.

``` python hl_lines="3 4"
# Code above omitted 👆

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

# Code below omitted 👇
```

<details>
<summary>👀 Full file preview</summary>

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

</details>

### Function decorators

FastStream brokers provide convenient function decorators `broker.subscriber`
and `@broker.publisher` to allow you to delegate the actual process of

- consuming and producing data to Event queues, and

- decoding and encoding JSON encoded messages

from user defined functions to the framework. The FastStream framework
delegates these jobs to AIOKafka and Pydantic libraries.

These decorators make it easy to specify the processing logic for your
consumers and producers, allowing you to focus on the core
business logic of your application without worrying about the underlying
integration.

This following example shows how to use the `@broker.subscriber` and
`@broker.publisher` decorators in a FastKafka application:

- The `@broker.subscriber` decorator is applied to the `on_input_data`
  function, which specifies that this function should be called whenever
  a message is received on the “input_data” Kafka topic. The
  `on_input_data` function takes a single argument which is expected to
  be an instance of the `Data` message class. Specifying the type
  of the single argument is instructing the Pydantic to use
  `InputData.parse_raw()` on the consumed message before passing it to
  the user defined function `on_input_data`.

- The `@broker.publisher` decorator is applied also to the `on_input_data` function,
  which specifies that this function should produce a message to the
  “output_data” topic whenever it is called. The `on_input_data`
  function takes the input data and creates a new
  `Data` message with incremented value and then returns it. The
  framework will call the `Data.json().encode("utf-8")` function
  on the returned value and produce it to the specified topic.

``` python hl_lines="17-21"
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

### Testing the service

The service can be tested using the `TestBroker` context managers which, by default, puts the Broker into "testing mode".

The Tester will redirect your `subscriber` and `publisher` decorated functions to the InMemory brokers so that you can quickly test your app without the need for a running broker and all its dependencies.

Using pytest, the test for our service would look like this:

``` python
import pytest

from faststream.kafka import TestKafkaBroker

from .basic import DataBasic, broker, on_input_data


@pytest.mark.asyncio
async def test_base_app():
    @broker.subscriber("output_data")
    async def on_output_data(msg: DataBasic):
        pass

    async with TestKafkaBroker(broker):
        await broker.publish(DataBasic(data=0.2), "input_data")

        on_input_data.mock.assert_called_once_with(dict(DataBasic(data=0.2)))

        on_output_data.mock.assert_called_once_with(dict(DataBasic(data=1.2)))
```

First we pass our broker to the `TestKafkaBroker`

``` python hl_lines="3 14"
import pytest

from faststream.kafka import TestKafkaBroker

from .basic import DataBasic, broker, on_input_data


@pytest.mark.asyncio
async def test_base_app():
    @broker.subscriber("output_data")
    async def on_output_data(msg: DataBasic):
        pass

    async with TestKafkaBroker(broker):
        await broker.publish(DataBasic(data=0.2), "input_data")

        on_input_data.mock.assert_called_once_with(dict(DataBasic(data=0.2)))

        on_output_data.mock.assert_called_once_with(dict(DataBasic(data=1.2)))
```

After passing the broker to the `TestKafkaBroker` we can publish an event to "input_data" and check if the tested broker produced a response as a reaction to it.

To check the response, we registered an additional `on_output_data` subscriber which will capture events on "output_data" topic.

``` python hl_lines="10-12 19"
import pytest

from faststream.kafka import TestKafkaBroker

from .basic import DataBasic, broker, on_input_data


@pytest.mark.asyncio
async def test_base_app():
    @broker.subscriber("output_data")
    async def on_output_data(msg: DataBasic):
        pass

    async with TestKafkaBroker(broker):
        await broker.publish(DataBasic(data=0.2), "input_data")

        on_input_data.mock.assert_called_once_with(dict(DataBasic(data=0.2)))

        on_output_data.mock.assert_called_once_with(dict(DataBasic(data=1.2)))
```

## Running the application

The application can be started using builtin FastStream CLI command.

First we will save our application code to `app.py` file. Here is the application code again:

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

To run the service, use the FastStream CLI command and pass the module (in this case, the file where the app implementation is located) and the app simbol to the command.

``` shell
faststream run basic:app
```

After running the command you should see the following output:

``` shell
INFO     - FastStream app starting...
INFO     - input_data |            - `OnInputData` waiting for messages
INFO     - FastStream app started successfully! To exit press CTRL+C
```

---
hide:
  - navigation
  - footer
---

FastStream
================

<b>Effortless event stream integration for your services</b>

------------------------------------------------------------------------

<a href="https://github.com/airtai/faststream/actions/workflows/test.yaml" target="_blank">
  <img src="https://github.com/airtai/faststream/actions/workflows/test.yaml/badge.svg?branch=main" alt="Test Passing"/>
</a>
<!-- <a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/airtai/faststream" target="_blank">
    <img src="https://coverage-badge.samuelcolvin.workers.dev/airtai/faststream.svg" alt="Coverage"> -->
</a>
<a href="https://pypi.org/project/faststream" target="_blank">
  <img src="https://img.shields.io/pypi/v/faststream?label=PyPI" alt="Package version">
</a>
<a href="https://www.pepy.tech/projects/faststream" target="_blank">
  <img src="https://static.pepy.tech/personalized-badge/faststream?period=month&units=international_system&left_color=grey&right_color=green&left_text=downloads/month" alt="Downloads"/>
</a>
<a href="https://pypi.org/project/faststream" target="_blank">
  <img src="https://img.shields.io/pypi/pyversions/faststream.svg" alt="Supported Python versions">
</a>
<a href="https://github.com/airtai/faststream/actions/workflows/codeql.yml" target="_blank">
  <img src="https://github.com/airtai/faststream/actions/workflows/codeql.yml/badge.svg" alt="CodeQL">
</a>
<a href="https://github.com/airtai/faststream/actions/workflows/dependency-review.yaml" target="_blank">
  <img src="https://github.com/airtai/faststream/actions/workflows/dependency-review.yaml/badge.svg" alt="Dependency Review">
</a>
<a href="https://github.com/airtai/faststream" target="_blank">
  <img src="https://img.shields.io/github/license/airtai/faststream.png" alt="Github">
</a>

------------------------------------------------------------------------

[FastStream](https://faststream.airt.ai/) is a powerful and easy-to-use Python
library for building asynchronous services that interact with event streams.
 Built on top of [Pydantic](https://docs.pydantic.dev/) and
[AsyncAPI](https://www.asyncapi.com/), FastStream simplifies the process
of writing producers and consumers for message queues, handling all the
parsing, networking, task scheduling and data generation automatically.
With FastStream, you can quickly prototype and develop high-performance
event-based services with minimal code, making it an ideal choice for
developers looking to streamline their workflow and accelerate their
projects.

## History

FastStream is a new package based on the ideas and experiences gained from
[FastKafka](https://github.com/airtai/fastkafka) and
[Propan](https://github.com/lancetnik/propan). By joining our forces, we
 picked up the best from both packages and created the unified way to write
  services capable of processing streamed data regradless of the underliying protocol.

  We'll continue to maintain both packages, but new development will be in this
  project. If you are starting a new service, this package is the recommended way to do it.


#### ⭐⭐⭐ Stay in touch ⭐⭐⭐

Please show your support and stay in touch by:

- giving our [GitHub repository](https://github.com/airtai/faststream/) a
  star, and

- joining our [Discord server](https://discord.gg/CJWmYpyFbc).

Your support helps us to stay in touch with you and encourages us to
continue developing and improving the library. Thank you for your
support!

------------------------------------------------------------------------

<!-- #### 🐝🐝🐝 We are quite busy lately 🐝🐝🐝

![Alt](https://repobeats.axiom.co/api/embed/d2d9164b6bf69bc14af4e6eb47e437b876d0dc0f.svg "Repobeats analytics image")
 -->

## Install

FastStream works on Linux, macOS, Windows and most Unix-style operating systems.
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

FastStream brokers provide convenient function decorators `@broker.subscriber`
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
`@broker.publisher` decorators in a FastStream application:

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

In order to get all Kafka or RabbitMQ related dependancies, you must install FastStream with the `kafka` or `rabbit` options, respectively:

``` sh
pip install faststream[kafka]
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

## License

FastStream is licensed under the Apache License 2.0

A permissive license whose main conditions require preservation of
copyright and license notices. Contributors provide an express grant of
patent rights. Licensed works, modifications, and larger works may be
distributed under different terms and without source code.

The full text of the license can be found
[here](https://raw.githubusercontent.com/airtai/faststream/main/LICENSE).

## Contributors

Thanks for all of these amazing peoples made the project better!

<a href="https://github.com/airtai/faststream/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=airtai/faststream"/>
</a>

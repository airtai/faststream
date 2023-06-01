# FastKafka

<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

<b>Effortless Kafka integration for your web services</b>

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

[FastKafka](https://fastkafka.airt.ai/) is a powerful and easy-to-use
Python library for building asynchronous services that interact with
Kafka topics. Built on top of [Pydantic](https://docs.pydantic.dev/),
[AIOKafka](https://github.com/aio-libs/aiokafka) and
[AsyncAPI](https://www.asyncapi.com/), FastKafka simplifies the process
of writing producers and consumers for Kafka topics, handling all the
parsing, networking, task scheduling and data generation automatically.
With FastKafka, you can quickly prototype and develop high-performance
Kafka-based services with minimal code, making it an ideal choice for
developers looking to streamline their workflow and accelerate their
projects.

------------------------------------------------------------------------

#### ⭐⭐⭐ Stay in touch ⭐⭐⭐

Please show your support and stay in touch by:

- giving our [GitHub repository](https://github.com/airtai/fastkafka/) a
  star, and

- joining our [Discord server](https://discord.gg/CJWmYpyFbc).

Your support helps us to stay in touch with you and encourages us to
continue developing and improving the library. Thank you for your
support!

------------------------------------------------------------------------

#### 🐝🐝🐝 We were busy lately 🐝🐝🐝

![Activity](https://repobeats.axiom.co/api/embed/21f36049093d5eb8e5fdad18c3c5d8df5428ca30.svg "Repobeats analytics image")

## Install

FastKafka works on Windows, macOS, Linux, and most Unix-style operating systems.
You can install base version of `fastkafka` with `pip` as usual:

``` sh
pip install fastkafka
```

To install fastkafka with testing features please use:

``` sh
pip install fastkafka[test]
```

To install fastkafka with asyncapi docs please use:

``` sh
pip install fastkafka[docs]
```

To install fastkafka with all the features please use:

``` sh
pip install fastkafka[test,docs]
```

## Tutorial

You can start an interactive tutorial in Google Colab by clicking the
button below:

<a href="https://colab.research.google.com/github/airtai/fastkafka/blob/main/nbs/index.ipynb" target=”_blank”>
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open in Colab" />
</a>

## Writing server code

To demonstrate FastKafka simplicity of using `@produces` and `@consumes`
decorators, we will focus on a simple app.

The app will consume jsons containig positive floats from one topic, log
them and then produce incremented values to another topic.

### Messages

FastKafka uses [Pydantic](https://docs.pydantic.dev/) to parse input
JSON-encoded data into Python objects, making it easy to work with
structured data in your Kafka-based applications. Pydantic’s
[`BaseModel`](https://docs.pydantic.dev/usage/models/) class allows you
to define messages using a declarative syntax, making it easy to specify
the fields and types of your messages.

This example defines one `Data` mesage class. This Class will model the
consumed and produced data in our app demo, it contains one
`NonNegativeFloat` field `data` that will be logged and “processed”
before being produced to another topic.

These message class will be used to parse and validate incoming data in
Kafka consumers and producers.

``` python
from pydantic import BaseModel, Field, NonNegativeFloat


class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., example=0.5, description="Float data example"
    )
```

### Application

This example shows how to initialize a FastKafka application.

It starts by defining a dictionary called `kafka_brokers`, which
contains two entries: `"localhost"` and `"production"`, specifying local
development and production Kafka brokers. Each entry specifies the URL,
port, and other details of a Kafka broker. This dictionary is used for
both generating the documentation and later to run the actual server
against one of the given kafka broker.

Next, an object of the
[`FastKafka`](https://fastkafka.airt.ai/docs/api/fastkafka#fastkafka.FastKafka)
class is initialized with the minimum set of arguments:

- `kafka_brokers`: a dictionary used for generation of documentation

We will also import and create a logger so that we can log the incoming
data in our consuming function.

``` python
from logging import getLogger
from fastkafka import FastKafka

logger = getLogger("Demo Kafka app")

kafka_brokers = {
    "localhost": {
        "url": "localhost",
        "description": "local development kafka broker",
        "port": 9092,
    },
    "production": {
        "url": "kafka.airt.ai",
        "description": "production kafka broker",
        "port": 9092,
        "protocol": "kafka-secure",
        "security": {"type": "plain"},
    },
}

kafka_app = FastKafka(
    title="Demo Kafka app",
    kafka_brokers=kafka_brokers,
)
```

### Function decorators

FastKafka provides convenient function decorators `@kafka_app.consumes`
and `@kafka_app.produces` to allow you to delegate the actual process of

- consuming and producing data to Kafka, and

- decoding and encoding JSON encode messages

from user defined functions to the framework. The FastKafka framework
delegates these jobs to AIOKafka and Pydantic libraries.

These decorators make it easy to specify the processing logic for your
Kafka consumers and producers, allowing you to focus on the core
business logic of your application without worrying about the underlying
Kafka integration.

This following example shows how to use the `@kafka_app.consumes` and
`@kafka_app.produces` decorators in a FastKafka application:

- The `@kafka_app.consumes` decorator is applied to the `on_input_data`
  function, which specifies that this function should be called whenever
  a message is received on the “input_data” Kafka topic. The
  `on_input_data` function takes a single argument which is expected to
  be an instance of the `Data` message class. Specifying the type of the
  single argument is instructing the Pydantic to use `Data.parse_raw()`
  on the consumed message before passing it to the user defined function
  `on_input_data`.

- The `@produces` decorator is applied to the `to_output_data` function,
  which specifies that this function should produce a message to the
  “output_data” Kafka topic whenever it is called. The `to_output_data`
  function takes a single float argument `data`. It it increments the
  data returns it wrapped in a `Data` object. The framework will call
  the `Data.json().encode("utf-8")` function on the returned value and
  produce it to the specified topic.

``` python
@kafka_app.consumes(topic="input_data", auto_offset_reset="latest")
async def on_input_data(msg: Data):
    logger.info(f"Got data: {msg.data}")
    await to_output_data(msg.data)


@kafka_app.produces(topic="output_data")
async def to_output_data(data: float) -> Data:
    processed_data = Data(data=data+1.0)
    return processed_data
```

## Testing the service

The service can be tested using the
[`Tester`](https://fastkafka.airt.ai/docs/api/fastkafka/testing/Tester)
instances which internally starts InMemory implementation of Kafka
broker.

The Tester will redirect your consumes and produces decorated functions
to the InMemory Kafka broker so that you can quickly test your app
without the need for a running Kafka broker and all its dependencies.

``` python
from fastkafka.testing import Tester

msg = Data(
    data=0.1,
)

# Start Tester app and create InMemory Kafka broker for testing
async with Tester(kafka_app) as tester:
    # Send Data message to input_data topic
    await tester.to_input_data(msg)

    # Assert that the kafka_app responded with incremented data in output_data topic
    await tester.awaited_mocks.on_output_data.assert_awaited_with(
        Data(data=1.1), timeout=2
    )
```

    [INFO] fastkafka._testing.in_memory_broker: InMemoryBroker._start() called
    [INFO] fastkafka._testing.in_memory_broker: InMemoryBroker._patch_consumers_and_producers(): Patching consumers and producers!
    [INFO] fastkafka._testing.in_memory_broker: InMemoryBroker starting
    [INFO] fastkafka._application.app: _create_producer() : created producer using the config: '{'bootstrap_servers': 'localhost:9092'}'
    [INFO] fastkafka._testing.in_memory_broker: AIOKafkaProducer patched start() called()
    [INFO] fastkafka._application.app: _create_producer() : created producer using the config: '{'bootstrap_servers': 'localhost:9092'}'
    [INFO] fastkafka._testing.in_memory_broker: AIOKafkaProducer patched start() called()
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() starting...
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer created using the following parameters: {'bootstrap_servers': 'localhost:9092', 'auto_offset_reset': 'latest', 'max_poll_records': 100}
    [INFO] fastkafka._testing.in_memory_broker: AIOKafkaConsumer patched start() called()
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer started.
    [INFO] fastkafka._testing.in_memory_broker: AIOKafkaConsumer patched subscribe() called
    [INFO] fastkafka._testing.in_memory_broker: AIOKafkaConsumer.subscribe(), subscribing to: ['input_data']
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer subscribed.
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() starting...
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer created using the following parameters: {'bootstrap_servers': 'localhost:9092', 'auto_offset_reset': 'earliest', 'max_poll_records': 100}
    [INFO] fastkafka._testing.in_memory_broker: AIOKafkaConsumer patched start() called()
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer started.
    [INFO] fastkafka._testing.in_memory_broker: AIOKafkaConsumer patched subscribe() called
    [INFO] fastkafka._testing.in_memory_broker: AIOKafkaConsumer.subscribe(), subscribing to: ['output_data']
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer subscribed.
    [INFO] Demo Kafka app: Got data: 0.1
    [INFO] fastkafka._testing.in_memory_broker: AIOKafkaConsumer patched stop() called
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer stopped.
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() finished.
    [INFO] fastkafka._testing.in_memory_broker: AIOKafkaProducer patched stop() called
    [INFO] fastkafka._testing.in_memory_broker: AIOKafkaConsumer patched stop() called
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer stopped.
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() finished.
    [INFO] fastkafka._testing.in_memory_broker: AIOKafkaProducer patched stop() called
    [INFO] fastkafka._testing.in_memory_broker: InMemoryBroker._stop() called
    [INFO] fastkafka._testing.in_memory_broker: InMemoryBroker stopping

### Recap

We have created a simple fastkafka application. The app will consume the
`Data` from the `input_data` topic, log it and produce the incremented
data to `output_data` topic.

To test the app we have:

1.  Created the app

2.  Started our Tester class which mirrors the developed app topics for
    testing purposes

3.  Sent Data message to `input_data` topic

4.  Asserted and checked that the developed service has reacted to Data
    message

## Running the service

The service can be started using builtin faskafka run CLI command.
Before we can do that, we will concatenate the code snippets from above
and save them in a file `"application.py"`

``` python
# content of the "application.py" file

from pydantic import BaseModel, Field, NonNegativeFloat

from fastkafka import FastKafka
from fastkafka._components.logger import get_logger

logger = get_logger(__name__)

class Data(BaseModel):
    data: NonNegativeFloat = Field(
        ..., example=0.5, description="Float data example"
    )

kafka_brokers = {
    "localhost": {
        "url": "localhost",
        "description": "local development kafka broker",
        "port": 9092,
    },
    "production": {
        "url": "kafka.airt.ai",
        "description": "production kafka broker",
        "port": 9092,
        "protocol": "kafka-secure",
        "security": {"type": "plain"},
    },
}

kafka_app = FastKafka(
    title="Demo Kafka app",
    kafka_brokers=kafka_brokers,
)

@kafka_app.consumes(topic="input_data", auto_offset_reset="latest")
async def on_input_data(msg: Data):
    logger.info(f"Got data: {msg.data}")
    await to_output_data(msg.data)


@kafka_app.produces(topic="output_data")
async def to_output_data(data: float) -> Data:
    processed_data = Data(data=data+1.0)
    return processed_data
```

To run the service, use the FastKafka CLI command and pass the module
(in this case, the file where the app implementation is located) and the
app simbol to the command.

``` sh
fastkafka run --num-workers=1 --kafka-broker localhost application:kafka_app
```

After running the command, you should see the following output in your
command line:

    [1504]: 23-05-31 11:36:45.874 [INFO] fastkafka._application.app: set_kafka_broker() : Setting bootstrap_servers value to 'localhost:9092'
    [1504]: 23-05-31 11:36:45.875 [INFO] fastkafka._application.app: _create_producer() : created producer using the config: '{'bootstrap_servers': 'localhost:9092'}'
    [1504]: 23-05-31 11:36:45.937 [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() starting...
    [1504]: 23-05-31 11:36:45.937 [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer created using the following parameters: {'bootstrap_servers': 'localhost:9092', 'auto_offset_reset': 'latest', 'max_poll_records': 100}
    [1504]: 23-05-31 11:36:45.956 [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer started.
    [1504]: 23-05-31 11:36:45.956 [INFO] aiokafka.consumer.subscription_state: Updating subscribed topics to: frozenset({'input_data'})
    [1504]: 23-05-31 11:36:45.956 [INFO] aiokafka.consumer.consumer: Subscribed to topic(s): {'input_data'}
    [1504]: 23-05-31 11:36:45.956 [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer subscribed.
    [1506]: 23-05-31 11:36:45.993 [INFO] fastkafka._application.app: set_kafka_broker() : Setting bootstrap_servers value to 'localhost:9092'
    [1506]: 23-05-31 11:36:45.994 [INFO] fastkafka._application.app: _create_producer() : created producer using the config: '{'bootstrap_servers': 'localhost:9092'}'
    [1506]: 23-05-31 11:36:46.014 [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() starting...
    [1506]: 23-05-31 11:36:46.015 [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer created using the following parameters: {'bootstrap_servers': 'localhost:9092', 'auto_offset_reset': 'latest', 'max_poll_records': 100}
    [1506]: 23-05-31 11:36:46.040 [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer started.
    [1506]: 23-05-31 11:36:46.042 [INFO] aiokafka.consumer.subscription_state: Updating subscribed topics to: frozenset({'input_data'})
    [1506]: 23-05-31 11:36:46.043 [INFO] aiokafka.consumer.consumer: Subscribed to topic(s): {'input_data'}
    [1506]: 23-05-31 11:36:46.043 [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer subscribed.
    [1506]: 23-05-31 11:36:46.068 [ERROR] aiokafka.cluster: Topic input_data not found in cluster metadata
    [1506]: 23-05-31 11:36:46.070 [INFO] aiokafka.consumer.group_coordinator: Metadata for topic has changed from {} to {'input_data': 0}. 
    [1504]: 23-05-31 11:36:46.131 [WARNING] aiokafka.cluster: Topic input_data is not available during auto-create initialization
    [1504]: 23-05-31 11:36:46.132 [INFO] aiokafka.consumer.group_coordinator: Metadata for topic has changed from {} to {'input_data': 0}. 
    [1506]: 23-05-31 11:37:00.237 [ERROR] aiokafka: Unable connect to node with id 0: [Errno 111] Connect call failed ('172.28.0.12', 9092)
    [1506]: 23-05-31 11:37:00.237 [ERROR] aiokafka: Unable to update metadata from [0]
    [1504]: 23-05-31 11:37:00.238 [ERROR] aiokafka: Unable connect to node with id 0: [Errno 111] Connect call failed ('172.28.0.12', 9092)
    [1504]: 23-05-31 11:37:00.238 [ERROR] aiokafka: Unable to update metadata from [0]
    [1506]: 23-05-31 11:37:00.294 [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer stopped.
    [1506]: 23-05-31 11:37:00.294 [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() finished.
    Starting process cleanup, this may take a few seconds...
    23-05-31 11:37:00.345 [INFO] fastkafka._server: terminate_asyncio_process(): Terminating the process 1504...
    23-05-31 11:37:00.345 [INFO] fastkafka._server: terminate_asyncio_process(): Terminating the process 1506...
    [1504]: 23-05-31 11:37:00.347 [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer stopped.
    [1504]: 23-05-31 11:37:00.347 [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() finished.
    23-05-31 11:37:00.607 [INFO] fastkafka._server: terminate_asyncio_process(): Process 1506 was already terminated.
    23-05-31 11:37:00.822 [INFO] fastkafka._server: terminate_asyncio_process(): Process 1504 was already terminated.

## Documentation

The kafka app comes with builtin documentation generation using
[AsyncApi HTML generator](https://www.asyncapi.com/tools/generator).

AsyncApi requires Node.js to be installed and we provide the following
convenience command line for it:

``` sh
fastkafka docs install_deps
```

    23-05-31 11:38:24.128 [INFO] fastkafka._components.docs_dependencies: AsyncAPI generator installed

To generate the documentation programatically you just need to call the
following command:

``` sh
fastkafka docs generate application:kafka_app
```

    23-05-31 11:38:25.113 [INFO] fastkafka._components.asyncapi: Old async specifications at '/content/asyncapi/spec/asyncapi.yml' does not exist.
    23-05-31 11:38:25.118 [INFO] fastkafka._components.asyncapi: New async specifications generated at: '/content/asyncapi/spec/asyncapi.yml'
    23-05-31 11:38:43.455 [INFO] fastkafka._components.asyncapi: Async docs generated at 'asyncapi/docs'
    23-05-31 11:38:43.455 [INFO] fastkafka._components.asyncapi: Output of '$ npx -y -p @asyncapi/generator ag asyncapi/spec/asyncapi.yml @asyncapi/html-template -o asyncapi/docs --force-write'

    Done! ✨
    Check out your shiny new generated files at /content/asyncapi/docs.

This will generate the *asyncapi* folder in relative path where all your
documentation will be saved. You can check out the content of it with:

``` sh
ls -l asyncapi
```

    total 8
    drwxr-xr-x 4 root root 4096 May 31 11:38 docs
    drwxr-xr-x 2 root root 4096 May 31 11:38 spec

In docs folder you will find the servable static html file of your
documentation. This can also be served using our `fastkafka docs serve`
CLI command (more on that in our guides).

In spec folder you will find a asyncapi.yml file containing the async
API specification of your application.

We can locally preview the generated documentation by running the
following command:

``` sh
fastkafka docs serve application:kafka_app
```

    23-05-31 11:38:45.250 [INFO] fastkafka._components.asyncapi: New async specifications generated at: '/content/asyncapi/spec/asyncapi.yml'
    23-05-31 11:39:04.410 [INFO] fastkafka._components.asyncapi: Async docs generated at 'asyncapi/docs'
    23-05-31 11:39:04.411 [INFO] fastkafka._components.asyncapi: Output of '$ npx -y -p @asyncapi/generator ag asyncapi/spec/asyncapi.yml @asyncapi/html-template -o asyncapi/docs --force-write'

    Done! ✨
    Check out your shiny new generated files at /content/asyncapi/docs.


    Serving documentation on http://127.0.0.1:8000
    127.0.0.1 - - [31/May/2023 11:39:14] "GET / HTTP/1.1" 200 -
    127.0.0.1 - - [31/May/2023 11:39:14] "GET /css/global.min.css HTTP/1.1" 200 -
    127.0.0.1 - - [31/May/2023 11:39:14] "GET /js/asyncapi-ui.min.js HTTP/1.1" 200 -
    127.0.0.1 - - [31/May/2023 11:39:14] "GET /css/asyncapi.min.css HTTP/1.1" 200 -
    Interupting serving of documentation and cleaning up...

From the parameters passed to the application constructor, we get the
documentation bellow:

``` python
from fastkafka import FastKafka

kafka_brokers = {
    "localhost": {
        "url": "localhost",
        "description": "local development kafka broker",
        "port": 9092,
    },
    "production": {
        "url": "kafka.airt.ai",
        "description": "production kafka broker",
        "port": 9092,
        "protocol": "kafka-secure",
        "security": {"type": "plain"},
    },
}

kafka_app = FastKafka(
    title="Demo Kafka app",
    kafka_brokers=kafka_brokers,
)
```

![Kafka_servers](https://raw.githubusercontent.com/airtai/fastkafka/main/nbs/images/screenshot-kafka-servers.png)

The following documentation snippet are for the consumer as specified in
the code above:

![Kafka_consumer](https://raw.githubusercontent.com/airtai/fastkafka/main/nbs/images/screenshot-kafka-consumer.png)

The following documentation snippet are for the producer as specified in
the code above:

![Kafka_producer](https://raw.githubusercontent.com/airtai/fastkafka/main/nbs/images/screenshot-kafka-producer.png)

Finally, all messages as defined as subclasses of *BaseModel* are
documented as well:

![Kafka\_![Kafka_servers](https://raw.githubusercontent.com/airtai/fastkafka/main/nbs/images/screenshot-kafka-messages.png)](https://raw.githubusercontent.com/airtai/fastkafka/main/nbs/images/screenshot-kafka-messages.png)

## License

FastKafka is licensed under the Apache License 2.0

A permissive license whose main conditions require preservation of
copyright and license notices. Contributors provide an express grant of
patent rights. Licensed works, modifications, and larger works may be
distributed under different terms and without source code.

The full text of the license can be found
[here](https://raw.githubusercontent.com/airtai/fastkafka/main/LICENSE).

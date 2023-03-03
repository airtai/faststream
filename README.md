FastKafka
================

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

[FastKafka](fastkafka.airt.ai) is a powerful and easy-to-use Python
library for building asynchronous services that interact with Kafka
topics. Built on top of [Pydantic](https://docs.pydantic.dev/),
[AIOKafka](https://github.com/aio-libs/aiokafka) and
[AsyncAPI](https://www.asyncapi.com/), FastKafka simplifies the process
of writing producers and consumers for Kafka topics, handling all the
parsing, networking, task scheduling and data generation automatically.
With FastKafka, you can quickly prototype and develop high-performance
Kafka-based services with minimal code, making it an ideal choice for
developers looking to streamline their workflow and accelerate their
projects.

## Install

FastKafka works on macOS, Linux, and most Unix-style operating systems.
You can install it with `pip` as usual:

``` sh
pip install fastkafka
```

## Tutorial

You can start an interactive tutorial in Google Colab by clicking the
button below:

<a href="https://colab.research.google.com/github/airtai/fastkafka/blob/main/nbs/guides/Guide_00_FastKafka_Demo.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab" target=”_blank”>
</a>

## Writing server code

Here is an example python script using FastKafka that takes data from a
Kafka topic, makes a prediction using a predictive model, and outputs
the prediction to another Kafka topic.

### Messages

FastKafka uses [Pydantic](https://docs.pydantic.dev/) to parse input
JSON-encoded data into Python objects, making it easy to work with
structured data in your Kafka-based applications. Pydantic’s
[`BaseModel`](https://docs.pydantic.dev/usage/models/) class allows you
to define messages using a declarative syntax, making it easy to specify
the fields and types of your messages.

This example defines two message classes for use in a FastKafka
application:

- The `InputData` class is used to represent input data for a predictive
  model. It has three fields: `user_id`, `feature_1`, and `feature_2`.
  The `user_id` field is of type
  [`NonNegativeInt`](https://docs.pydantic.dev/usage/types/#constrained-types),
  which is a subclass of int that only allows non-negative integers. The
  `feature_1` and `feature_2` fields are both lists of floating-point
  numbers and integers, respectively.

- The `Prediction` class is used to represent the output of the
  predictive model. It has two fields: `user_id` and `score`. The
  `score` field is a floating-point number and it represents the
  prediction made by the model, such as the probability of churn in the
  next 28 days.

These message classes will be used to parse and validate incoming data
in Kafka consumers and producers.

``` python
from typing import List

from pydantic import BaseModel, Field, NonNegativeInt


class InputData(BaseModel):
    user_id: NonNegativeInt = Field(..., example=202020, description="ID of a user")
    feature_1: List[float] = Field(
        ...,
        example=[1.2, 2.3, 4.5, 6.7, 0.1],
        description="input feature 1",
    )
    feature_2: List[int] = Field(
        ...,
        example=[2, 4, 3, 1, 0],
        description="input feature 2",
    )


class Prediction(BaseModel):
    user_id: NonNegativeInt = Field(..., example=202020, description="ID of a user")
    score: float = Field(
        ...,
        example=0.4321,
        description="Prediction score (e.g. the probability of churn in the next 28 days)",
        ge=0.0,
        le=1.0,
    )
```

These message classes will be used to parse and validate incoming data
in a Kafka consumer and to produce a JSON-encoded message in a producer.
Using Pydantic’s BaseModel in combination with FastKafka makes it easy
to work with structured data in your Kafka-based applications.

### Application

This example shows how to initialize a FastKafka application.

It starts by defining a dictionary called `kafka_brokers`, which
contains two entries: `"localhost"` and `"production"`, specifying local
development and production Kafka brokers. Each entry specifies the URL,
port, and other details of a Kafka broker. This dictionary is used for
generating the documentation only and it is not being checked by the
actual server.

Next, an object of the
[`FastKafka`](https://airtai.github.io/fastkafka/fastkafka.html#fastkafka)
class is initialized with the minimum set of arguments:

- `kafka_brokers`: a dictionary used for generation of documentation

- `bootstrap_servers`: a `host[:port]` string or list of `host[:port]`
  strings that a consumer or a producer should contact to bootstrap
  initial cluster metadata

``` python
from fastkafka.application import FastKafka

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
    kafka_brokers=kafka_brokers,
    bootstrap_servers="localhost:9092",
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
  be an instance of the `InputData` message class. Specifying the type
  of the single argument is instructing the Pydantic to use
  `InputData.parse_raw()` on the consumed message before passing it to
  the user defined function `on_input_data`.

- The `@produces` decorator is applied to the `to_predictions` function,
  which specifies that this function should produce a message to the
  “predictions” Kafka topic whenever it is called. The `to_predictions`
  function takes two arguments: `user_id` and `score`. It creates a new
  `Prediction` message with these values and then returns it. The
  framework will call the `Prediction.json().encode("utf-8")` function
  on the returned value and produce it to the specified topic.

``` python
@kafka_app.consumes(topic="input_data", auto_offset_reset="latest", group_id="my_group")
async def on_input_data(msg: InputData):
    # this is a mock up for testing, should be replaced with the real model
    class Model:
        async def predict(self, feature_1: List[int], feature_2: List[float]) -> float:
            return 0.87

    model = Model()

    score = await model.predict(feature_1=msg.feature_1, feature_2=msg.feature_2)
    await to_predictions(user_id=msg.user_id, score=score)


@kafka_app.produces(topic="predictions")
async def to_predictions(user_id: int, score: float) -> Prediction:
    prediction = Prediction(user_id=user_id, score=score)
    return prediction
```

## Testing the service

The service can be tested using the
[`LocalKafkaBroker`](https://airtai.github.io/fastkafka/localkafkabroker.html#localkafkabroker)
and [`Tester`](https://airtai.github.io/fastkafka/tester.html#tester)
instances.

``` python
from fastkafka.application import Tester
from fastkafka.helpers import create_missing_topics
from fastkafka.testing import LocalKafkaBroker
```

``` python
async with LocalKafkaBroker(
    zookeeper_port=9892, listener_port=9893, topics=kafka_app.get_topics()
) as bootstrap_servers:
    kafka_app.set_bootstrap_servers(bootstrap_servers)

    # Creating the Tester object
    tester = Tester(app=kafka_app)

    async with tester:
        # Send message to input_data topic
        await tester.to_input_data(
            InputData(user_id=1, feature_1=[0.1, 0.2], feature_2=[1.1, -1.2])
        )
        # Assert that the "kafka_app" service reacted to sent message with a Prediction message in predictions topic
        await tester.awaited_mocks.on_predictions.assert_awaited_with(
            Prediction(user_id=1, score=0.87), timeout=5
        )

print("ok")
```

    [INFO] fastkafka.testing: Java is already installed.
    [INFO] fastkafka.testing: Kafka is already installed.
    [INFO] fastkafka.testing: Starting zookeeper...
    [INFO] fastkafka.testing: Zookeeper started, sleeping for 5 seconds...
    [INFO] fastkafka.testing: Starting Kafka broker...
    [INFO] fastkafka.testing: Kafka broker started, sleeping for 5 seconds...
    [INFO] fastkafka.testing: Local Kafka broker up and running on 127.0.0.1:9893
    [INFO] fastkafka.application: _create_producer() : created producer using the config: '{'bootstrap_servers': '127.0.0.1:9893'}'
    [INFO] fastkafka.application: _create_producer() : created producer using the config: '{'bootstrap_servers': '127.0.0.1:9893'}'
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() starting...
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer created using the following parameters: {'bootstrap_servers': '127.0.0.1:9893', 'auto_offset_reset': 'latest', 'max_poll_records': 100, 'group_id': 'my_group'}
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() starting...
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer created using the following parameters: {'bootstrap_servers': '127.0.0.1:9893', 'auto_offset_reset': 'earliest', 'max_poll_records': 100}
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer started.
    [INFO] aiokafka.consumer.subscription_state: Updating subscribed topics to: frozenset({'input_data'})
    [INFO] aiokafka.consumer.consumer: Subscribed to topic(s): {'input_data'}
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer subscribed.
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer started.
    [INFO] aiokafka.consumer.subscription_state: Updating subscribed topics to: frozenset({'predictions'})
    [INFO] aiokafka.consumer.consumer: Subscribed to topic(s): {'predictions'}
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer subscribed.
    [INFO] aiokafka.consumer.group_coordinator: Metadata for topic has changed from {} to {'predictions': 1}. 
    [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [INFO] aiokafka.consumer.group_coordinator: Discovered coordinator 0 for group my_group
    [INFO] aiokafka.consumer.group_coordinator: Revoking previously assigned partitions set() for group my_group
    [INFO] aiokafka.consumer.group_coordinator: (Re-)joining group my_group
    [INFO] aiokafka.consumer.group_coordinator: Joined group 'my_group' (generation 1) with member_id aiokafka-0.8.0-431e1a90-1105-454b-b444-bb29fc7acad9
    [INFO] aiokafka.consumer.group_coordinator: Elected group leader -- performing partition assignments using roundrobin
    [INFO] aiokafka.consumer.group_coordinator: Successfully synced group my_group with generation 1
    [INFO] aiokafka.consumer.group_coordinator: Setting newly assigned partitions {TopicPartition(topic='input_data', partition=0)} for group my_group
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer stopped.
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() finished.
    [INFO] aiokafka.consumer.group_coordinator: LeaveGroup request succeeded
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer stopped.
    [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() finished.
    [INFO] fastkafka._components._subprocess: terminate_asyncio_process(): Terminating the process 36258...
    [INFO] fastkafka._components._subprocess: terminate_asyncio_process(): Process 36258 terminated.
    [INFO] fastkafka._components._subprocess: terminate_asyncio_process(): Terminating the process 35893...
    [INFO] fastkafka._components._subprocess: terminate_asyncio_process(): Process 35893 terminated.
    ok

## Running the service

The service can be started using builtin faskafka run CLI command

We will concatenate the code snippets from above and save them in a file
`"server.py"`

### Example

This example contains the content of the file “server.py”:

``` python

from typing import List
from pydantic import BaseModel, Field, NonNegativeInt

class InputData(BaseModel):
    user_id: NonNegativeInt = Field(..., example=202020, description="ID of a user")
    feature_1: List[float] = Field(
        ...,
        example=[1.2, 2.3, 4.5, 6.7, 0.1],
        description="input feature 1",
    )
    feature_2: List[int] = Field(
        ...,
        example=[2, 4, 3, 1, 0],
        description="input feature 2",
    )

class Prediction(BaseModel):
    user_id: NonNegativeInt = Field(..., example=202020, description="ID of a user")
    score: float = Field(
        ...,
        example=0.4321,
        description="Prediction score (e.g. the probability of churn in the next 28 days)",
        ge=0.0,
        le=1.0,
    )



from os import environ

from fastkafka.application import FastKafka

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

bootstrap_servers = f"{environ['KAFKA_HOSTNAME']}:{environ['KAFKA_PORT']}"

kafka_app = FastKafka(
    kafka_brokers=kafka_brokers,
    bootstrap_servers=bootstrap_servers,
)



@kafka_app.consumes(topic="input_data", auto_offset_reset="latest", group_id="my_group")
async def on_input_data(msg: InputData):
    global model
    score = await model.predict(feature_1=msg.feature_1, feature_2=msg.feature_2)
    await to_predictions(user_id=msg.user_id, score=score)


@kafka_app.produces(topic="predictions")
async def to_predictions(user_id: int, score: float) -> Prediction:
    prediction = Prediction(user_id=user_id, score=score)
    return prediction


# this is a mock up for testing, should be replaced with the real model
class Model:
    async def predict(self, feature_1: List[int], feature_2: List[float]) -> float:
        return 0.87


model = Model()
```

Notice the
`bootstrap_servers = f"{environ['KAFKA_HOSTNAME']}:{environ['KAFKA_PORT']}"`
line. This enables us to pass the Kafka bootstrap server address to the
app through the environment variables.

Then, we start the FastKafka service by running the following command in
the folder where the server.py file is located:

``` shell
fastkafka run --num-workers=2 server:kafka_app
```

After running the command, you should see an output like the one below:

    [INFO] fastkafka.testing: Java is already installed.
    [INFO] fastkafka.testing: Kafka is already installed.
    [INFO] fastkafka.testing: Starting zookeeper...
    [INFO] fastkafka.testing: Zookeeper started, sleeping for 5 seconds...
    [INFO] fastkafka.testing: Starting Kafka broker...
    [INFO] fastkafka.testing: Kafka broker started, sleeping for 5 seconds...
    [INFO] fastkafka.testing: Local Kafka broker up and running on 127.0.0.1:9893
    [38842]: [INFO] fastkafka.application: _create_producer() : created producer using the config: '{'bootstrap_servers': 'localhost:9893'}'
    [38842]: [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() starting...
    [38842]: [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer created using the following parameters: {'bootstrap_servers': 'localhost:9893', 'auto_offset_reset': 'latest', 'max_poll_records': 100, 'group_id': 'my_group'}
    [38842]: [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer started.
    [38842]: [INFO] aiokafka.consumer.subscription_state: Updating subscribed topics to: frozenset({'input_data'})
    [38842]: [INFO] aiokafka.consumer.consumer: Subscribed to topic(s): {'input_data'}
    [38842]: [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer subscribed.
    [38844]: [INFO] fastkafka.application: _create_producer() : created producer using the config: '{'bootstrap_servers': 'localhost:9893'}'
    [38844]: [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() starting...
    [38844]: [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer created using the following parameters: {'bootstrap_servers': 'localhost:9893', 'auto_offset_reset': 'latest', 'max_poll_records': 100, 'group_id': 'my_group'}
    [38844]: [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer started.
    [38844]: [INFO] aiokafka.consumer.subscription_state: Updating subscribed topics to: frozenset({'input_data'})
    [38844]: [INFO] aiokafka.consumer.consumer: Subscribed to topic(s): {'input_data'}
    [38844]: [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer subscribed.
    [38842]: [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [38844]: [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [38842]: [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [38844]: [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [38842]: [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [38844]: [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [38842]: [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [38844]: [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [38842]: [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [38844]: [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [38842]: [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [38844]: [ERROR] aiokafka.consumer.group_coordinator: Group Coordinator Request failed: [Error 15] CoordinatorNotAvailableError
    [38842]: [INFO] aiokafka.consumer.group_coordinator: Discovered coordinator 0 for group my_group
    [38842]: [INFO] aiokafka.consumer.group_coordinator: Revoking previously assigned partitions set() for group my_group
    [38842]: [INFO] aiokafka.consumer.group_coordinator: (Re-)joining group my_group
    [38844]: [INFO] aiokafka.consumer.group_coordinator: Discovered coordinator 0 for group my_group
    [38844]: [INFO] aiokafka.consumer.group_coordinator: Revoking previously assigned partitions set() for group my_group
    [38844]: [INFO] aiokafka.consumer.group_coordinator: (Re-)joining group my_group
    [38844]: [INFO] aiokafka.consumer.group_coordinator: Joined group 'my_group' (generation 1) with member_id aiokafka-0.8.0-51dca0da-604f-4547-8646-16ed669891c6
    [38842]: [INFO] aiokafka.consumer.group_coordinator: Joined group 'my_group' (generation 1) with member_id aiokafka-0.8.0-9d2385ea-7617-49aa-9db1-71b163bf77ff
    [38842]: [INFO] aiokafka.consumer.group_coordinator: Elected group leader -- performing partition assignments using roundrobin
    [38844]: [INFO] aiokafka.consumer.group_coordinator: Successfully synced group my_group with generation 1
    [38844]: [INFO] aiokafka.consumer.group_coordinator: Setting newly assigned partitions {TopicPartition(topic='input_data', partition=0)} for group my_group
    [38842]: [INFO] aiokafka.consumer.group_coordinator: Successfully synced group my_group with generation 1
    [38842]: [INFO] aiokafka.consumer.group_coordinator: Setting newly assigned partitions set() for group my_group
    Starting process cleanup, this may take a few seconds...
    [INFO] fastkafka.server: terminate_asyncio_process(): Terminating the process 38842...
    [INFO] fastkafka.server: terminate_asyncio_process(): Terminating the process 38844...
    [38842]: [INFO] aiokafka.consumer.group_coordinator: LeaveGroup request succeeded
    [38842]: [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer stopped.
    [38842]: [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() finished.
    [38844]: [INFO] aiokafka.consumer.group_coordinator: LeaveGroup request succeeded
    [38844]: [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer stopped.
    [38844]: [INFO] fastkafka._components.aiokafka_consumer_loop: aiokafka_consumer_loop() finished.
    [INFO] fastkafka.server: terminate_asyncio_process(): Process 38842 terminated.
    [INFO] fastkafka.server: terminate_asyncio_process(): Process 38844 terminated.

    [INFO] fastkafka._components._subprocess: terminate_asyncio_process(): Terminating the process 37742...
    [INFO] fastkafka._components._subprocess: terminate_asyncio_process(): Process 37742 terminated.
    [INFO] fastkafka._components._subprocess: terminate_asyncio_process(): Terminating the process 37377...
    [INFO] fastkafka._components._subprocess: terminate_asyncio_process(): Process 37377 terminated.

When the service is started, several log messages are printed to the
console, including information about the application startup, AsyncAPI
specification generation, and consumer loop status.

During the lifetime of the service, incoming requests will be processed
by the FastKafka application and appropriate actions will be taken based
on the defined Kafka consumers and producers. For example, if a message
is received on the “input_data” Kafka topic, the `on_input_data`
function will be called to process the message, and if the
`to_predictions` function is called, it will produce a message to the
“predictions” Kafka topic. The service will continue to run until it is
shut down, at which point the application shutdown process will be
initiated and the service will stop.

### Checking out the documentation

To generate the documentation **locally**, you can use the built in
kafka function that will do all the work for you. In the folder where
the server.py file is located, run the following command:

``` shell
fastkafka docs generate server:kafka_app
```

    [INFO] fastkafka._components.asyncapi: Old async specifications at '/tmp/tmp7tcpqamz/asyncapi/spec/asyncapi.yml' does not exist.
    [INFO] fastkafka._components.asyncapi: New async specifications generated at: '/tmp/tmp7tcpqamz/asyncapi/spec/asyncapi.yml'
    [INFO] fastkafka._components.asyncapi: Async docs generated at 'asyncapi/docs'
    [INFO] fastkafka._components.asyncapi: Output of '$ npx -y -p @asyncapi/generator ag asyncapi/spec/asyncapi.yml @asyncapi/html-template -o asyncapi/docs --force-write'

    Done! ✨
    Check out your shiny new generated files at /tmp/tmp7tcpqamz/asyncapi/docs.

To preview the documentation locally, run the following command:

``` shell
fastkafka docs serve server:kafka_app
```

After running the command you should see the following output:

    [INFO] fastkafka._components.asyncapi: Old async specifications at '/tmp/tmpwbqvpgk1/asyncapi/spec/asyncapi.yml' does not exist.
    [INFO] fastkafka._components.asyncapi: New async specifications generated at: '/tmp/tmpwbqvpgk1/asyncapi/spec/asyncapi.yml'
    [INFO] fastkafka._components.asyncapi: Async docs generated at 'asyncapi/docs'
    [INFO] fastkafka._components.asyncapi: Output of '$ npx -y -p @asyncapi/generator ag asyncapi/spec/asyncapi.yml @asyncapi/html-template -o asyncapi/docs --force-write'

    Done! ✨
    Check out your shiny new generated files at /tmp/tmpwbqvpgk1/asyncapi/docs.


    Serving documentation on http://127.0.0.1:8000
    Interupting serving of documentation and cleaning up...

    {'localhost': {'description': 'local development kafka broker',
                   'port': 9092,
                   'url': 'localhost'},
     'production': {'description': 'production kafka broker',
                    'port': 9092,
                    'protocol': 'kafka-secure',
                    'security': {'type': 'plain'},
                    'url': 'kafka.airt.ai'}}
    [ERROR] aiokafka: Unable connect to node with id 0: [Errno 111] Connect call failed ('192.168.48.6', 9893)
    [ERROR] aiokafka: Unable to update metadata from [0]

The generated documentation is as follows:

![Kafka_servers](https://raw.githubusercontent.com/airtai/fastkafka/main/nbs/images/screenshot-kafka-servers.png)

Next, you can see the documentation generated from the `@consumes`
decorator when used on the function `on_input_data` with a single
parameter of type `InputData`:

``` python
class InputData(BaseModel):
    user_id: NonNegativeInt = Field(..., example=202020, description="ID of a user")
    feature_1: List[float] = Field(
        ...,
        example=[1.2, 2.3, 4.5, 6.7, 0.1],
        description="input feature 1",
    )
    feature_2: List[int] = Field(
        ...,
        example=[2, 4, 3, 1, 0],
        description="input feature 2",
    )
```

``` python
@kafka_app.consumes(topic="input_data", auto_offset_reset="latest", group_id="my_group")
async def on_input_data(msg: InputData):
    global model
    score = await model.predict(feature_1=msg.feature_1, feature_2=msg.feature_2)
    await to_predictions(user_id=msg.user_id, score=score)
```

The resulting documentation is generated as follows:

![Kafka_consumer](https://raw.githubusercontent.com/airtai/fastkafka/main/nbs/images/screenshot-kafka-consumer.png)

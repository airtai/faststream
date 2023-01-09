FastKafkaAPI
================

<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

<b>Effortless Kafka integration for your web services</b>

------------------------------------------------------------------------

![PyPI](https://img.shields.io/pypi/v/fast-kafka-api.png) ![PyPI -
Downloads](https://img.shields.io/pypi/dm/fast-kafka-api.png) ![PyPI -
Python
Version](https://img.shields.io/pypi/pyversions/fast-kafka-api.png)

![GitHub Workflow
Status](https://img.shields.io/github/actions/workflow/status/airtai/fast-kafka-api/test.yaml)
![CodeQL](https://github.com/airtai/fast-kafka-api//actions/workflows/codeql.yml/badge.svg)
![Dependency
Review](https://github.com/airtai/fast-kafka-api//actions/workflows/dependency-review.yml/badge.svg)

![GitHub](https://img.shields.io/github/license/airtai/fast-kafka-api.png)

------------------------------------------------------------------------

FastKafkaAPI is a powerful and easy-to-use Python library for building
asynchronous web services that interact with Kafka topics. Built on top
of FastAPI, Starlette, Pydantic, and AIOKafka, FastKafkaAPI simplifies
the process of writing producers and consumers for Kafka topics,
handling all the parsing, networking, and task scheduling automatically.
With FastKafkaAPI, you can quickly prototype and develop
high-performance Kafka-based services with minimal code, making it an
ideal choice for developers looking to streamline their workflow and
accelerate their projects.

## Install

This command installs the FastKafkaAPI package from the Python Package
Index (PyPI) using the pip package manager.

`pip` is a command-line tool that allows you to install and manage
Python packages, including FastKafkaAPI. When you run the `pip install`
command with the name of a package (in this case, “fast-kafka-api”), pip
will download the package from PyPI, along with any dependencies that
the package requires, and install it on your system.

After running this command, you will be able to import and use the
FastKafkaAPI package in your Python code. For example, you might use it
to initialize a FastKafkaAPI application, as shown in the example
bellow, and to use the `@consumes` and `@produces` decorators to define
Kafka consumers and producers in your application.

Installing FastKafkaAPI from PyPI using `pip` is the recommended way to
install the package, as it makes it easy to manage the package and its
dependencies. If you prefer, you can also install FastKafkaAPI from the
source code by cloning the repository and running `pip install .` in the
root directory of the project.

``` sh
pip install fast-kafka-api
```

## How to use

Here is an example python script using FastKafkaAPI that takes data from
an input Kafka topic, makes a prediction using a predictive model, and
outputs the prediction to an output Kafka topic.

### Messages

FastKafkaAPI uses Pydantic to parse input JSON-encoded data into Python
objects, making it easy to work with structured data in your Kafka-based
applications. Pydantic’s `BaseModel` class allows you to define messages
using a declarative syntax, making it easy to specify the fields and
types of your messages.

This example defines two message classes for use in a FastKafkaAPI
application: `InputData` and `Prediction`.

The `InputData` class is used to represent input data for a predictive
model. It has three fields: `user_id`, `feature_1`, and `feature_2`. The
`user_id` field is of type `NonNegativeInt`, which is a subclass of int
that only allows non-negative integers. The `feature_1` and `feature_2`
fields are both lists of floating-point numbers and integers,
respectively. These fields are used to represent input features for the
predictive model.

The `Prediction` class is used to represent the output of the predictive
model. It has two fields: `user_id` and `score`. The `user_id` field is
of type `NonNegativeInt`, and the `score` field is a floating-point
number. The `score` field represents the prediction made by the model,
such as the probability of churn in the next 28 days.

These message classes will be used to parse and validate incoming data
in Kafka consumers and producers. Using these message classes in
combination with FastKafkaAPI makes it easy to work with structured data
in your Kafka-based applications.

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
Using Pydantic’s BaseModel in combination with FastKafkaAPI makes it
easy to work with structured data in your Kafka-based applications.

### Application

This example shows how to initialize a FastKafkaAPI application. It
starts by defining two environment variables: `KAFKA_HOSTNAME` and
`KAFKA_PORT`, which are used to specify the hostname and port of the
Kafka broker.

Next, it defines a dictionary called `kafka_brokers`, which contains two
entries: “localhost” and “production”. Each entry specifies the URL,
port, and other details of a Kafka broker. This dictionary is used to
define the available Kafka brokers that can be used in the application.

The `kafka_config` dictionary specifies the configuration options for
the Kafka broker, such as the `bootstrap_servers` setting, which
specifies the hostname and port of the Kafka broker.

Finally, the FastKafkaAPI class is initialized with several arguments:
`title`, `contact`, `version`, `description`, `kafka_brokers`, and
`kafka_config`. These arguments are used to configure various aspects of
the application, such as the title, version, and description of the
application, as well as the available Kafka brokers and the Kafka
configuration options. The resulting
[`FastKafkaAPI`](https://airtai.github.io/fast-kafka-api/fastkafkaapi.html#fastkafkaapi)
object, which is stored in the `app` variable, represents the
initialized FastKafkaAPI application.

``` python
from os import environ

from fast_kafka_api.application import FastKafkaAPI

kafka_server_url = environ["KAFKA_HOSTNAME"]
kafka_server_port = environ["KAFKA_PORT"]

kafka_brokers = {
    "localhost": {
        "url": "kafka",
        "description": "local development kafka broker",
        "port": 9092,
    },
    "production": {
        "url": "kafka.acme.com",
        "description": "production kafka broker",
        "port": 9092,
        "protocol": "kafka-secure",
        "security": {"type": "plain"},
    },
}

kafka_config = {
    "bootstrap_servers": f"{kafka_server_url}:{kafka_server_port}",
}

app = FastKafkaAPI(
    title="FastKafkaAPI Example",
    contact={"name": "airt.ai", "url": "https://airt.ai", "email": "info@airt.ai"},
    version="0.0.1",
    description="A simple example on how to use FastKafkaAPI",
    kafka_brokers=kafka_brokers,
    **kafka_config,
)
```

### Function decorators

FastKafkaAPI provides convenient function decorators called `@consumes`
and `@produces` to allow you to delegate the actual processing of data
to user-defined functions. These decorators make it easy to specify the
processing logic for your Kafka consumers and producers, allowing you to
focus on the core business logic of your application without worrying
about the underlying Kafka integration.

This example shows how to use the `@consumes` and `@produces` decorators
in a FastKafkaAPI application.

The `@consumes` decorator is applied to the `on_input_data` function,
which specifies that this function should be called whenever a message
is received on the “input_data” Kafka topic. The `on_input_data`
function takes a single argument, `msg`, which is expected to be an
instance of the `InputData` message class.

Inside the `on_input_data` function, the `model.predict` function is
called with the `feature_1` and `feature_2` fields from the `msg`
argument. This function returns a prediction score, which is then passed
to the `to_predictions` function along with the `user_id` field from the
`msg` argument.

The `@produces` decorator is applied to the `to_predictions` function,
which specifies that this function should produce a message to the
“predictions” Kafka topic whenever it is called. The `to_predictions`
function takes two arguments: `user_id` and `score`. It creates a new
`Prediction` message with these values and then returns it.

In summary, this example shows how to use the `@consumes` and
`@produces` decorators to specify the processing logic for Kafka
consumers and producers in a FastKafkaAPI application. The `@consumes`
decorator is applied to functions that should be called when a message
is received on a Kafka topic, and the `@produces` decorator is applied
to functions that should produce a message to a Kafka topic. These
decorators make it easy to specify the processing logic for your Kafka
consumers and producers, allowing you to focus on the core business
logic of your application without worrying about the underlying Kafka
integration.

``` python
@app.consumes(topic="input_data")
async def on_input_data(msg: InputData):
    print(f"msg={msg}")
    score = await model.predict(feature_1=msg.feature_1, feature_2=msg.feature_2)
    await to_predictions(user_id=msg.user_id, score=score)


@app.produces(topic="predictions")
async def to_predictions(user_id: int, score: float) -> Prediction:
    prediction = Prediction(user_id=user_id, score=score)
    print(f"prediction={prediction}")
    return prediction
```

### Running the service

This example shows how to start the FastKafkaAPI service using the
uvicorn library. The `uvicorn.run` function is called with the `app`
argument (which represents the FastKafkaAPI application) and the `host`
and `port` arguments, which specify the hostname and port on which the
service should listen for incoming requests.

When the service is started, several log messages are printed to the
console, including information about the application startup, AsyncAPI
specification generation, and consumer loop status.

During the lifetime of the service, incoming requests will be processed
by the FastKafkaAPI application and appropriate actions will be taken
based on the defined Kafka consumers and producers. For example, if a
message is received on the “input_data” Kafka topic, the `on_input_data`
function will be called to process the message, and if the
`to_predictions` function is called, it will produce a message to the
“predictions” Kafka topic. The service will continue to run until it is
shut down, at which point the application shutdown process will be
initiated and the service will stop.

``` python
import uvicorn

uvicorn.run(app._fast_api_app, host="0.0.0.0", port=4000)
```

    INFO:     Started server process [21284]
    INFO:     Waiting for application startup.

    [INFO] fast_kafka_api._components.asyncapi: Old async specifications at '/work/fast-kafka-api/nbs/asyncapi/spec/asyncapi.yml' does not exist.
    [INFO] fast_kafka_api._components.asyncapi: New async specifications generated at: 'asyncapi/spec/asyncapi.yml'
    [INFO] fast_kafka_api._components.asyncapi: Async docs generated at 'asyncapi/docs'
    [INFO] fast_kafka_api._components.asyncapi: Output of '$ npx -y -p @asyncapi/generator ag asyncapi/spec/asyncapi.yml @asyncapi/html-template -o asyncapi/docs --force-write'

    Done! ✨
    Check out your shiny new generated files at /work/fast-kafka-api/nbs/asyncapi/docs.


    [INFO] fast_kafka_api._components.aiokafka_consumer_loop: aiokafka_consumer_loop() starting..
    [INFO] fast_kafka_api._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer created.

    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://0.0.0.0:4000 (Press CTRL+C to quit)

    [INFO] fast_kafka_api._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer started.
    [INFO] aiokafka.consumer.subscription_state: Updating subscribed topics to: frozenset({'input_data'})
    [INFO] aiokafka.consumer.consumer: Subscribed to topic(s): {'input_data'}
    [INFO] fast_kafka_api._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer subscribed.
    [INFO] aiokafka.consumer.group_coordinator: Metadata for topic has changed from {} to {'input_data': 1}. 

    INFO:     Shutting down
    INFO:     Waiting for application shutdown.

    [INFO] fast_kafka_api._components.aiokafka_consumer_loop: aiokafka_consumer_loop(): Consumer stopped.
    [INFO] fast_kafka_api._components.aiokafka_consumer_loop: aiokafka_consumer_loop() finished.

    INFO:     Application shutdown complete.
    INFO:     Finished server process [21284]

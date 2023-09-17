---
hide:
  - navigation
  - footer
---

# Features of FastStream

<b>Effortless event stream integration for your services</b>

---

<p align="center">
  <a href="https://github.com/airtai/faststream/actions/workflows/test.yaml" target="_blank">
    <img src="https://github.com/airtai/faststream/actions/workflows/test.yaml/badge.svg?branch=main" alt="Test Passing"/>
  </a>

  <a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/airtai/faststream" target="_blank">
      <img src="https://coverage-badge.samuelcolvin.workers.dev/airtai/faststream.svg" alt="Coverage">
  </a>

  <a href="https://www.pepy.tech/projects/faststream" target="_blank">
    <img src="https://static.pepy.tech/personalized-badge/faststream?period=month&units=international_system&left_color=grey&right_color=green&left_text=downloads/month" alt="Downloads"/>
  </a>

  <a href="https://pypi.org/project/faststream" target="_blank">
    <img src="https://img.shields.io/pypi/v/faststream?label=PyPI" alt="Package version">
  </a>

  <a href="https://pypi.org/project/faststream" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/faststream.svg" alt="Supported Python versions">
  </a>

  <br/>

  <a href="https://github.com/airtai/faststream/actions/workflows/codeql.yml" target="_blank">
    <img src="https://github.com/airtai/faststream/actions/workflows/codeql.yml/badge.svg" alt="CodeQL">
  </a>

  <a href="https://github.com/airtai/faststream/actions/workflows/dependency-review.yaml" target="_blank">
    <img src="https://github.com/airtai/faststream/actions/workflows/dependency-review.yaml/badge.svg" alt="Dependency Review">
  </a>

  <a href="https://github.com/airtai/faststream/blob/main/LICENSE" target="_blank">
    <img src="https://img.shields.io/github/license/airtai/faststream.png" alt="Github">
  </a>

  <a href="https://discord.gg/CJWmYpyFbc" target="_blank">
      <img alt="Discord" src="https://img.shields.io/discord/1085457301214855171?logo=discord">
  </a>
</p>

---

[**FastStream**](https://faststream.airt.ai/) simplifies the process of writing producers and consumers for message queues, handling all the
parsing, networking and documentatino generation automatically.

Making streaming microservices has never been easier. Designed with junior developers in mind, **FastStream** simplifies your work while keeping the door open for more advanced use-cases. Here's a look at the core features that make **FastStream** a go-to framework for modern, data-centric microservices.

- **Multiple Brokers**: **FastStream** provides a unified API to work across multiple message brokers (**Kafka**, **RabbitMQ** support)

- [**Pydantic Validation**](#writing-app-code): Leverage [**Pydantic's**](https://docs.pydantic.dev/){.external-link target="_blank"} validation capabilities to serialize and validates incoming messages

- [**Automatic Docs**](#project-documentation): Stay ahead with automatic [AsyncAPI](https://www.asyncapi.com/){.external-link target="_blank"} documentation.

- **Intuitive**: full typed editor support makes your development experience smooth, catching errors before they reach runtime

- [**Powerful Dependency Injection System**](#dependencies): Manage your service dependencies efficiently with **FastStream**'s built-in DI system.

- [**Testable**](#testing-the-service): supports in-memory tests, making your CI/CD pipeline faster and more reliable

- **Extendable**: use extensions for lifespans, custom serialization and middlewares

- [**Integrations**](#any-framework): **FastStream** is fully compatible with any HTTP framework you want ([**FastAPI**](#fastapi-plugin) especially)

- **Built for Automatic Code Generation**: **FastStream** is optimized for automatic code generation using advanced models like GPT and Llama

That's **FastStream** in a nutshell—easy, efficient, and powerful. Whether you're just starting with streaming microservices or looking to scale, **FastStream** has got you covered.

---

## History

**FastStream** is a new package based on the ideas and experiences gained from [FastKafka](https://github.com/airtai/fastkafka){.external-link target="_blank"} and [Propan](https://github.com/lancetnik/propan){.external-link target="_blank"}. By joining our forces, we picked up the best from both packages and created the unified way to write services capable of processing streamed data regradless of the underliying protocol. We'll continue to maintain both packages, but new development will be in this project. If you are starting a new service, this package is the recommended way to do it.

---

## Install

**FastStream** works on **Linux**, **macOS**, **Windows** and most **Unix**-style operating systems.
You can install it with `pip` as usual:

=== "Kafka"
    ```sh
    pip install faststream[kafka]
    ```

=== "RabbitMQ"
    ```sh
    pip install faststream[rabbit]
    ```

!!! tip ""
    By default **FastStream** uses **PydanticV2** written in **Rust**, but you can downgrade it manually, if your platform has no **Rust** support - **FastStream** will works with the **PydanticV1** correctly as well.

---

## Writing app code

**FastStream** brokers provide convenient function decorators `#!python @broker.subscriber`
and `#!python @broker.publisher` to allow you to delegate the actual process of

- consuming and producing data to Event queues, and

- decoding and encoding JSON encoded messages

These decorators make it easy to specify the processing logic for your consumers and producers, allowing you to focus on the core business logic of your application without worrying about the underlying integration.

Also, **FastStream** uses [**Pydantic**](https://docs.pydantic.dev/){.external-link target="_blank"} to parse input
JSON-encoded data into Python objects, making it easy to work with structured data in your applications, so you can serialize you input messages just using type annotations.

Here is an example python app using **FastStream** that consumes data from an incoming data stream and outputs the data to another one.

=== "Kafka"
    ```python linenums="1" hl_lines="9"
from faststream import FastStream
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

@broker.subscriber("in-topic")
@broker.publisher("out-topic")
async def handle_msg(user: str, user_id: int) -> str:
    return f"User: {user_id} - {user} registered"
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="9"
from faststream import FastStream
from faststream.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)

@broker.subscriber("in-queue")
@broker.publisher("out-queue")
async def handle_msg(user: str, user_id: int) -> str:
    return f"User: {user_id} - {user} registered"
    ```

Also, **Pydantic**’s [`BaseModel`](https://docs.pydantic.dev/usage/models/){.external-link target="_blank"} class allows you
to define messages using a declarative syntax, making it easy to specify the fields and types of your messages.

=== "Kafka"
    ```python linenums="1" hl_lines="1 8 14"
from pydantic import BaseModel, Field, PositiveInt
from faststream import FastStream
from faststream.kafka import KafkaBroker

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

class User(BaseModel):
    user: str = Field(..., examples=["John"])
    user_id: PositiveInt = Field(..., examples=["1"])

@broker.subscriber("in-topic")
@broker.publisher("out-topic")
async def handle_msg(data: User) -> str:
    return f"User: {data.user} - {data.user_id} registered"
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="1 8 14"
from pydantic import BaseModel, Field, PositiveInt
from faststream import FastStream
from faststream.rabbit import RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)

class User(BaseModel):
    user: str = Field(..., examples=["John"])
    user_id: PositiveInt = Field(..., examples=["1"])

@broker.subscriber("in-queue")
@broker.publisher("out-queue")
async def handle_msg(data: User) -> str:
    return f"User: {data.user} - {data.user_id} registered"
    ```

---

## Testing the service

The service can be tested using the `TestBroker` context managers which, by default, puts the Broker into "testing mode".

The Tester will redirect your `subscriber` and `publisher` decorated functions to the InMemory brokers so that you can quickly test your app without the need for a running broker and all its dependencies.

Using pytest, the test for our service would look like this:

=== "Kafka"
    ```python linenums="1" hl_lines="3 10 18-19"
    # Code above omitted 👆

import pytest
import pydantic
from faststream.kafka import TestKafkaBroker


@pytest.mark.asyncio
async def test_correct():
    async with TestKafkaBroker(broker) as br:
        await br.publish({
            "user": "John",
            "user_id": 1,
        }, "in-topic")

@pytest.mark.asyncio
async def test_invalid():
    async with TestKafkaBroker(broker) as br:
        with pytest.raises(pydantic.ValidationError):
            await br.publish("wrong message", "in-topic")
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="3 10 18-19"
    # Code above omitted 👆

import pytest
import pydantic
from faststream.rabbit import TestRabbitBroker


@pytest.mark.asyncio
async def test_correct():
    async with TestRabbitBroker(broker) as br:
        await br.publish({
            "user": "John",
            "user_id": 1,
        }, "in-queue")

@pytest.mark.asyncio
async def test_invalid():
    async with TestRabbitBroker(broker) as br:
        with pytest.raises(pydantic.ValidationError):
            await br.publish("wrong message", "in-queue")
    ```

## Running the application

The application can be started using builtin **FastStream** CLI command.

To run the service, use the **FastStream CLI** command and pass the module (in this case, the file where the app implementation is located) and the app simbol to the command.

``` shell
faststream run basic:app
```

After running the command you should see the following output:

``` shell
INFO     - FastStream app starting...
INFO     - input_data |            - `HandleMsg` waiting for messages
INFO     - FastStream app started successfully! To exit press CTRL+C
```

Also, **FastStream** provides you a great hotreload feature to improve your Development Experience

``` shell
faststream run basic:app --reload
```

And multiprocessing horizontal scaling feature as well

``` shell
faststream run basic:app --workers 3
```

You can know more about **CLI** features [here](./getting-started/cli/index.md){.internal-link}

---

## Project Documentation

**FastStream** automatically generates documentation for your project according to the [**AsyncAPI**](https://www.asyncapi.com/){.external-link target="_blank"} specification. You can work with both generated artifacts and place a Web view of your documentation on resources available to related teams.

The availability of such documentation significantly simplifies the integration of services: you can immediately see what channels and message format the application works with. And most importantly, it won't cost anything - **FastStream** has already created the docs for you!

![HTML-page](../assets/img/AsyncAPI-basic-html-short.png)

---

## Dependencies

**FastStream** (thanks to [**FastDepend**](https://lancetnik.github.io/FastDepends/){.external-link target="_blank"}) has a dependency management system close to `pytest fixtures` and `FastAPI Depends` at the same time. Function arguments declare which dependencies you want are needed, and a special decorator delivers them from the global Context object.

```python linenums="1" hl_lines="9-10"
from faststream import Depends, Logger
async def base_dep(user_id: int) -> bool:
    return True

@broker.subscriber("in-test")
async def base_handler(user: str,
                       logger: Logger,
                       dep: bool = Depends(base_dep)):
    assert dep is True
    logger.info(user)
```

---

## HTTP Frameworks integrations

### Any Framework

You can use **FastStream** `MQBrokers` without `FastStream` application.
Just *start* and *stop* them according to your application lifespan.

{! includes/index/integrations.md !}

### **FastAPI** Plugin

Also, **FastStream** can be used as part of **FastAPI**.

Just import a **StreamRouter** you need and declare message handler with the same `#!python @router.subscriber(...)` and `#!python @router.publisher(...)` decorators.

!!! tip
    When used this way, **FastStream** does not utilize its own dependency and serialization system, but integrates into **FastAPI**.
    That is, you can use `Depends`, `BackgroundTasks` and other **FastAPI** tools as if it were a regular HTTP endpoint.

{! includes/getting_started/integrations/fastapi/1.md !}

!!! note
    More integration features can be found [here](./getting-started/integrations/fastapi/index.md){.internal-link}

---

## Stay in touch

Please show your support and stay in touch by:

- giving our [GitHub repository](https://github.com/airtai/faststream/) a star, and

- joining our [Discord server](https://discord.gg/CJWmYpyFbc)

Your support helps us to stay in touch with you and encourages us to
continue developing and improving the library. Thank you for your
support!

---

## Contributors

Thanks for all of these amazing peoples made the project better!

<a href="https://github.com/airtai/faststream/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=airtai/faststream"/>
</a>

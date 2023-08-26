<p align="center">
    <a href="https://lancetnik.github.io/Propan/" target="_blank">
        <img src="https://lancetnik.github.io/Propan/assets/img/logo-no-background.png" alt="Propan logo" style="height: 250px; width: 600px;"/>
    </a>
</p>

<p align="center">
    <a href="https://github.com/Lancetnik/Propan/actions/workflows/tests.yml" target="_blank">
        <img src="https://github.com/Lancetnik/Propan/actions/workflows/tests.yml/badge.svg" alt="Tests coverage"/>
    </a>
    <a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/lancetnik/propan" target="_blank">
        <img src="https://coverage-badge.samuelcolvin.workers.dev/lancetnik/propan.svg" alt="Coverage">
    </a>
    <a href="https://pypi.org/project/propan" target="_blank">
        <img src="https://img.shields.io/pypi/v/propan?label=pypi%20package" alt="Package version">
    </a>
    <a href="https://pepy.tech/project/propan" target="_blank">
        <img src="https://static.pepy.tech/personalized-badge/propan?period=total&units=international_system&left_color=grey&right_color=blue&left_text=Downloads" alt="downloads"/>
    </a>
    <br/>
    <a href="https://pypi.org/project/propan" target="_blank">
        <img src="https://img.shields.io/pypi/pyversions/propan.svg" alt="Supported Python versions">
    </a>
    <a href="https://github.com/Lancetnik/Propan/blob/main/LICENSE" target="_blank">
        <img alt="GitHub" src="https://img.shields.io/github/license/Lancetnik/Propan?color=%23007ec6">
    </a>
</p>

# Propan

**Propan** - just *~~an another one HTTP~~* a **declarative Python Messaging Framework**. It's inspired by <a href="https://FastAPI.tiangolo.com/ru/" target="_blank">*FastAPI*</a> and <a href="https://docs.celeryq.dev/projects/kombu/en/stable/" target="_blank">*Kombu*</a>, simplify Message Brokers around code writing and provides a helpful development toolkit, which existed only in HTTP-frameworks world until now.

It's designed to create reactive microservices around <a href="https://microservices.io/patterns/communication-style/messaging.html" target="_blank">Messaging Architecture</a>.

It is a modern, high-level framework on top of popular specific Python brokers libraries, based on <a href="https://docs.pydantic.dev/" target="_blank">*pydantic*</a> and <a href="https://FastAPI.tiangolo.com/ru/" target="_blank">*FastAPI*</a>, <a href="https://docs.pytest.org/en/latest/" target="_blank">*pytest*</a> concepts.

---

**Documentation**: <a href="https://lancetnik.github.io/Propan/" target="_blank">https://lancetnik.github.io/Propan/</a>

---

### The key features are

* **Simple**: Designed to be easy to use and learn.
* **Intuitive**: Great editor support. Autocompletion everywhere.
* [**Dependencies management**](#dependencies): Minimization of code duplication. Access to dependencies at any level of the call stack.
* [**Integrations**](#http-frameworks-integrations): **Propan** is fully compatible with <a href="https://lancetnik.github.io/Propan/integrations/1_integrations-index/" target="_blank">any HTTP framework</a> you want
* **MQ independent**: Single interface to popular MQ:
  * **Redis** (based on <a href="https://redis.readthedocs.io/en/stable/index.html" target="_blank">redis-py</a>)
  * **RabbitMQ** (based on <a href="https://aio-pika.readthedocs.io/en/latest/" target="_blank">aio-pika</a>)
  * **Kafka** (based on <a href="https://aiokafka.readthedocs.io/en/stable/" target="_blank">aiokafka</a>)
  * **SQS** (based on <a href="https://aiobotocore.readthedocs.io/en/latest/" target="_blank">aiobotocore</a>)
  * **Nats** (based on <a href="https://github.com/nats-io/nats.py" target="_blank">nats-py</a>)
* <a href="https://lancetnik.github.io/Propan/getting_started/4_broker/5_rpc/" target="_blank">**RPC**</a>: The framework supports RPC requests over MQ, which will allow performing long operations on remote services asynchronously.
* [**Great to develop**](#cli-power): CLI tool provides great development experience:
  * framework-independent way to manage the project environment
  * application code *hot reload*
  * robust application templates
* [**Documentation**](#project-documentation): **Propan** automatically generates and presents an interactive <a href="https://www.asyncapi.com/" target="_blank">**AsyncAPI**</a> documentation for your project
* <a href="https://lancetnik.github.io/Propan/getting_started/7_testing" target="_blank">**Testability**</a>: **Propan** allows you to test your app without external dependencies: you do not have to set up a Message Broker, you can use a virtual one!

### Supported MQ brokers

|                   | async                                                   | sync                                        |
|-------------------|:-------------------------------------------------------:|:-------------------------------------------:|
| **RabbitMQ**      | :heavy_check_mark: **stable** :heavy_check_mark:        | :hammer_and_wrench: WIP :hammer_and_wrench: |
| **Redis**         | :heavy_check_mark: **stable** :heavy_check_mark:        | :mag: planning :mag:                        |
| **Nats**          | :heavy_check_mark: **stable** :heavy_check_mark:        | :mag: planning :mag:                        |
| **Kafka**         | :warning: **beta** :warning:                            | :mag: planning :mag:                        |
| **SQS**           | :warning: **beta** :warning:                            | :mag: planning :mag:                        |
| **NatsJS**        | :warning: **beta** :warning:                            | :mag: planning :mag:                        |
| **ZeroMQ**        | :hammer_and_wrench: WIP :hammer_and_wrench:             | :mag: planning :mag:                        |
| **MQTT**          | :mag: planning :mag:                                    | :mag: planning :mag:                        |
| **Redis Streams** | :mag: planning :mag:                                    | :mag: planning :mag:                        |
| **Pulsar**        | :mag: planning :mag:                                    | :mag: planning :mag:                        |
| **ActiveMQ**      | :mag: planning :mag:                                    | :mag: planning :mag:                        |
| **AzureSB**       | :mag: planning :mag:                                    | :mag: planning :mag:                        |

---

### ⭐ Support the project ⭐

If you are interested in this project, please give me feedback by:

- giving the [repository](https://github.com/Lancetnik/Propan) a star

- tweet about <a href="https://twitter.com/compose/tweet?text=I'm like @PropanFramework because... https://github.com/Lancetnik/Propan" class="external-link" target="_blank">**Propan**</a> and let me and others know why you use it

- joining <a href="https://discord.gg/ChhMXJpvz7" target="_blank">Discord server</a>

Your support helps me to stay in touch with you and encourages to
continue developing and improving the library. Thank you for your
support!

Really, share information about this project with others. The bigger community we have - the better project will be!

---

## Declarative?

With declarative tools you can define **what you need to get**. With traditional imperative tools you must write **what you need to do**.

Take a look at classic imperative tools, such as <a href="https://aio-pika.readthedocs.io/en/latest/" target="_blank">aio-pika</a>, <a href="https://pika.readthedocs.io/en/stable/" target="_blank">pika</a>, <a href="https://redis.readthedocs.io/en/stable/index.html" target="_blank">redis-py</a>, <a href="https://github.com/nats-io/nats.py" target="_blank">nats-py</a>, etc.

This is the **Quickstart** with the *aio-pika*:

```python
import asyncio
import aio_pika

async def main():
    connection = await aio_pika.connect_robust(
        "amqp://guest:guest@127.0.0.1/"
    )

    queue_name = "test_queue"

    async with connection:
        channel = await connection.channel()

        queue = await channel.declare_queue(queue_name)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    print(message.body)

asyncio.run(main())
```

**aio-pika** is a great tool with a really easy learning curve. But it's still imperative. You need to *connect*, declare *channel*, *queues*, *exchanges* by yourself. Also, you need to manage *connection*, *message*, *queue* context to avoid any troubles.

It is not a bad way, but it can be much easier.

```python
from propan import FastStream, RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)

@broker.handle("test_queue")
async def base_handler(body):
    print(body)
```

This is the **Propan** declarative way to write the same code. That is so much easier, isn't it?

---

## Quickstart

Install using `pip`:

```shell
pip install "propan[rabbit]"
# or
pip install "propan[async-nats]"
# or
pip install "propan[async-redis]"
# or
pip install "propan[kafka]"
# or
pip install "propan[async-sqs]"
```

### Basic usage

Create an application with the following code at `serve.py`:

```python
from propan import FastStream
from propan import RabbitBroker
# from propan import RedisBroker
# from propan import NatsBroker
# from propan import SQSBroker
# from propan import KafkaBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
# broker = NatsBroker("nats://localhost:4222")
# broker = RedisBroker("redis://localhost:6379")
# broker = SQSBroker("http://localhost:9324", ...)
# broker = KafkaBroker("localhost:9092")

app = FastStream(broker)

@broker.handle("test")
async def base_handler(body):
    print(body)
```

And just run it:

```shell
propan run serve:app --workers 3
```

---

## Type casting

Propan uses `pydantic` to cast incoming function arguments to types according to their annotation.

```python
from pydantic import BaseModel
from propan import FastStream, RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(broker)

class SimpleMessage(BaseModel):
    key: int

@broker.handle("test2")
async def second_handler(body: SimpleMessage):
    assert isinstance(body.key, int)

```

---

## Dependencies

**Propan** a has dependencies management policy close to `pytest fixtures` and `FastAPI Depends` at the same time.
You can specify in functions arguments which dependencies
you would to use. Framework passes them from the global Context object.

Also, you can specify your own dependencies, call dependencies functions and
[more](https://github.com/Lancetnik/Propan/tree/main/examples/dependencies).

```python
from propan import FastStream, RabbitBroker, Context, Depends

rabbit_broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(rabbit_broker)

async def dependency(user_id: int) -> bool:
    return True

@rabbit_broker.handle("test")
async def base_handler(user_id: int,
                       dep: bool = Depends(dependency),
                       broker: RabbitBroker = Context()):
    assert dep is True
    assert broker is rabbit_broker
```

---

## RPC over MQ

Also, **Propan** allows you to use **RPC** requests over your broker with a simple way:

```python
from propan import FastStream, RabbitBroker

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")
app = FastStream(rabbit_broker)

@broker.handle("ping")
async def base_handler():
    return "pong"

@app.after_startup
async def self_ping():
    assert (
        await broker.publish("", "ping", callback=True)
    ) == "pong"
```

---

## Project Documentation

**Propan** automatically generates documentation for your project according to the <a href="https://www.asyncapi.com/" target="_blank">**AsyncAPI**</a> specification. You can work with both generated artifacts and place a Web view of your documentation on resources available to related teams.

The availability of such documentation significantly simplifies the integration of services: you can immediately see what channels and message format the application works with. And most importantly, it doesn't cost you anything - **Propan** has already done everything for you!

![HTML-page](https://lancetnik.github.io/Propan/assets/img/docs-html-short.png)

---

## CLI power

**Propan** has its own CLI tool that provided the following features:

* project generation
* multiprocessing workers
* project hot reloading
* documentation generating and hosting
* custom command line arguments passing

### Context passing

For example: pass your current *.env* project setting to context

```bash
propan run serve:app --env=.env.dev
```

```python
from propan import FastStream, RabbitBroker
from propan.annotations import ContextRepo
from pydantic import BaseSettings

broker = RabbitBroker("amqp://guest:guest@localhost:5672/")

app = FastStream(broker)

class Settings(BaseSettings):
    ...

@app.on_startup
async def setup(env: str, context: ContextRepo):
    settings = Settings(_env_file=env)
    context.set_global("settings", settings)
```

### Project template

Also, **Propan CLI** is able to generate a production-ready application template:

```bash
propan create async rabbit [projectname]
```

*Notice: project template require* `pydantic[dotenv]` *installation.*

Run the created project:

```bash
# Run rabbimq first
docker compose --file [projectname]/docker-compose.yaml up -d

# Run project
propan run [projectname].app.serve:app --env=.env --reload
```

Now you can enjoy a new development experience!

---

## HTTP Frameworks integrations

### Any Framework

You can use **Propan** `MQBrokers` without `FastStream`.
Just *start* and *stop* them according to your application lifespan.

```python
from propan import NatsBroker
from sanic import Sanic

app = Sanic("MyHelloWorldApp")
broker = NatsBroker("nats://localhost:4222")

@broker.handle("test")
async def base_handler(body):
    print(body)

@app.after_server_start
async def start_broker(app, loop):
    await broker.start()

@app.after_server_stop
async def stop_broker(app, loop):
    await broker.close()
```

### FastAPI Plugin

Also, **Propan** can be used as part of **FastAPI**.

Just import a **PropanRouter** you need and declare the message handler
using the `@event` decorator. This decorator is similar to the decorator `@handle` for the corresponding brokers.

```python
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from propan.fastapi import RabbitRouter

router = RabbitRouter("amqp://guest:guest@localhost:5672")
app = FastAPI(lifespan=router.lifespan_context)

class Incoming(BaseModel):
    username: str

def call():
    return True

@router.event("test")
async def hello(m: Incoming, d = Depends(call)):
    return { "response": f"Hello, {m.username}!" }

app.include_router(router)
```

## Examples

To see more framework usages go to [**examples/**](https://github.com/Lancetnik/Propan/tree/main/examples)

## Contributors

Thanks for all of these amazing peoples made the project better!

<a href="https://github.com/Lancetnik/Propan/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Lancetnik/Propan"/>
</a>

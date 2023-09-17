# Basic Subscriber

To start consuming from a Kafka topic just decorate your consuming function with a `#!python @broker.subscriber(...)` decorator passing a string as a topic key.

In the folowing example we will create a simple FastStream app that will consume `HelloWorld` messages from a **hello_world** topic.

The full app code looks like this:

```python linenums="1"
{!> docs_src/kafka/consumes_basics/app.py!}
```

## Import FastStream and KafkaBroker

To use the `#!python @broker.subscriber(...)` decorator, first we need to import the base FastStream app KafkaBroker to create our broker.

```python linenums="1"
{!> docs_src/kafka/consumes_basics/app.py [ln:3-4] !}
```

## Define the HelloWorld message structure

Next, you need to define the structure of the messages you want to consume from the topic using pydantic. For the guide we’ll stick to something basic, but you are free to define any complex message structure you wish in your project.

```python linenums="1"
{!> docs_src/kafka/consumes_basics/app.py [ln:7-12] !}
```

## Create a KafkaBroker

Next, we will create a `KafkaBroker` object and wrap it into the `FastStream` object so that we can start our app using CLI later.

```python linenums="1"
{!> docs_src/kafka/consumes_basics/app.py [ln:15-16] !}
```

## Create a function that will consume messages from a Kafka hello-world topic

Let’s create a consumer function that will consume `HelloWorld` messages from **hello_world** topic and log them.

```python linenums="1"
{!> docs_src/kafka/consumes_basics/app.py [ln:19-21] !}
```

The function decorated with the `#!python @broker.subscriber(...)` decorator will be called when a message is produced to Kafka.

The message will then be injected into the typed msg argument of the function and its type will be used to parse the message.

In this example case, when the message is sent into a **hello_world** topic, it will be parsed into a `HelloWorld` class and `on_hello_world` function will be called with the parsed class as msg argument value.

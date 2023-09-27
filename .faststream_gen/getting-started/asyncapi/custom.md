# Customizing AsyncAPI Documentation for FastStream

In this guide, we will explore how to customize AsyncAPI documentation for your FastStream application. Whether you want to add custom app info, broker information, handlers, or fine-tune payload details, we'll walk you through each step.

## Prerequisites

Before we dive into customization, ensure you have a basic FastStream application up and running. If you haven't done that yet, let's setup a simple appication right now.

Copy the following code in your basic.py file:

```python linenums="1"
from faststream import FastStream
from faststream.kafka import KafkaBroker, KafkaMessage

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

@broker.publisher("output_data")
@broker.subscriber("input_data")
async def on_input_data(msg):
    # your processing logic
    pass
```

faststream docs serve basic:app

![HTML-page](../../../assets/img/AsyncAPI-basic-html-short.png)

## Setup Custom FastStream App Info

Let's start by customizing the app information that appears in your AsyncAPI documentation. This is a great way to give your documentation a personal touch. Here's how:

1. Locate the app configuration in your FastStream application.
1. Update the `title`, `version`, and `description` fields to reflect your application's details.
1. Save the changes.
1. Serve your FastStream app documentation.

Copy the following code in your basic.py file, we have highligted the additional info passed to FastStream app:

```python linenums="1" hl_lines="7-12"
from faststream import FastStream
from faststream.kafka import KafkaBroker, KafkaMessage
from faststream.asyncapi.schema import Contact, ExternalDocs, License, Tag

broker = KafkaBroker("localhost:9092")
app = FastStream(broker,
            title="My App",
            version="1.0.0",
            description="Test description",
            license=License(name="MIT", url="https://opensource.org/license/mit/"),
            terms_of_service="https://my-terms.com/",
            contact=Contact(name="support", url="https://help.com/"),
        )

@broker.publisher("output_data")
@broker.subscriber("input_data")
async def on_input_data(msg):
    # your processing logic
    pass
```

faststream docs serve basic:app

![HTML-page](../../../assets/img/AsyncAPI-basic-html-short.png)

Now, your documentation reflects your application's identity and purpose.

## Setup Custom Broker Information

The next step is to customize broker information. This helps users understand the messaging system your application uses. Follow these steps:

1. Locate the broker configuration in your FastStream application.
1. Update the `description` field.
1. Save the changes.
1. Serve your FastStream app.

Copy the following code in your basic.py file, we have highligted the additional info passed to the FastStream app broker:

```python linenums="1" hl_lines="5"
from faststream import FastStream
from faststream.kafka import KafkaBroker, KafkaMessage
from faststream.asyncapi.schema import Tag

broker = KafkaBroker("localhost:9092", description="Kafka broker running locally")
app = FastStream(broker)

@broker.publisher("output_data")
@broker.subscriber("input_data")
async def on_input_data(msg):
    # your processing logic
    pass
```

faststream docs serve basic:app

![HTML-page](../../../assets/img/AsyncAPI-basic-html-short.png)

Your AsyncAPI documentation now provides clear insights into the messaging infrastructure you're using.

## Setup Custom Handler Information

Customizing handler information helps users comprehend the purpose and behavior of each message handler. Here's how to do it:

1. Navigate to your handler definitions in your FastStream application.
1. Add descriptions to each handler using `description` field.
1. Save the changes.
1. Serve your FastStream app.

Copy the following code in your basic.py file, we have highligted the additional info passed to the FastStream app handlers:

```python linenums="1" hl_lines="7-8"
from faststream import FastStream
from faststream.kafka import KafkaBroker, KafkaMessage

broker = KafkaBroker("localhost:9092")
app = FastStream(broker)

@broker.publisher("output_data", description="My publisher description")
@broker.subscriber("input_data", description="My subscriber description")
async def on_input_data(msg):
    # your processing logic
    pass
```

faststream docs serve basic:app

![HTML-page](../../../assets/img/AsyncAPI-basic-html-short.png)

Now, your documentation is enriched with meaningful details about each message handler.

## Setup Payload Information via Pydantic Model

To describe your message payload effectively, you can use Pydantic models. Here's how:

1. Define Pydantic models for your message payloads.
1. Annotate these models with descriptions and examples.
1. Use these models as argument types or return types in your handlers.
1. Save the changes.
1. Serve your FastStream app.

Copy the following code in your basic.py file, we have highligted the creation of payload info and you can see it being passed to the return type and the `msg` argument type in the `on_input_data` function:

```python linenums="1" hl_lines="5"
from pydantic import BaseModel, Field, NonNegativeFloat

from faststream import FastStream
from faststream.kafka import KafkaBroker


class DataBasic(BaseModel):
    data: NonNegativeFloat = Field(
        ..., examples=[0.5], description="Float data example"
    )


broker = KafkaBroker("localhost:9092")
app = FastStream(broker)


@broker.publisher("output_data")
@broker.subscriber("input_data")
async def on_input_data(msg: DataBasic) -> DataBasic:
    # your processing logic
    pass
```

faststream docs serve basic:app

![HTML-page](../../../assets/img/AsyncAPI-basic-html-short.png)

Your AsyncAPI documentation now showcases well-structured payload information.

## Generate Schema.json, Customize Manually, and Serve It

To take customization to the next level, you can manually modify the schema.json file. Follow these steps:

faststream docs gen basic:app
1. Manually edit the asyncapi.json file to add custom fields, descriptions, and details.
1. Save your changes.
faststream docs serve asyncapi.json

Now, you have fine-tuned control over your AsyncAPI documentation.

## Conclusion

Customizing AsyncAPI documentation for your FastStream application not only enhances its appearance but also provides valuable insights to users. With these steps, you can create documentation that's not only informative but also uniquely yours.

Happy coding with your customized FastStream AsyncAPI documentation!

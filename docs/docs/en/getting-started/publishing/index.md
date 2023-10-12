# Publishing Basics

**FastStream** is broker-agnostic and easy to use, even as a client in non-**FastStream** applications.

It offers several use cases for publishing messages:

* Using `#!python broker.publish(...)`
* Using a `#!python @broker.publisher(...)` decorator
* Using a publisher object decorator
* Using a publisher object directly

All of these variants have their own advantages and limitations, so you can choose you want based on your demands. Please, visit the following pages for details.

## Serialization

**FastStream** allows you to publish any JSON-serializable messages (Python types, Pydantic models, etc.) or raw bytes.

It automatically sets up all required headers, especially the `correlation_id`, which is used to trace message processing pipelines across all services.

`content-type` is a meaningfull header for **FastStream** services. It helps framework to serialize messages faster, selecting the right serializer based on the header. This header is setted automatically by **FastStream** too, but you should set it up manually using another libraries to interact with **FastStream** application.

Content-Type can be:

* `text/plain`
* `application/json`
* empty with bytes content

Btw, you can use `application/json` for all of your messages if they are not raw bytes. You can event don't use any header at all, but it makes serialization slower a bit.

## Publishing

**FastStream** also can be used as just a Broker client to send messages in your another applications. It is a really easy and pretty close to *aiohttp* or *requests*.

You just need to `#!python connect` your broker - and you are already able to send a message. Also, you can use *Broker* as an async context manager to connect and disconnect at scope exit.

To publish a message, simply set up the message content and a routing key:

{!> includes/getting_started/publishing/index.md !}

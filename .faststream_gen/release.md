---
hide:
  - navigation
  - footer
---

# Release Notes

**FastStream** is a new package based on the ideas and experiences gained from [FastKafka](https://github.com/airtai/fastkafka) and [Propan](https://github.com/lancetnik/propan). By joining our forces, we picked up the best from both packages and created the unified way to write services capable of processing streamed data regradless of the underliying protocol. We'll continue to maintain both packages, but new development will be in this project. If you are starting a new service, this package is the recommended way to do it.

## Features

[**FastStream**](https://faststream.airt.ai/) simplifies the process of writing producers and consumers for message queues, handling all the
parsing, networking and documentation generation automatically.

Making streaming microservices has never been easier. Designed with junior developers in mind, **FastStream** simplifies your work while keeping the door open for more advanced use-cases. Here's a look at the core features that make **FastStream** a go-to framework for modern, data-centric microservices.

- **Multiple Brokers**: **FastStream** provides a unified API to work across multiple message brokers (**Kafka**, **RabbitMQ** support)

- [**Pydantic Validation**](#writing-app-code): Leverage [**Pydantic's**](https://docs.pydantic.dev/) validation capabilities to serialize and validates incoming messages

- [**Automatic Docs**](#project-documentation): Stay ahead with automatic [AsyncAPI](https://www.asyncapi.com/) documentation.

- **Intuitive**: full typed editor support makes your development experience smooth, catching errors before they reach runtime

- [**Powerful Dependency Injection System**](#dependencies): Manage your service dependencies efficiently with **FastStream**'s built-in DI system.

- [**Testable**](#testing-the-service): supports in-memory tests, making your CI/CD pipeline faster and more reliable

- **Extendable**: use extensions for lifespans, custom serialization and middlewares

- [**Integrations**](#any-framework): **FastStream** is fully compatible with any HTTP framework you want ([**FastAPI**](#fastapi-plugin) especially)

- **Built for Automatic Code Generation**: **FastStream** is optimized for automatic code generation using advanced models like GPT and Llama

That's **FastStream** in a nutshell—easy, efficient, and powerful. Whether you're just starting with streaming microservices or looking to scale, **FastStream** has got you covered.

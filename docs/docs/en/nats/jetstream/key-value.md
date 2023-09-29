# Key-Value Storage

## Overview

[*Key-Value*](https://docs.nats.io/nats-concepts/jetstream/key-value-store){.external-link target="_blank"} storage is just a high-level interface on top of *NatsJS*.

It is a regular *JetStream*, where the *KV key* is a subject.

`Put`/`Update` an object to *KV* by *key* - it's like publishing a new message to the corresponding subject in the stream.

Thus, the `Get` command returns not only the current *key* value but the latest one with an offset of it. Additionally, you can ask for a specific value based on its offset in the *KV* stream.

This interface provides you with rich abilities to use it like a regular *KV* storage (ignoring offset) + subscribe to *KV key* changes + ask for an old *KV value* revision. So you can use this feature in your application in a really different way. You can find some examples on the *NATS* developers' official [YouTube channel](https://youtube.com/@NATS_io?si=DWHvNFjsLruxg5OZ){.external-link target="_blank"}

## FastStream Details

**FastStream** has no native interfaces to this *NatsJS* functionality (yet), but it allows you to get access into the inner `JetStream` object to create it manually.

First of all, you need to create a *Key-Value* storage object and pass it into the context:

```python linenums="1" hl_lines="14-15"
{!> docs_src/nats/js/key_value.py [ln:5-7,11-12,22-27] !}
```

!!! tip
    We placed this code in `#!python @app.on_startup` hook because `#!python @app.after_startup` will be triggered **AFTER** your handlers start consuming messages. So, if you need to have access to any custom context objects, you should set them up in the `#!python @app.on_startup` hook.

    Also, we call `#!python await broker.connect()` method manually to establish the connection to be able to create a storage.

---

Next, we are ready to use this object right in our handlers.

Let's create an annotated object to shorten context object access:

```python linenums="1" hl_lines="5"
{!> docs_src/nats/js/key_value.py [ln:1-2,9] !}
```

And just use it in a handler:

```python linenums="1" hl_lines="4 7-8"
{!> docs_src/nats/js/key_value.py [ln:4,15-19] !}
```

Finally, let's test our code behavior by putting something into the KV storage and sending a message:

```python linenums="1" hl_lines="3-4"
{!> docs_src/nats/js/key_value.py [ln:30-33] !}
```

??? example "Full listing"
    ```python linenums="1"
    {!> docs_src/nats/js/key_value.py !}
    ```

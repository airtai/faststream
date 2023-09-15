---
# template variables
note_decor: Now you can use the created router to register handlers and publishers as if it were a regular broker
note_include: Then you can simply include all the handlers declared using the router in your broker
note_publish: Please note that when publishing a message, you now need to specify the same prefix that you used when creating the router
---

# Broker Router

Sometimes you want to:

* split an application to includable modules
* separate business logic from you handler registration
* apply some [decoder](../serialization/index.md)/[middleware](../middlewares/index.md)/[dependencies](../dependencies/global.md) to subscribers group

This reason **FastStream** has a special *Broker Router*.

## Router usage

First you need to import *Broker Router* from the same module from where you imported the broker.

!!! note ""
    When creating, you can specify a prefix that will be automatically applied to all subscribers and publishers of this router.

{% import 'getting_started/routers/1.md' as includes with context %}
{{ includes }}

!!! tip
    Also, at *Broker Router* creation you can specify [middleware](../middlewares/index.md), [dependencies](../dependencies/global.md), [parser](../serialization/parser.md) and [decoder](../serialization/decoder.md) to apply them to all subscribers, declared via this router.

## Delay handler registration

If you want to separate your application core logic from **FastStream** routing one, you can just write some core functions and use them as a *Broker Router* `handlers` lately:

=== "Kafka"
    ```python linenums="1" hl_lines="2 8 13 15"
    {!> docs_src/getting_started/routers/router_delay_kafka.py [ln:1-15] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="2 8 13 15"
    {!> docs_src/getting_started/routers/router_delay_rabbit.py [ln:1-15] !}
    ```

!!! warning
    Be careful, this way you have no ability to test you handlers with a [`mock`](../subscription/test.md) object.

---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Broker Publishing

The easiest way to publish a message is to use a Broker, which allows you to use it as a publisher client in any applications.

In the **FastStream** project, this call is not represented in the **AsyncAPI** scheme. You can use it to send rarely-publishing messages, such as startup or shutdown events.

=== "AIOKafka"
    ```python linenums="1" hl_lines="10 20"
    {!> docs_src/getting_started/publishing/kafka/broker.py !}
    ```

=== "Confluent"
    ```python linenums="1" hl_lines="10 20"
    {!> docs_src/getting_started/publishing/confluent/broker.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="10 20"
    {!> docs_src/getting_started/publishing/rabbit/broker.py !}
    ```

=== "NATS"
    ```python linenums="1" hl_lines="10 20"
    {!> docs_src/getting_started/publishing/nats/broker.py !}
    ```

=== "Redis"
    ```python linenums="1" hl_lines="10 20"
    {!> docs_src/getting_started/publishing/redis/broker.py !}
    ```

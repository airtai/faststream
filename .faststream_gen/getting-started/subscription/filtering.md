# Application-level Filtering

**FastStream** also allows you to specify the message processing way using message headers, body type or something else. The `filter` feature enables you to consume various messages with different schemas within a single event stream.

!!! tip
    Message must be consumed at ONCE (crossing filters are not allowed)

As an example, let's create a subscriber for both `JSON` and non-`JSON` messages:

=== "Kafka"
    ```python linenums="1" hl_lines="10 17"
    {!> docs_src/getting_started/subscription/filter_kafka.py [ln:1-19] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="10 17"
    {!> docs_src/getting_started/subscription/filter_rabbit.py [ln:1-19] !}
    ```

!!! note
    A subscriber without a filter is a default subscriber. It consumes messages that have not been consumed yet.

For now, the following message will be delivered to the `handle` function

=== "Kafka"
    ```python hl_lines="2"
    {!> docs_src/getting_started/subscription/filter_kafka.py [ln:24-27] !}
    ```

=== "RabbitMQ"
    ```python hl_lines="2"
    {!> docs_src/getting_started/subscription/filter_rabbit.py [ln:24-27] !}
    ```

And this one will be delivered to the `default_handler`

=== "Kafka"
    ```python hl_lines="2"
    {!> docs_src/getting_started/subscription/filter_kafka.py [ln:29-32] !}
    ```

=== "RabbitMQ"
    ```python hl_lines="2"
    {!> docs_src/getting_started/subscription/filter_rabbit.py [ln:29-32] !}
    ```

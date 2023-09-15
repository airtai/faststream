# Application-level filtering

Also, **FastStream** allows you to specify message processing way by message headers, body type or smth else. Using `filter` feature you are able to consume various messages with different schemas in the one event stream.

!!! tip
    Message must be consumed at ONCE (crossing filters are not allowed)

As an example lets create a subscriber for `JSON` and not-`JSON` messages both:

=== "Kafka"
    ```python linenums="1" hl_lines="10 17"
    {!> docs_src/getting_started/subscription/filter_kafka.py [ln:1-19] !}
    ```

=== "RabbitMQ"
    ```python linenums="1" hl_lines="10 17"
    {!> docs_src/getting_started/subscription/filter_rabbit.py [ln:1-19] !}
    ```

!!! note
    Subscriber without filter is a default subscriber. It consumes messages, not consumed yet.


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

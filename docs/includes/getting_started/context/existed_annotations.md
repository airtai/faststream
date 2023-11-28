=== "Kafka"
    ```python
    from faststream.kafka.annotations import (
        Logger, ContextRepo, KafkaMessage, KafkaBroker, KafkaProducer
    )
    ```

    !!! tip ""
        `faststream.kafka.KafkaMessage` is an alias to `faststream.kafka.annotations.KafkaMessage`

        ```python
        from faststream.kafka import KafkaMessage
        ```

    To use them, simply import and use them as subscriber argument annotations.

    ```python linenums="1" hl_lines="3-8 17-20"
    {!> docs_src/getting_started/context/existed_context_kafka.py [ln:1-11,26-35] !}
    ```

=== "RabbitMQ"
    ```python
    from faststream.rabbit.annotations import (
        Logger, ContextRepo, RabbitMessage, RabbitBroker, RabbitProducer
    )
    ```

    !!! tip ""
        `faststream.rabbit.RabbitMessage` is an alias to `faststream.rabbit.annotations.RabbitMessage`

        ```python
        from faststream.rabbit import RabbitMessage
        ```

    To use them, simply import and use them as subscriber argument annotations.

    ```python linenums="1" hl_lines="3-8 17-20"
    {!> docs_src/getting_started/context/existed_context_rabbit.py [ln:1-11,26-35] !}
    ```

=== "NATS"
    ```python
    from faststream.nats.annotations import (
        Logger, ContextRepo, NatsMessage,
        NatsBroker, NatsProducer, NatsJsProducer,
        Client, JsClient,
    )
    ```

    !!! tip ""
        `faststream.nats.NatsMessage` is an alias to `faststream.nats.annotations.NatsMessage`

        ```python
        from faststream.nats import NatsMessage
        ```
    To use them, simply import and use them as subscriber argument annotations.

    ```python linenums="1" hl_lines="3-8 17-20"
    {!> docs_src/getting_started/context/existed_context_nats.py [ln:1-11,26-35] !}
    ```

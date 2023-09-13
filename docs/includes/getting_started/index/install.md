=== "Kafka"
    ```console
    pip install "faststream[kafka]"
    ```

    !!! tip
        {{ run_docker }}
        ```bash
        docker run -d --rm -p 9092:9092 --name test-mq \
        -e KAFKA_ENABLE_KRAFT=yes \
        -e KAFKA_CFG_NODE_ID=1 \
        -e KAFKA_CFG_PROCESS_ROLES=broker,controller \
        -e KAFKA_CFG_CONTROLLER_LISTENER_NAMES=CONTROLLER \
        -e KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 \
        -e KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT \
        -e KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://127.0.0.1:9092 \
        -e KAFKA_BROKER_ID=1 \
        -e KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=1@kafka:9093 \
        -e ALLOW_PLAINTEXT_LISTENER=yes \
        bitnami/kafka:3.5.0
        ```

=== "RabbitMQ"
    ```console
    pip install "faststream[rabbit]"
    ```

    !!! tip
        {{ run_docker }}
        ```bash
        docker run -d --rm -p 5672:5672 --name test-mq rabbitmq:alpine
        ```

# Subscriber testing

Original application

=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/subscription/annotation_kafka.py [ln:7-10]!}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/subscription/annotation_kafka.py [ln:7-10]!}
    ```

* in-memory TestClient
* publishing (show error raising)
* check incoming message body
* note about mock clearing after context exit

=== "Kafka"
    ```python linenums="1"
    {!> docs_src/getting_started/subscription/testing_kafka.py !}
    ```

=== "RabbitMQ"
    ```python linenums="1"
    {!> docs_src/getting_started/subscription/testing_rabbit.py !}
    ```

* test with real broker
* wait consumer called

Show pytests setup toggle example (details in the application [config](../config/index.md){.internal-link}):

```console
REAL=True/False pytest tests
```

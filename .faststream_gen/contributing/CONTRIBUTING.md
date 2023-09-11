# Development

If you already cloned the repository and you know that you need to deep dive in the code, here are some guidelines to set up your environment.

## Virtual environment with `venv`

You can create a virtual environment in a directory using Python's `venv` module:

```bash
python -m venv venv
```

That will create a directory `./venv/` with the Python binaries and then you will be able to install packages for that isolated environment.

## Activate the environment

Activate the new environment with:

```bash
source ./venv/bin/activate
```

Make sure you have the latest pip version on your virtual environment to

```bash
python -m pip install --upgrade pip
```

## pip

After activating the environment as described above:

```bash
pip install -e ".[dev]"
```

It will install all the dependencies and your local FastStream in your local environment.

### Using your local FastStream

If you create a Python file that imports and uses FastStream, and run it with the Python from your local environment, it will use your local FastStream source code.

And if you update that local FastStream source code, as it is installed with `-e`, when you run that Python file again, it will use the fresh version of FastStream you just edited.

That way, you don't have to "install" your local version to be able to test every change.

To use your local FastStream cli type:

```bash
python -m faststream ...
```

## Tests

### Pytest

To run tests with your current FastStream application and Python environment use:

```bash
pytest tests
# or
./scripts/test.sh
# with coverage output
./scripts/test-cov.sh -m "all"
```

There are some *pytest marks* at project:

* **slow**
* **rabbit**
* **kafka**
* **all**

Default *pytest* calling runs "not slow" tests.

To run all tests use:

```bash
pytest -m 'all'
```

Also if you didn't up local rabbit or kafka intance, run tests without that dependencies

```bash
pytest -m 'not rabbit and not kafka'
```

To run all tests based on RabbitMQ, Kafka or another dependencies you should run first following *docker-compose.yml*

```yaml
version: "3"

services:
    rabbitmq:
        image: rabbitmq:alpine
        ports:
          - "5672:5672"
    kafka:
        image: bitnami/kafka:3.5.0
        ports:
          - "9092:9092"
        environment:
          KAFKA_ENABLE_KRAFT: "true"
          KAFKA_CFG_NODE_ID: "1"
          KAFKA_CFG_PROCESS_ROLES: "broker,controller"
          KAFKA_CFG_CONTROLLER_LISTENER_NAMES: "CONTROLLER"
          KAFKA_CFG_LISTENERS: "PLAINTEXT://:9092,CONTROLLER://:9093"
          KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP: "CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT"
          KAFKA_CFG_ADVERTISED_LISTENERS: "PLAINTEXT://127.0.0.1:9092"
          KAFKA_BROKER_ID: "1"
          KAFKA_CFG_CONTROLLER_QUORUM_VOTERS: "1@kafka:9093"
          ALLOW_PLAINTEXT_LISTENER: "true"

```

```bash
docker compose up -d
```

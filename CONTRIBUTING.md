> **_NOTE:_**  This is an auto-generated file. Please edit docs/docs/en/getting-started/contributing/CONTRIBUTING.md instead.

# Development

After cloning the project, you'll need to set up the development environment. Here are the guidelines on how to do this.

## Virtual Environment with `venv`

Create a virtual environment in a directory using Python's `venv` module:

```bash
python -m venv venv
```

That will create a `./venv/` directory with Python binaries, allowing you to install packages in an isolated environment.

## Activate the Environment

Activate the new environment with:

```bash
source ./venv/bin/activate
```

Ensure you have the latest pip version in your virtual environment:

```bash
python -m pip install --upgrade pip
```

## Installing Dependencies

After activating the virtual environment as described above, run:

```bash
pip install -e ".[dev]"
```

This will install all the dependencies and your local **FastStream** in your virtual environment.

### Using Your local **FastStream**

If you create a Python file that imports and uses **FastStream**, and run it with the Python from your local environment, it will use your local **FastStream** source code.

Whenever you update your local **FastStream** source code, it will automatically use the latest version when you run your Python file again. This is because it is installed with `-e`.

This way, you don't have to "install" your local version to be able to test every change.

To use your local **FastStream CLI**, type:

```bash
python -m faststream ...
```

## Running Tests

### Pytest

To run tests with your current **FastStream** application and Python environment, use:

```bash
pytest tests
# or
./scripts/test.sh
# with coverage output
./scripts/test-cov.sh
```

In your project, you'll find some *pytest marks*:

* **slow**
* **rabbit**
* **kafka**
* **nats**
* **redis**
* **all**

By default, running *pytest* will execute "not slow" tests.

To run all tests use:

```bash
pytest -m 'all'
```

If you don't have a local broker instance running, you can run tests without those dependencies:

```bash
pytest -m 'not rabbit and not kafka and not nats and not redis'
```

To run tests based on RabbitMQ, Kafka, or other dependencies, the following dependencies are needed to be started as docker containers:

```yaml
version: "3"
services:
  # nosemgrep: yaml.docker-compose.security.writable-filesystem-service.writable-filesystem-service
  rabbitmq:
    image: rabbitmq:alpine
    ports:
      - "5672:5672"
    # https://semgrep.dev/r?q=yaml.docker-compose.security.no-new-privileges.no-new-privileges
    security_opt:
      - no-new-privileges:true
  # nosemgrep: yaml.docker-compose.security.writable-filesystem-service.writable-filesystem-service
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
    # https://semgrep.dev/r?q=yaml.docker-compose.security.no-new-privileges.no-new-privileges
    security_opt:
      - no-new-privileges:true
  # nosemgrep: yaml.docker-compose.security.writable-filesystem-service.writable-filesystem-service
  nats:
    image: nats
    command: -js
    ports:
      - 4222:4222
      - 8222:8222  # management
    # https://semgrep.dev/r?q=yaml.docker-compose.security.no-new-privileges.no-new-privileges
    security_opt:
      - no-new-privileges:true
  # nosemgrep: yaml.docker-compose.security.writable-filesystem-service.writable-filesystem-service
  redis:
    image: redis:alpine
    ports:
      - 6379:6379
    # https://semgrep.dev/r?q=yaml.docker-compose.security.no-new-privileges.no-new-privileges
    security_opt:
      - no-new-privileges:true
```

You can start the dependencies easily using provided script by running:

```bash
./scripts/start_test_env.sh
```

Once you are done with development and running tests, you can stop the dependencies' docker containers by running:

```bash
./scripts/stop_test_env.sh
```

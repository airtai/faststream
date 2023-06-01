# `fastkafka`

**Usage**:

```console
$ fastkafka [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `docs`: Commands for managing fastkafka app...
* `run`: Runs Fast Kafka API application
* `testing`: Commands for managing fastkafka testing

## `fastkafka docs`

Commands for managing fastkafka app documentation

**Usage**:

```console
$ fastkafka docs [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `generate`: Generates documentation for a FastKafka...
* `install_deps`: Installs dependencies for FastKafka...
* `serve`: Generates and serves documentation for a...

### `fastkafka docs generate`

Generates documentation for a FastKafka application

**Usage**:

```console
$ fastkafka docs generate [OPTIONS] APP
```

**Arguments**:

* `APP`: input in the form of 'path:app', where **path** is the path to a python file and **app** is an object of type **FastKafka**.  [required]

**Options**:

* `--root-path TEXT`: root path under which documentation will be created; default is current directory
* `--help`: Show this message and exit.

### `fastkafka docs install_deps`

Installs dependencies for FastKafka documentation generation

**Usage**:

```console
$ fastkafka docs install_deps [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `fastkafka docs serve`

Generates and serves documentation for a FastKafka application

**Usage**:

```console
$ fastkafka docs serve [OPTIONS] APP
```

**Arguments**:

* `APP`: input in the form of 'path:app', where **path** is the path to a python file and **app** is an object of type **FastKafka**.  [required]

**Options**:

* `--root-path TEXT`: root path under which documentation will be created; default is current directory
* `--bind TEXT`: Some info  [default: 127.0.0.1]
* `--port INTEGER`: Some info  [default: 8000]
* `--help`: Show this message and exit.

## `fastkafka run`

Runs Fast Kafka API application

**Usage**:

```console
$ fastkafka run [OPTIONS] APP
```

**Arguments**:

* `APP`: input in the form of 'path:app', where **path** is the path to a python file and **app** is an object of type **FastKafka**.  [required]

**Options**:

* `--num-workers INTEGER`: Number of FastKafka instances to run, defaults to number of CPU cores.  [default: 4]
* `--kafka-broker TEXT`: kafka_broker, one of the keys of the kafka_brokers dictionary passed in the constructor of FastaKafka class.  [default: localhost]
* `--help`: Show this message and exit.

## `fastkafka testing`

Commands for managing fastkafka testing

**Usage**:

```console
$ fastkafka testing [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `install_deps`: Installs dependencies for FastKafka app...

### `fastkafka testing install_deps`

Installs dependencies for FastKafka app testing

**Usage**:

```console
$ fastkafka testing install_deps [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.


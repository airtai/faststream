# `run_fastkafka_server_process`

**Usage**:

```console
$ run_fastkafka_server_process [OPTIONS] APP
```

**Arguments**:

* `APP`: Input in the form of 'path:app', where **path** is the path to a python file and **app** is an object of type **FastKafka**.  [required]

**Options**:

* `--kafka-broker TEXT`: Kafka broker, one of the keys of the kafka_brokers dictionary passed in the constructor of FastKafka class.  [required]
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.


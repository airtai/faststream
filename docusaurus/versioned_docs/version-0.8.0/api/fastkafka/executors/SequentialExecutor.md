## fastkafka.executors.SequentialExecutor {#fastkafka.executors.SequentialExecutor}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/task_streaming.py#L305-L356" class="link-to-source" target="_blank">View source</a>


A class that implements a sequential executor for processing consumer records.

The SequentialExecutor class extends the StreamExecutor class and provides functionality
for running processing tasks in sequence by awaiting their coroutines.

### __init__ {#fastkafka._components.task_streaming.SequentialExecutor.init}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/task_streaming.py#L312-L326" class="link-to-source" target="_blank">View source</a>

```py
__init__(
    self, throw_exceptions=False, max_buffer_size=100000
)
```

Create an instance of SequentialExecutor

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `throw_exceptions` | `bool` | Flag indicating whether exceptions should be thrown or logged.Defaults to False. | `False` |
| `max_buffer_size` | `int` | Maximum buffer size for the memory object stream.Defaults to 100_000. | `100000` |

### run {#fastkafka._components.task_streaming.SequentialExecutor.run}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/task_streaming.py#L328-L356" class="link-to-source" target="_blank">View source</a>

```py
run(
    self, is_shutting_down_f, generator, processor
)
```

Runs the sequential executor.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `is_shutting_down_f` | `Callable[[], bool]` | Function to check if the executor is shutting down. | *required* |
| `generator` | `Callable[[], Awaitable[aiokafka.structs.ConsumerRecord]]` | Generator function for retrieving consumer records. | *required* |
| `processor` | `Callable[[aiokafka.structs.ConsumerRecord], Awaitable[NoneType]]` | Processor function for processing consumer records. | *required* |


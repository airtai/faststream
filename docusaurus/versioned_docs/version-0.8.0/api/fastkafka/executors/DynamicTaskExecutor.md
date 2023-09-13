## fastkafka.executors.DynamicTaskExecutor {#fastkafka.executors.DynamicTaskExecutor}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/task_streaming.py#L207-L272" class="link-to-source" target="_blank">View source</a>


A class that implements a dynamic task executor for processing consumer records.

The DynamicTaskExecutor class extends the StreamExecutor class and provides functionality
for running a tasks in parallel using asyncio.Task.

### __init__ {#fastkafka._components.task_streaming.DynamicTaskExecutor.init}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/task_streaming.py#L214-L237" class="link-to-source" target="_blank">View source</a>

```py
__init__(
    self, throw_exceptions=False, max_buffer_size=100000, size=100000
)
```

Create an instance of DynamicTaskExecutor

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `throw_exceptions` | `bool` | Flag indicating whether exceptions should be thrown ot logged.Defaults to False. | `False` |
| `max_buffer_size` | `int` | Maximum buffer size for the memory object stream.Defaults to 100_000. | `100000` |
| `size` | `int` | Size of the task pool. Defaults to 100_000. | `100000` |

### run {#fastkafka._components.task_streaming.DynamicTaskExecutor.run}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/task_streaming.py#L239-L272" class="link-to-source" target="_blank">View source</a>

```py
run(
    self, is_shutting_down_f, generator, processor
)
```

Runs the dynamic task executor.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `is_shutting_down_f` | `Callable[[], bool]` | Function to check if the executor is shutting down. | *required* |
| `generator` | `Callable[[], Awaitable[aiokafka.structs.ConsumerRecord]]` | Generator function for retrieving consumer records. | *required* |
| `processor` | `Callable[[aiokafka.structs.ConsumerRecord], Awaitable[NoneType]]` | Processor function for processing consumer records. | *required* |


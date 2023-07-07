## `fastkafka.executors.DynamicTaskExecutor` {#fastkafka.executors.DynamicTaskExecutor}


A class that implements a dynamic task executor for processing consumer records.

The DynamicTaskExecutor class extends the StreamExecutor class and provides functionality
for running a tasks in parallel using asyncio.Task.

### `__init__` {#init}

`def __init__(self, throw_exceptions: bool = False, max_buffer_size: int = 100000, size: int = 100000) -> None`

Create an instance of DynamicTaskExecutor

**Parameters**:
- `throw_exceptions`: Flag indicating whether exceptions should be thrown ot logged.
Defaults to False.
- `max_buffer_size`: Maximum buffer size for the memory object stream.
Defaults to 100_000.
- `size`: Size of the task pool. Defaults to 100_000.

### `run` {#run}

`def run(self, is_shutting_down_f: Callable[[], bool], generator: Callable[[], Awaitable[aiokafka.structs.ConsumerRecord]], processor: Callable[[aiokafka.structs.ConsumerRecord], Awaitable[NoneType]]) -> None`

Runs the dynamic task executor.

**Parameters**:
- `is_shutting_down_f`: Function to check if the executor is shutting down.
- `generator`: Generator function for retrieving consumer records.
- `processor`: Processor function for processing consumer records.

**Returns**:
- None


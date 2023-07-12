## `fastkafka.executors.SequentialExecutor` {#fastkafka.executors.SequentialExecutor}


A class that implements a sequential executor for processing consumer records.

The SequentialExecutor class extends the StreamExecutor class and provides functionality
for running processing tasks in sequence by awaiting their coroutines.

### `__init__` {#init}

`def __init__(self, throw_exceptions: bool = False, max_buffer_size: int = 100000) -> None`

Create an instance of SequentialExecutor

**Parameters**:
- `throw_exceptions`: Flag indicating whether exceptions should be thrown or logged.
Defaults to False.
- `max_buffer_size`: Maximum buffer size for the memory object stream.
Defaults to 100_000.

### `run` {#run}

`def run(self, is_shutting_down_f: Callable[[], bool], generator: Callable[[], Awaitable[aiokafka.structs.ConsumerRecord]], processor: Callable[[aiokafka.structs.ConsumerRecord], Awaitable[NoneType]]) -> None`

Runs the sequential executor.

**Parameters**:
- `is_shutting_down_f`: Function to check if the executor is shutting down.
- `generator`: Generator function for retrieving consumer records.
- `processor`: Processor function for processing consumer records.

**Returns**:
- None


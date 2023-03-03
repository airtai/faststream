# Release notes

<!-- do not remove -->

## 0.1.0rc5

### New Features

- Enable FastKafka reentrancy ([#92](https://github.com/airtai/fastkafka/issues/92))
  - - [x] Remove passing of custom producers in @produces decorator
- [x] Add cleanup of stale producers in populate_producers and close_producers methods

- Allocation of random port in LocalKafkaBroker ([#80](https://github.com/airtai/fastkafka/issues/80))
  - If the Zookeeper or Kafka process crashes while creating it's most likely that the requested port is occupied.
To solve this, if the process crashes, try with a randomly generated port.
 
- [x] Zookeeper random port allocation
- [x] Kafka random port allocation

- Create missing topics in LocalKafkaBroker ([#79](https://github.com/airtai/fastkafka/issues/79))
  - Changed to pass to LocalKafkaBroker

- [x] add topics function to KafkaApp for listing topics
- [x] Implement creation of topics in LocalKafkaBroker
- [x] Wait for topics to be created in Broker

- Implement FastKafka Tester class ([#75](https://github.com/airtai/fastkafka/issues/75))
  - - [x] Implent mocking of consume and produce functions
- [x] Implement mirroring of consumers and producers

- Release polishing ([#69](https://github.com/airtai/fastkafka/issues/69))
  - - [x] Remove stale uvicorn imports from notebooks
- [x] Transfer nest-asyncio requirement to dev requirements
- [x] Replace Ilock with posix_ipc
- [ ] Implement mechanism for port allocation in LocalKafkaBroker
- [ ] Cleanup logging in LocalKafkaBoker

- Create LocalKafkaBroker class ([#66](https://github.com/airtai/fastkafka/issues/66))

- Start LocalKafkaBroker in testing ([#65](https://github.com/airtai/fastkafka/issues/65))

- ESAKafka mockup ([#62](https://github.com/airtai/fastkafka/issues/62))
  - - [x] Prepare project repository and structure
- [x] Mockup services for ESA
- [x] Test mockups

- Integrate static check changes from workflow repository ([#59](https://github.com/airtai/fastkafka/issues/59))

- Refactor consumer_loop ([#43](https://github.com/airtai/fastkafka/issues/43))
  - - [x] Remove unnecessary process_msgs and integrate it back to _aiokafka_consumer_loop
- [x] Rework process_msgs tests to use mock patching
- [x] Remove creating and sending async callback to process stream every time when msg is consumed
- [x] Write docs
- [ ] Fix failing CI tests

- Add better exception handling in consumer callbacks ([#37](https://github.com/airtai/fastkafka/issues/37))

- Implement mechanism for registering actions after startup ([#35](https://github.com/airtai/fastkafka/issues/35))

- Make FastKafkaAPI not inherit from FastAPI ([#34](https://github.com/airtai/fastkafka/issues/34))

- Implement sync and async variants for producer decorator ([#22](https://github.com/airtai/fastkafka/issues/22))

- Add Kafka healthcheck in CI ([#11](https://github.com/airtai/fastkafka/issues/11))

- CLI command for exporting async docs ([#8](https://github.com/airtai/fastkafka/issues/8))

### Bugs Squashed

- Enable FastKafka reentrancy ([#92](https://github.com/airtai/fastkafka/issues/92))
  - - [x] Remove passing of custom producers in @produces decorator
- [x] Add cleanup of stale producers in populate_producers and close_producers methods

- FastKafka context manager __aenter__ and __aexit__ unuseable separately because of TaskGroup exceptions when closing ([#91](https://github.com/airtai/fastkafka/issues/91))
  - TaskGroup must be closed in the same task it was opened, otherwise exception is raised
This breaks FastKafka when async context manager methods are used separately
- [x] Replace task group with asyncio.create_task calls to enable using __aenter__ and __aexit__ methods in FastKafk

- Release polishing ([#69](https://github.com/airtai/fastkafka/issues/69))
  - - [x] Remove stale uvicorn imports from notebooks
- [x] Transfer nest-asyncio requirement to dev requirements
- [x] Replace Ilock with posix_ipc
- [ ] Implement mechanism for port allocation in LocalKafkaBroker
- [ ] Cleanup logging in LocalKafkaBoker

- Fastkafka CLI run workers does not output log messages until cancelled ([#60](https://github.com/airtai/fastkafka/issues/60))
  - The issue happens when the code does not flush the output, such as in regular python print().
- [x] Write a warning in the 02_First_Steps for flushing

- Fix export_async_spec failing when @consumes function has a return type None ([#48](https://github.com/airtai/fastkafka/issues/48))

- Fix silent failing in guides when executing example scripts ([#44](https://github.com/airtai/fastkafka/issues/44))
  - - [x] Add exit_code return value to run_script_and_cancel helper function
- [x] Assert exit_code is equal to 0 when run_script_and_cancel runs
- [x] Add tests for run_script_and_cancel helper function
- [x] Check log levels for Guide_02_First_steps


## 0.1.0rc1


### Bugs Squashed

- Consumer is not created with all parameters passed to FastKafkaAPI constructor ([#49](https://github.com/airtai/fastkafka/issues/49))


## 0.0.4

- inheritance from FastAPI removed


## 0.0.3

Documentation polishing and Semgrep scan added


## 0.0.2


### Bugs Squashed

- Documentation build failing in CI ([#21](https://github.com/airtai/fast-kafka-api/issues/21))


## 0.0.1

Initial release

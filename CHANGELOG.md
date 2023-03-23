# Release notes

<!-- do not remove -->

## 0.3.0rc2

### New Features

- Add support for Redpanda for testing and deployment ([#181](https://github.com/airtai/fastkafka/pull/181)), thanks to [@kumaranvpl](https://github.com/kumaranvpl)

- Remove bootstrap_servers from __init__ and use the name of broker as an option when running/testing ([#134](https://github.com/airtai/fastkafka/issues/134))

### Bugs Squashed

- Fix the helper.py link in CHANGELOG.md ([#165](https://github.com/airtai/fastkafka/issues/165))


## 0.3.0rc0

### New Features

- Add a GH action file to check for broken links in the docs ([#163](https://github.com/airtai/fastkafka/issues/163))

- Optimize requirements for testing and docs ([#151](https://github.com/airtai/fastkafka/issues/151))

- Break requirements into base and optional for testing and dev ([#124](https://github.com/airtai/fastkafka/issues/124))
  - MInimize base requirements needed just for running the service.

Move to setup.py

- Add link to example git repo into guide for building docs using actions ([#81](https://github.com/airtai/fastkafka/issues/81))

- Add logging for run_in_background ([#46](https://github.com/airtai/fastkafka/issues/46))

- Implement partition Key mechanism for producers ([#16](https://github.com/airtai/fastkafka/issues/16))
  - - [x] Implement partition key mechanism for `@produces` decorator
Implemented behaviour:
  1. A method decorated with `@produces` can return defined message as-is: the message is wrapped in a Event object with key=None and passed to producer = message sent without defined key, partition chosen at random
  2. A method decorated with `@produces` can return defined message wrapped in an Event object with key argument value in bytes = message sent to kafka with defined key, partition chosen using the defined key

### Bugs Squashed

- fastkafka docs install_deps fails ([#157](https://github.com/airtai/fastkafka/issues/157))
  - Unexpected internal error: [Errno 2] No such file or directory: 'npx'

- Broken links in docs ([#141](https://github.com/airtai/fastkafka/issues/141))
  - Looks nice! Btw: The links to your docs in your readme are broken:)

https://www.reddit.com/r/Python/comments/11paz9u/comment/jbz18oq/?utm_source=share&utm_medium=web2x&context=3

- fastkafka run is not showing up in CLI docs ([#132](https://github.com/airtai/fastkafka/issues/132))


## 0.2.3

- Fixed broken links on PyPi index page


## 0.2.2

### New Features

- Extract JDK and Kafka installation out of LocalKafkaBroker ([#131](https://github.com/airtai/fastkafka/issues/131))

- PyYAML version relaxed ([#119](https://github.com/airtai/fastkafka/pull/119)), thanks to [@davorrunje](https://github.com/davorrunje)

- Replace docker based kafka with local ([#68](https://github.com/airtai/fastkafka/issues/68))
  - [x] replace docker compose with a simple docker run (standard run_jupyter.sh should do)
  - [x] replace all tests to use LocalKafkaBroker
  - [x] update documentation

### Bugs Squashed

- Fix broken link for FastKafka docs in index notebook ([#145](https://github.com/airtai/fastkafka/issues/145))

- Fix encoding issues when loading setup.py on windows OS ([#135](https://github.com/airtai/fastkafka/issues/135))


## 0.2.0

### New Features

- Replace kafka container with LocalKafkaBroker ([#112](https://github.com/airtai/fastkafka/issues/112))
  - - [x] Replace kafka container with LocalKafkaBroker in tests
- [x] Remove kafka container from tests environment
- [x] Fix failing tests

### Bugs Squashed

- Fix random failing in CI ([#109](https://github.com/airtai/fastkafka/issues/109))


## 0.1.3

- version update in __init__.py


## 0.1.2

### New Features


- Git workflow action for publishing Kafka docs ([#78](https://github.com/airtai/fastkafka/issues/78))


### Bugs Squashed

- Include missing requirement ([#110](https://github.com/airtai/fastkafka/issues/110))
  - [x] Typer is imported in this [file](https://github.com/airtai/fastkafka/blob/main/fastkafka/_components/helpers.py) but it is not included in [settings.ini](https://github.com/airtai/fastkafka/blob/main/settings.ini)
  - [x] Add aiohttp which is imported in this [file](https://github.com/airtai/fastkafka/blob/main/fastkafka/_helpers.py)
  - [x] Add nbformat which is imported in _components/helpers.py
  - [x] Add nbconvert which is imported in _components/helpers.py


## 0.1.1


### Bugs Squashed

- JDK install fails on Python 3.8 ([#106](https://github.com/airtai/fastkafka/issues/106))



## 0.1.0

Initial release

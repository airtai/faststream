# Release notes

<!-- do not remove -->

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
  - [x] Add aiohttp which is imported in this [file](https://github.com/airtai/fastkafka/blob/main/fastkafka/helpers.py)
  - [x] Add nbformat which is imported in _components/helpers.py
  - [x] Add nbconvert which is imported in _components/helpers.py


## 0.1.1


### Bugs Squashed

- JDK install fails on Python 3.8 ([#106](https://github.com/airtai/fastkafka/issues/106))



## 0.1.0

Initial release

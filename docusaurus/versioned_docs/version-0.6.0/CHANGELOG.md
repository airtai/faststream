# Release notes

<!-- do not remove -->

## 0.6.0

### New Features

- Timestamps added to CLI commands ([#283](https://github.com/airtai/fastkafka/pull/283)), thanks to [@davorrunje](https://github.com/davorrunje)

- Added option to process messages concurrently ([#278](https://github.com/airtai/fastkafka/pull/278)), thanks to [@Sternakt](https://github.com/Sternakt)
  - A new `executor` option is added that supports either sequential processing for tasks with small latencies or concurrent processing for tasks with larger latencies.

- Add consumes and produces functions to app ([#274](https://github.com/airtai/fastkafka/pull/274)), thanks to [@Sternakt](https://github.com/Sternakt)


- Add batching for producers ([#273](https://github.com/airtai/fastkafka/pull/273)), thanks to [@Sternakt](https://github.com/Sternakt)
  - requirement(batch): batch support is a real need! and i see it on the issue list.... so hope we do not need to wait too long

    https://discord.com/channels/1085457301214855171/1090956337938182266/1098592795557630063

- Fix broken links in guides ([#272](https://github.com/airtai/fastkafka/pull/272)), thanks to [@harishmohanraj](https://github.com/harishmohanraj)

- Generate the docusaurus sidebar dynamically by parsing summary.md ([#270](https://github.com/airtai/fastkafka/pull/270)), thanks to [@harishmohanraj](https://github.com/harishmohanraj)

- Metadata passed to consumer ([#269](https://github.com/airtai/fastkafka/pull/269)), thanks to [@Sternakt](https://github.com/Sternakt)
  - requirement(key): read the key value somehow..Maybe I missed something in the docs
    requirement(header): read header values, Reason: I use CDC | Debezium and in the current system the header values are important to differentiate between the CRUD operations.

    https://discord.com/channels/1085457301214855171/1090956337938182266/1098592795557630063

- Contribution with instructions how to build and test added ([#255](https://github.com/airtai/fastkafka/pull/255)), thanks to [@Sternakt](https://github.com/Sternakt)


- Export encoders, decoders from fastkafka.encoder ([#246](https://github.com/airtai/fastkafka/pull/246)), thanks to [@kumaranvpl](https://github.com/kumaranvpl)


- Create a Github action file to automatically index the website and commit it to the FastKafkachat repository. ([#239](https://github.com/airtai/fastkafka/issues/239))


- UI Improvement: Post screenshots with links to the actual messages in testimonials section ([#228](https://github.com/airtai/fastkafka/issues/228))

### Bugs Squashed

- Batch testing fix ([#280](https://github.com/airtai/fastkafka/pull/280)), thanks to [@Sternakt](https://github.com/Sternakt)

- Tester breaks when using Batching or KafkaEvent producers ([#279](https://github.com/airtai/fastkafka/issues/279))

- Consumer loop callbacks are not executing in parallel ([#276](https://github.com/airtai/fastkafka/issues/276))


## 0.5.0

### New Features

- Significant speedup of Kafka producer ([#236](https://github.com/airtai/fastkafka/pull/236)), thanks to [@Sternakt](https://github.com/Sternakt)
 

- Added support for AVRO encoding/decoding ([#231](https://github.com/airtai/fastkafka/pull/231)), thanks to [@kumaranvpl](https://github.com/kumaranvpl)


### Bugs Squashed

- Fixed sidebar to include guides in docusaurus documentation ([#238](https://github.com/airtai/fastkafka/pull/238)), thanks to [@Sternakt](https://github.com/Sternakt)

- Fixed link to symbols in docusaurus docs ([#227](https://github.com/airtai/fastkafka/pull/227)), thanks to [@harishmohanraj](https://github.com/harishmohanraj)

- Removed bootstrap servers from constructor ([#220](https://github.com/airtai/fastkafka/pull/220)), thanks to [@kumaranvpl](https://github.com/kumaranvpl)


## 0.4.0

### New Features

- Integrate fastkafka chat ([#208](https://github.com/airtai/fastkafka/pull/208)), thanks to [@harishmohanraj](https://github.com/harishmohanraj)

- Add benchmarking ([#206](https://github.com/airtai/fastkafka/pull/206)), thanks to [@kumaranvpl](https://github.com/kumaranvpl)

- Enable fast testing without running kafka locally ([#198](https://github.com/airtai/fastkafka/pull/198)), thanks to [@Sternakt](https://github.com/Sternakt)

- Generate docs using Docusaurus ([#194](https://github.com/airtai/fastkafka/pull/194)), thanks to [@harishmohanraj](https://github.com/harishmohanraj)

- Add test cases for LocalRedpandaBroker ([#189](https://github.com/airtai/fastkafka/pull/189)), thanks to [@kumaranvpl](https://github.com/kumaranvpl)

- Reimplement patch and delegates from fastcore ([#188](https://github.com/airtai/fastkafka/pull/188)), thanks to [@Sternakt](https://github.com/Sternakt)

- Rename existing functions into start and stop and add lifespan handler ([#117](https://github.com/airtai/fastkafka/issues/117))
  - https://www.linkedin.com/posts/tiangolo_fastapi-activity-7038907638331404288-Oar3/?utm_source=share&utm_medium=member_ios


## 0.3.1

-  README.md file updated


## 0.3.0

### New Features

- Guide for fastkafka produces using partition key ([#172](https://github.com/airtai/fastkafka/pull/172)), thanks to [@Sternakt](https://github.com/Sternakt)
  - Closes #161

- Add support for Redpanda for testing and deployment ([#181](https://github.com/airtai/fastkafka/pull/181)), thanks to [@kumaranvpl](https://github.com/kumaranvpl)

- Remove bootstrap_servers from __init__ and use the name of broker as an option when running/testing ([#134](https://github.com/airtai/fastkafka/issues/134))

- Add a GH action file to check for broken links in the docs ([#163](https://github.com/airtai/fastkafka/issues/163))

- Optimize requirements for testing and docs ([#151](https://github.com/airtai/fastkafka/issues/151))

- Break requirements into base and optional for testing and dev ([#124](https://github.com/airtai/fastkafka/issues/124))
  - Minimize base requirements needed just for running the service.

- Add link to example git repo into guide for building docs using actions ([#81](https://github.com/airtai/fastkafka/issues/81))

- Add logging for run_in_background ([#46](https://github.com/airtai/fastkafka/issues/46))

- Implement partition Key mechanism for producers ([#16](https://github.com/airtai/fastkafka/issues/16))

### Bugs Squashed

- Implement checks for npm installation and version ([#176](https://github.com/airtai/fastkafka/pull/176)), thanks to [@Sternakt](https://github.com/Sternakt)
  - Closes #158 by checking if the npx is installed and more verbose error handling

- Fix the helper.py link in CHANGELOG.md ([#165](https://github.com/airtai/fastkafka/issues/165))

- fastkafka docs install_deps fails ([#157](https://github.com/airtai/fastkafka/issues/157))
  - Unexpected internal error: [Errno 2] No such file or directory: 'npx'

- Broken links in docs ([#141](https://github.com/airtai/fastkafka/issues/141))

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

# Basic Publisher

You can use a `#!python @KafkaBroker.publisher(...)` (or `#!python KafkaBroker.publish("msg", "topic")` or `#!python KafkaBroker.publish_batch("msg1", "msg2", topic="topic")`) to produce messages to Kafka topics.

In this guide we will create a simple FastKafka app that will produce hello world messages to hello_world topic.

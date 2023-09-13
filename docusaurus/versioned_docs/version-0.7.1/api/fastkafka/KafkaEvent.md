## `fastkafka.KafkaEvent` {#fastkafka.KafkaEvent}


A generic class for representing Kafka events. Based on BaseSubmodel, bound to pydantic.BaseModel

**Parameters**:
- `message`: The message contained in the Kafka event, can be of type pydantic.BaseModel.
- `key`: The optional key used to identify the Kafka event.


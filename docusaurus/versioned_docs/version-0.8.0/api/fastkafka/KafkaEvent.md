## fastkafka.KafkaEvent {#fastkafka.KafkaEvent}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_components/producer_decorator.py#L36-L46" class="link-to-source" target="_blank">View source</a>


A generic class for representing Kafka events. Based on BaseSubmodel, bound to pydantic.BaseModel

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `message` | `BaseSubmodel` | The message contained in the Kafka event, can be of type pydantic.BaseModel. | *required* |
| `key` | `Optional[bytes]` | The optional key used to identify the Kafka event. | `None` |


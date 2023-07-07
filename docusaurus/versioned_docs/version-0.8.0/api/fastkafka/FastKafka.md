### __init__ {#fastkafka._application.app.FastKafka.init}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_application/app.py#L179-L305" class="link-to-source" target="_blank">View source</a>

```py
__init__(
    self,
    title=None,
    description=None,
    version=None,
    contact=None,
    kafka_brokers=None,
    root_path=None,
    lifespan=None,
    bootstrap_servers_id='localhost',
    loop=None,
    client_id=None,
    metadata_max_age_ms=300000,
    request_timeout_ms=40000,
    api_version='auto',
    acks=<object object at 0x7ff10d5f9100>,
    key_serializer=None,
    value_serializer=None,
    compression_type=None,
    max_batch_size=16384,
    partitioner=<kafka.partitioner.default.DefaultPartitioner object at 0x7ff10c16e2d0>,
    max_request_size=1048576,
    linger_ms=0,
    send_backoff_ms=100,
    retry_backoff_ms=100,
    security_protocol='PLAINTEXT',
    ssl_context=None,
    connections_max_idle_ms=540000,
    enable_idempotence=False,
    transactional_id=None,
    transaction_timeout_ms=60000,
    sasl_mechanism='PLAIN',
    sasl_plain_password=None,
    sasl_plain_username=None,
    sasl_kerberos_service_name='kafka',
    sasl_kerberos_domain_name=None,
    sasl_oauth_token_provider=None,
    group_id=None,
    key_deserializer=None,
    value_deserializer=None,
    fetch_max_wait_ms=500,
    fetch_max_bytes=52428800,
    fetch_min_bytes=1,
    max_partition_fetch_bytes=1048576,
    auto_offset_reset='latest',
    enable_auto_commit=True,
    auto_commit_interval_ms=5000,
    check_crcs=True,
    partition_assignment_strategy=(<class 'kafka.coordinator.assignors.roundrobin.RoundRobinPartitionAssignor'>,),
    max_poll_interval_ms=300000,
    rebalance_timeout_ms=None,
    session_timeout_ms=10000,
    heartbeat_interval_ms=3000,
    consumer_timeout_ms=200,
    max_poll_records=None,
    exclude_internal_topics=True,
    isolation_level='read_uncommitted',
)
```

Creates FastKafka application

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `title` | `Optional[str]` | optional title for the documentation. If None,the title will be set to empty string | `None` |
| `description` | `Optional[str]` | optional description for the documentation. IfNone, the description will be set to empty string | `None` |
| `version` | `Optional[str]` | optional version for the documentation. If None,the version will be set to empty string | `None` |
| `contact` | `Optional[Dict[str, str]]` | optional contact for the documentation. If None, thecontact will be set to placeholder values:name='Author' url=HttpUrl(' https://www.google.com ', ) email='noreply@gmail.com' | `None` |
| `kafka_brokers` | `Optional[Dict[str, Any]]` | dictionary describing kafka brokers used for settingthe bootstrap server when running the applicationa and forgenerating documentation. Defaults to    {        "localhost": {            "url": "localhost",            "description": "local kafka broker",            "port": "9092",        }    } | `None` |
| `root_path` | `Union[pathlib.Path, str, NoneType]` | path to where documentation will be created | `None` |
| `lifespan` | `Optional[Callable[[ForwardRef('FastKafka')], AsyncContextManager[NoneType]]]` | asynccontextmanager that is used for setting lifespan hooks.__aenter__ is called before app start and __aexit__ after app stop.The lifespan is called whe application is started as async contextmanager, e.g.:`async with kafka_app...` | `None` |
| `client_id` |  | a name for this client. This string is passed ineach request to servers and can be used to identify specificserver-side log entries that correspond to this client.Default: ``aiokafka-producer-#`` (appended with a unique numberper instance) | `None` |
| `key_serializer` |  | used to convert user-supplied keys to bytesIf not :data:`None`, called as ``f(key),`` should return:class:`bytes`.Default: :data:`None`. | `None` |
| `value_serializer` |  | used to convert user-supplied messagevalues to :class:`bytes`. If not :data:`None`, called as``f(value)``, should return :class:`bytes`.Default: :data:`None`. | `None` |
| `acks` |  | one of ``0``, ``1``, ``all``. The number of acknowledgmentsthe producer requires the leader to have received before considering arequest complete. This controls the durability of records that aresent. The following settings are common:* ``0``: Producer will not wait for any acknowledgment from the server  at all. The message will immediately be added to the socket  buffer and considered sent. No guarantee can be made that the  server has received the record in this case, and the retries  configuration will not take effect (as the client won't  generally know of any failures). The offset given back for each  record will always be set to -1.* ``1``: The broker leader will write the record to its local log but  will respond without awaiting full acknowledgement from all  followers. In this case should the leader fail immediately  after acknowledging the record but before the followers have  replicated it then the record will be lost.* ``all``: The broker leader will wait for the full set of in-sync  replicas to acknowledge the record. This guarantees that the  record will not be lost as long as at least one in-sync replica  remains alive. This is the strongest available guarantee.If unset, defaults to ``acks=1``. If `enable_idempotence` is:data:`True` defaults to ``acks=all`` | `<object object at 0x7ff10d5f9100>` |
| `compression_type` |  | The compression type for all data generated bythe producer. Valid values are ``gzip``, ``snappy``, ``lz4``, ``zstd``or :data:`None`.Compression is of full batches of data, so the efficacy of batchingwill also impact the compression ratio (more batching means bettercompression). Default: :data:`None`. | `None` |
| `max_batch_size` |  | Maximum size of buffered data per partition.After this amount :meth:`send` coroutine will block until batch isdrained.Default: 16384 | `16384` |
| `linger_ms` |  | The producer groups together any records that arrivein between request transmissions into a single batched request.Normally this occurs only under load when records arrive fasterthan they can be sent out. However in some circumstances the clientmay want to reduce the number of requests even under moderate load.This setting accomplishes this by adding a small amount ofartificial delay; that is, if first request is processed faster,than `linger_ms`, producer will wait ``linger_ms - process_time``.Default: 0 (i.e. no delay). | `0` |
| `partitioner` |  | Callable used to determine which partitioneach message is assigned to. Called (after key serialization):``partitioner(key_bytes, all_partitions, available_partitions)``.The default partitioner implementation hashes each non-None keyusing the same murmur2 algorithm as the Java client so thatmessages with the same key are assigned to the same partition.When a key is :data:`None`, the message is delivered to a random partition(filtered to partitions with available leaders only, if possible). | `<kafka.partitioner.default.DefaultPartitioner object at 0x7ff10c16e2d0>` |
| `max_request_size` |  | The maximum size of a request. This is alsoeffectively a cap on the maximum record size. Note that the serverhas its own cap on record size which may be different from this.This setting will limit the number of record batches the producerwill send in a single request to avoid sending huge requests.Default: 1048576. | `1048576` |
| `metadata_max_age_ms` |  | The period of time in milliseconds afterwhich we force a refresh of metadata even if we haven't seen anypartition leadership changes to proactively discover any newbrokers or partitions. Default: 300000 | `300000` |
| `request_timeout_ms` |  | Produce request timeout in milliseconds.As it's sent as part of:class:`~kafka.protocol.produce.ProduceRequest` (it's a blockingcall), maximum waiting time can be up to ``2 *request_timeout_ms``.Default: 40000. | `40000` |
| `retry_backoff_ms` |  | Milliseconds to backoff when retrying onerrors. Default: 100. | `100` |
| `api_version` |  | specify which kafka API version to use.If set to ``auto``, will attempt to infer the broker version byprobing various APIs. Default: ``auto`` | `'auto'` |
| `security_protocol` |  | Protocol used to communicate with brokers.Valid values are: ``PLAINTEXT``, ``SSL``, ``SASL_PLAINTEXT``,``SASL_SSL``. Default: ``PLAINTEXT``. | `'PLAINTEXT'` |
| `ssl_context` |  | pre-configured :class:`~ssl.SSLContext`for wrapping socket connections. Directly passed into asyncio's:meth:`~asyncio.loop.create_connection`. For moreinformation see :ref:`ssl_auth`.Default: :data:`None` | `None` |
| `connections_max_idle_ms` |  | Close idle connections after the numberof milliseconds specified by this config. Specifying :data:`None` willdisable idle checks. Default: 540000 (9 minutes). | `540000` |
| `enable_idempotence` |  | When set to :data:`True`, the producer willensure that exactly one copy of each message is written in thestream. If :data:`False`, producer retries due to broker failures,etc., may write duplicates of the retried message in the stream.Note that enabling idempotence acks to set to ``all``. If it is notexplicitly set by the user it will be chosen. If incompatiblevalues are set, a :exc:`ValueError` will be thrown.New in version 0.5.0. | `False` |
| `sasl_mechanism` |  | Authentication mechanism when security_protocolis configured for ``SASL_PLAINTEXT`` or ``SASL_SSL``. Valid valuesare: ``PLAIN``, ``GSSAPI``, ``SCRAM-SHA-256``, ``SCRAM-SHA-512``,``OAUTHBEARER``.Default: ``PLAIN`` | `'PLAIN'` |
| `sasl_plain_username` |  | username for SASL ``PLAIN`` authentication.Default: :data:`None` | `None` |
| `sasl_plain_password` |  | password for SASL ``PLAIN`` authentication.Default: :data:`None` | `None` |
| `group_id` |  | name of the consumer group to join for dynamicpartition assignment (if enabled), and to use for fetching andcommitting offsets. If None, auto-partition assignment (viagroup coordinator) and offset commits are disabled.Default: None | `None` |
| `key_deserializer` |  | Any callable that takes araw message key and returns a deserialized key. | `None` |
| `value_deserializer` |  | Any callable that takes araw message value and returns a deserialized value. | `None` |
| `fetch_min_bytes` |  | Minimum amount of data the server shouldreturn for a fetch request, otherwise wait up to`fetch_max_wait_ms` for more data to accumulate. Default: 1. | `1` |
| `fetch_max_bytes` |  | The maximum amount of data the server shouldreturn for a fetch request. This is not an absolute maximum, ifthe first message in the first non-empty partition of the fetchis larger than this value, the message will still be returnedto ensure that the consumer can make progress. NOTE: consumerperforms fetches to multiple brokers in parallel so memoryusage will depend on the number of brokers containingpartitions for the topic.Supported Kafka version >= 0.10.1.0. Default: 52428800 (50 Mb). | `52428800` |
| `fetch_max_wait_ms` |  | The maximum amount of time in millisecondsthe server will block before answering the fetch request ifthere isn't sufficient data to immediately satisfy therequirement given by fetch_min_bytes. Default: 500. | `500` |
| `max_partition_fetch_bytes` |  | The maximum amount of dataper-partition the server will return. The maximum total memoryused for a request ``= #partitions * max_partition_fetch_bytes``.This size must be at least as large as the maximum message sizethe server allows or else it is possible for the producer tosend messages larger than the consumer can fetch. If thathappens, the consumer can get stuck trying to fetch a largemessage on a certain partition. Default: 1048576. | `1048576` |
| `max_poll_records` |  | The maximum number of records returned in asingle call to :meth:`.getmany`. Defaults ``None``, no limit. | `None` |
| `auto_offset_reset` |  | A policy for resetting offsets on:exc:`.OffsetOutOfRangeError` errors: ``earliest`` will move to the oldestavailable message, ``latest`` will move to the most recent, and``none`` will raise an exception so you can handle this case.Default: ``latest``. | `'latest'` |
| `enable_auto_commit` |  | If true the consumer's offset will beperiodically committed in the background. Default: True. | `True` |
| `auto_commit_interval_ms` |  | milliseconds between automaticoffset commits, if enable_auto_commit is True. Default: 5000. | `5000` |
| `check_crcs` |  | Automatically check the CRC32 of the recordsconsumed. This ensures no on-the-wire or on-disk corruption tothe messages occurred. This check adds some overhead, so it maybe disabled in cases seeking extreme performance. Default: True | `True` |
| `partition_assignment_strategy` |  | List of objects to use todistribute partition ownership amongst consumer instances whengroup management is used. This preference is implicit in the orderof the strategies in the list. When assignment strategy changes:to support a change to the assignment strategy, new versions mustenable support both for the old assignment strategy and the newone. The coordinator will choose the old assignment strategy untilall members have been updated. Then it will choose the newstrategy. Default: [:class:`.RoundRobinPartitionAssignor`] | `(<class 'kafka.coordinator.assignors.roundrobin.RoundRobinPartitionAssignor'>,)` |
| `max_poll_interval_ms` |  | Maximum allowed time between calls toconsume messages (e.g., :meth:`.getmany`). If this intervalis exceeded the consumer is considered failed and the group willrebalance in order to reassign the partitions to another consumergroup member. If API methods block waiting for messages, that timedoes not count against this timeout. See `KIP-62`_ for moreinformation. Default 300000 | `300000` |
| `rebalance_timeout_ms` |  | The maximum time server will wait for thisconsumer to rejoin the group in a case of rebalance. In Java clientthis behaviour is bound to `max.poll.interval.ms` configuration,but as ``aiokafka`` will rejoin the group in the background, wedecouple this setting to allow finer tuning by users that use:class:`.ConsumerRebalanceListener` to delay rebalacing. Defaultsto ``session_timeout_ms`` | `None` |
| `session_timeout_ms` |  | Client group session and failure detectiontimeout. The consumer sends periodic heartbeats(`heartbeat.interval.ms`) to indicate its liveness to the broker.If no hearts are received by the broker for a group member withinthe session timeout, the broker will remove the consumer from thegroup and trigger a rebalance. The allowed range is configured withthe **broker** configuration properties`group.min.session.timeout.ms` and `group.max.session.timeout.ms`.Default: 10000 | `10000` |
| `heartbeat_interval_ms` |  | The expected time in millisecondsbetween heartbeats to the consumer coordinator when usingKafka's group management feature. Heartbeats are used to ensurethat the consumer's session stays active and to facilitaterebalancing when new consumers join or leave the group. Thevalue must be set lower than `session_timeout_ms`, but typicallyshould be set no higher than 1/3 of that value. It can beadjusted even lower to control the expected time for normalrebalances. Default: 3000 | `3000` |
| `consumer_timeout_ms` |  | maximum wait timeout for background fetchingroutine. Mostly defines how fast the system will see rebalance andrequest new data for new partitions. Default: 200 | `200` |
| `exclude_internal_topics` |  | Whether records from internal topics(such as offsets) should be exposed to the consumer. If set to Truethe only way to receive records from an internal topic issubscribing to it. Requires 0.10+ Default: True | `True` |
| `isolation_level` |  | Controls how to read messages writtentransactionally.If set to ``read_committed``, :meth:`.getmany` will only returntransactional messages which have been committed.If set to ``read_uncommitted`` (the default), :meth:`.getmany` willreturn all messages, even transactional messages which have beenaborted.Non-transactional messages will be returned unconditionally ineither mode.Messages will always be returned in offset order. Hence, in`read_committed` mode, :meth:`.getmany` will only returnmessages up to the last stable offset (LSO), which is the one lessthan the offset of the first open transaction. In particular anymessages appearing after messages belonging to ongoing transactionswill be withheld until the relevant transaction has been completed.As a result, `read_committed` consumers will not be able to read upto the high watermark when there are in flight transactions.Further, when in `read_committed` the seek_to_end method willreturn the LSO. See method docs below. Default: ``read_uncommitted`` | `'read_uncommitted'` |
| `sasl_oauth_token_provider` |  | OAuthBearer token provider instance. (See :mod:`kafka.oauth.abstract`).Default: None | `None` |

### benchmark {#fastkafka._application.app.FastKafka.benchmark}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_application/app.py#L1108-L1159" class="link-to-source" target="_blank">View source</a>

```py
benchmark(
    self, interval=1, sliding_window_size=None
)
```

Decorator to benchmark produces/consumes functions

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `interval` | `Union[int, datetime.timedelta]` | Period to use to calculate throughput. If value is of type int,then it will be used as seconds. If value is of type timedelta,then it will be used as it is. default: 1 - one second | `1` |
| `sliding_window_size` | `Optional[int]` | The size of the sliding window to use to calculateaverage throughput. default: None - By default average throughput isnot calculated | `None` |

### consumes {#fastkafka._application.app.FastKafka.consumes}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_application/app.py#L474-L557" class="link-to-source" target="_blank">View source</a>

```py
consumes(
    self,
    topic=None,
    decoder='json',
    executor=None,
    brokers=None,
    prefix='on_',
    description=None,
    loop=None,
    bootstrap_servers='localhost',
    client_id='aiokafka-0.8.1',
    group_id=None,
    key_deserializer=None,
    value_deserializer=None,
    fetch_max_wait_ms=500,
    fetch_max_bytes=52428800,
    fetch_min_bytes=1,
    max_partition_fetch_bytes=1048576,
    request_timeout_ms=40000,
    retry_backoff_ms=100,
    auto_offset_reset='latest',
    enable_auto_commit=True,
    auto_commit_interval_ms=5000,
    check_crcs=True,
    metadata_max_age_ms=300000,
    partition_assignment_strategy=(<class 'kafka.coordinator.assignors.roundrobin.RoundRobinPartitionAssignor'>,),
    max_poll_interval_ms=300000,
    rebalance_timeout_ms=None,
    session_timeout_ms=10000,
    heartbeat_interval_ms=3000,
    consumer_timeout_ms=200,
    max_poll_records=None,
    ssl_context=None,
    security_protocol='PLAINTEXT',
    api_version='auto',
    exclude_internal_topics=True,
    connections_max_idle_ms=540000,
    isolation_level='read_uncommitted',
    sasl_mechanism='PLAIN',
    sasl_plain_password=None,
    sasl_plain_username=None,
    sasl_kerberos_service_name='kafka',
    sasl_kerberos_domain_name=None,
    sasl_oauth_token_provider=None,
)
```

Decorator registering the callback called when a message is received in a topic.

This function decorator is also responsible for registering topics for AsyncAPI specificiation and documentation.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `topic` | `Optional[str]` | Kafka topic that the consumer will subscribe to and execute thedecorated function when it receives a message from the topic,default: None. If the topic is not specified, topic name will beinferred from the decorated function name by stripping the defined prefix | `None` |
| `decoder` | `Union[str, Callable[[bytes, Type[pydantic.main.BaseModel]], Any]]` | Decoder to use to decode messages consumed from the topic,default: json - By default, it uses json decoder to decodebytes to json string and then it creates instance of pydanticBaseModel. It also accepts custom decoder function. | `'json'` |
| `executor` | `Union[str, fastkafka._components.task_streaming.StreamExecutor, NoneType]` | Type of executor to choose for consuming tasks. Avaliable optionsare "SequentialExecutor" and "DynamicTaskExecutor". The default option is"SequentialExecutor" which will execute the consuming tasks sequentially.If the consuming tasks have high latency it is recommended to use"DynamicTaskExecutor" which will wrap the consuming functions into tasksand run them in on asyncio loop in background. This comes with a cost ofincreased overhead so use it only in cases when your consume functions havehigh latency such as database queries or some other type of networking. | `None` |
| `prefix` | `str` | Prefix stripped from the decorated function to define a topic nameif the topic argument is not passed, default: "on_". If the decoratedfunction name is not prefixed with the defined prefix and topic argumentis not passed, then this method will throw ValueError | `'on_'` |
| `brokers` | `Union[Dict[str, Any], fastkafka._components.asyncapi.KafkaBrokers, NoneType]` | Optional argument specifying multiple broker clusters for consumingmessages from different Kafka clusters in FastKafka. | `None` |
| `description` | `Optional[str]` | Optional description of the consuming function async docs.If not provided, consuming function __doc__ attr will be used. | `None` |
| `bootstrap_servers` |  | a ``host[:port]`` string (or list of``host[:port]`` strings) that the consumer should contact to bootstrapinitial cluster metadata.This does not have to be the full node list.It just needs to have at least one broker that will respond to aMetadata API Request. Default port is 9092. If no servers arespecified, will default to ``localhost:9092``. | `'localhost'` |
| `client_id` |  | a name for this client. This string is passed ineach request to servers and can be used to identify specificserver-side log entries that correspond to this client. Alsosubmitted to :class:`~.consumer.group_coordinator.GroupCoordinator`for logging with respect to consumer group administration. Default:``aiokafka-{version}`` | `'aiokafka-0.8.1'` |
| `group_id` |  | name of the consumer group to join for dynamicpartition assignment (if enabled), and to use for fetching andcommitting offsets. If None, auto-partition assignment (viagroup coordinator) and offset commits are disabled.Default: None | `None` |
| `key_deserializer` |  | Any callable that takes araw message key and returns a deserialized key. | `None` |
| `value_deserializer` |  | Any callable that takes araw message value and returns a deserialized value. | `None` |
| `fetch_min_bytes` |  | Minimum amount of data the server shouldreturn for a fetch request, otherwise wait up to`fetch_max_wait_ms` for more data to accumulate. Default: 1. | `1` |
| `fetch_max_bytes` |  | The maximum amount of data the server shouldreturn for a fetch request. This is not an absolute maximum, ifthe first message in the first non-empty partition of the fetchis larger than this value, the message will still be returnedto ensure that the consumer can make progress. NOTE: consumerperforms fetches to multiple brokers in parallel so memoryusage will depend on the number of brokers containingpartitions for the topic.Supported Kafka version >= 0.10.1.0. Default: 52428800 (50 Mb). | `52428800` |
| `fetch_max_wait_ms` |  | The maximum amount of time in millisecondsthe server will block before answering the fetch request ifthere isn't sufficient data to immediately satisfy therequirement given by fetch_min_bytes. Default: 500. | `500` |
| `max_partition_fetch_bytes` |  | The maximum amount of dataper-partition the server will return. The maximum total memoryused for a request ``= #partitions * max_partition_fetch_bytes``.This size must be at least as large as the maximum message sizethe server allows or else it is possible for the producer tosend messages larger than the consumer can fetch. If thathappens, the consumer can get stuck trying to fetch a largemessage on a certain partition. Default: 1048576. | `1048576` |
| `max_poll_records` |  | The maximum number of records returned in asingle call to :meth:`.getmany`. Defaults ``None``, no limit. | `None` |
| `request_timeout_ms` |  | Client request timeout in milliseconds.Default: 40000. | `40000` |
| `retry_backoff_ms` |  | Milliseconds to backoff when retrying onerrors. Default: 100. | `100` |
| `auto_offset_reset` |  | A policy for resetting offsets on:exc:`.OffsetOutOfRangeError` errors: ``earliest`` will move to the oldestavailable message, ``latest`` will move to the most recent, and``none`` will raise an exception so you can handle this case.Default: ``latest``. | `'latest'` |
| `enable_auto_commit` |  | If true the consumer's offset will beperiodically committed in the background. Default: True. | `True` |
| `auto_commit_interval_ms` |  | milliseconds between automaticoffset commits, if enable_auto_commit is True. Default: 5000. | `5000` |
| `check_crcs` |  | Automatically check the CRC32 of the recordsconsumed. This ensures no on-the-wire or on-disk corruption tothe messages occurred. This check adds some overhead, so it maybe disabled in cases seeking extreme performance. Default: True | `True` |
| `metadata_max_age_ms` |  | The period of time in milliseconds afterwhich we force a refresh of metadata even if we haven't seen anypartition leadership changes to proactively discover any newbrokers or partitions. Default: 300000 | `300000` |
| `partition_assignment_strategy` |  | List of objects to use todistribute partition ownership amongst consumer instances whengroup management is used. This preference is implicit in the orderof the strategies in the list. When assignment strategy changes:to support a change to the assignment strategy, new versions mustenable support both for the old assignment strategy and the newone. The coordinator will choose the old assignment strategy untilall members have been updated. Then it will choose the newstrategy. Default: [:class:`.RoundRobinPartitionAssignor`] | `(<class 'kafka.coordinator.assignors.roundrobin.RoundRobinPartitionAssignor'>,)` |
| `max_poll_interval_ms` |  | Maximum allowed time between calls toconsume messages (e.g., :meth:`.getmany`). If this intervalis exceeded the consumer is considered failed and the group willrebalance in order to reassign the partitions to another consumergroup member. If API methods block waiting for messages, that timedoes not count against this timeout. See `KIP-62`_ for moreinformation. Default 300000 | `300000` |
| `rebalance_timeout_ms` |  | The maximum time server will wait for thisconsumer to rejoin the group in a case of rebalance. In Java clientthis behaviour is bound to `max.poll.interval.ms` configuration,but as ``aiokafka`` will rejoin the group in the background, wedecouple this setting to allow finer tuning by users that use:class:`.ConsumerRebalanceListener` to delay rebalacing. Defaultsto ``session_timeout_ms`` | `None` |
| `session_timeout_ms` |  | Client group session and failure detectiontimeout. The consumer sends periodic heartbeats(`heartbeat.interval.ms`) to indicate its liveness to the broker.If no hearts are received by the broker for a group member withinthe session timeout, the broker will remove the consumer from thegroup and trigger a rebalance. The allowed range is configured withthe **broker** configuration properties`group.min.session.timeout.ms` and `group.max.session.timeout.ms`.Default: 10000 | `10000` |
| `heartbeat_interval_ms` |  | The expected time in millisecondsbetween heartbeats to the consumer coordinator when usingKafka's group management feature. Heartbeats are used to ensurethat the consumer's session stays active and to facilitaterebalancing when new consumers join or leave the group. Thevalue must be set lower than `session_timeout_ms`, but typicallyshould be set no higher than 1/3 of that value. It can beadjusted even lower to control the expected time for normalrebalances. Default: 3000 | `3000` |
| `consumer_timeout_ms` |  | maximum wait timeout for background fetchingroutine. Mostly defines how fast the system will see rebalance andrequest new data for new partitions. Default: 200 | `200` |
| `api_version` |  | specify which kafka API version to use.:class:`AIOKafkaConsumer` supports Kafka API versions >=0.9 only.If set to ``auto``, will attempt to infer the broker version byprobing various APIs. Default: ``auto`` | `'auto'` |
| `security_protocol` |  | Protocol used to communicate with brokers.Valid values are: ``PLAINTEXT``, ``SSL``, ``SASL_PLAINTEXT``,``SASL_SSL``. Default: ``PLAINTEXT``. | `'PLAINTEXT'` |
| `ssl_context` |  | pre-configured :class:`~ssl.SSLContext`for wrapping socket connections. Directly passed into asyncio's:meth:`~asyncio.loop.create_connection`. For more information see:ref:`ssl_auth`. Default: None. | `None` |
| `exclude_internal_topics` |  | Whether records from internal topics(such as offsets) should be exposed to the consumer. If set to Truethe only way to receive records from an internal topic issubscribing to it. Requires 0.10+ Default: True | `True` |
| `connections_max_idle_ms` |  | Close idle connections after the numberof milliseconds specified by this config. Specifying `None` willdisable idle checks. Default: 540000 (9 minutes). | `540000` |
| `isolation_level` |  | Controls how to read messages writtentransactionally.If set to ``read_committed``, :meth:`.getmany` will only returntransactional messages which have been committed.If set to ``read_uncommitted`` (the default), :meth:`.getmany` willreturn all messages, even transactional messages which have beenaborted.Non-transactional messages will be returned unconditionally ineither mode.Messages will always be returned in offset order. Hence, in`read_committed` mode, :meth:`.getmany` will only returnmessages up to the last stable offset (LSO), which is the one lessthan the offset of the first open transaction. In particular anymessages appearing after messages belonging to ongoing transactionswill be withheld until the relevant transaction has been completed.As a result, `read_committed` consumers will not be able to read upto the high watermark when there are in flight transactions.Further, when in `read_committed` the seek_to_end method willreturn the LSO. See method docs below. Default: ``read_uncommitted`` | `'read_uncommitted'` |
| `sasl_mechanism` |  | Authentication mechanism when security_protocolis configured for ``SASL_PLAINTEXT`` or ``SASL_SSL``. Valid values are:``PLAIN``, ``GSSAPI``, ``SCRAM-SHA-256``, ``SCRAM-SHA-512``,``OAUTHBEARER``.Default: ``PLAIN`` | `'PLAIN'` |
| `sasl_plain_username` |  | username for SASL ``PLAIN`` authentication.Default: None | `None` |
| `sasl_plain_password` |  | password for SASL ``PLAIN`` authentication.Default: None | `None` |
| `sasl_oauth_token_provider` |  | OAuthBearer token provider instance. (See :mod:`kafka.oauth.abstract`).Default: None | `None` |

**Returns**:

|  Type | Description |
|---|---|
| `Callable[[Union[Callable[[Union[List[pydantic.main.BaseModel], pydantic.main.BaseModel]], Awaitable[None]], Callable[[Union[List[pydantic.main.BaseModel], pydantic.main.BaseModel], Union[List[fastkafka.EventMetadata], fastkafka.EventMetadata]], Awaitable[None]], Callable[[Union[List[pydantic.main.BaseModel], pydantic.main.BaseModel]], None], Callable[[Union[List[pydantic.main.BaseModel], pydantic.main.BaseModel], Union[List[fastkafka.EventMetadata], fastkafka.EventMetadata]], None]]], Union[Callable[[Union[List[pydantic.main.BaseModel], pydantic.main.BaseModel]], Awaitable[None]], Callable[[Union[List[pydantic.main.BaseModel], pydantic.main.BaseModel], Union[List[fastkafka.EventMetadata], fastkafka.EventMetadata]], Awaitable[None]], Callable[[Union[List[pydantic.main.BaseModel], pydantic.main.BaseModel]], None], Callable[[Union[List[pydantic.main.BaseModel], pydantic.main.BaseModel], Union[List[fastkafka.EventMetadata], fastkafka.EventMetadata]], None]]]` | : A function returning the same function |

### create_docs {#fastkafka._application.app.FastKafka.create_docs}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_application/app.py#L938-L964" class="link-to-source" target="_blank">View source</a>

```py
create_docs(
    self
)
```

Create the asyncapi documentation based on the configured consumers and producers.

This function exports the asyncapi specification based on the configured consumers
and producers in the FastKafka instance. It generates the asyncapi documentation by
extracting the topics and callbacks from the consumers and producers.

Note:
    The asyncapi documentation is saved to the location specified by the `_asyncapi_path`
    attribute of the FastKafka instance.

### create_mocks {#fastkafka._application.app.FastKafka.create_mocks}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_application/app.py#L1026-L1104" class="link-to-source" target="_blank">View source</a>

```py
create_mocks(
    self
)
```

Creates self.mocks as a named tuple mapping a new function obtained by calling the original functions and a mock

### fastapi_lifespan {#fastkafka._application.app.FastKafka.fastapi_lifespan}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_application/app.py#L1163-L1182" class="link-to-source" target="_blank">View source</a>

```py
fastapi_lifespan(
    self, kafka_broker_name
)
```

Method for managing the lifespan of a FastAPI application with a specific Kafka broker.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `kafka_broker_name` | `str` | The name of the Kafka broker to start FastKafka | *required* |

**Returns**:

|  Type | Description |
|---|---|
| `Callable[[ForwardRef('FastAPI')], AsyncIterator[None]]` | Lifespan function to use for initializing FastAPI |

### get_topics {#fastkafka._application.app.FastKafka.get_topics}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_application/app.py#L663-L672" class="link-to-source" target="_blank">View source</a>

```py
get_topics(
    self
)
```

Get all topics for both producing and consuming.

**Returns**:

|  Type | Description |
|---|---|
| `Iterable[str]` | A set of topics for both producing and consuming. |

### is_started {#fastkafka._application.app.FastKafka.is_started}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_application/app.py#L308-L319" class="link-to-source" target="_blank">View source</a>

```py
@property
is_started(
    self
)
```

Property indicating whether the FastKafka object is started.

The is_started property indicates if the FastKafka object is currently
in a started state. This implies that all background tasks, producers,
and consumers have been initiated, and the object is successfully connected
to the Kafka broker.

**Returns**:

|  Type | Description |
|---|---|
| `bool` | True if the object is started, False otherwise. |

### produces {#fastkafka._application.app.FastKafka.produces}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_application/app.py#L582-L659" class="link-to-source" target="_blank">View source</a>

```py
produces(
    self,
    topic=None,
    encoder='json',
    prefix='to_',
    brokers=None,
    description=None,
    loop=None,
    bootstrap_servers='localhost',
    client_id=None,
    metadata_max_age_ms=300000,
    request_timeout_ms=40000,
    api_version='auto',
    acks=<object object at 0x7ff10d5f9100>,
    key_serializer=None,
    value_serializer=None,
    compression_type=None,
    max_batch_size=16384,
    partitioner=<kafka.partitioner.default.DefaultPartitioner object at 0x7ff10c16e2d0>,
    max_request_size=1048576,
    linger_ms=0,
    send_backoff_ms=100,
    retry_backoff_ms=100,
    security_protocol='PLAINTEXT',
    ssl_context=None,
    connections_max_idle_ms=540000,
    enable_idempotence=False,
    transactional_id=None,
    transaction_timeout_ms=60000,
    sasl_mechanism='PLAIN',
    sasl_plain_password=None,
    sasl_plain_username=None,
    sasl_kerberos_service_name='kafka',
    sasl_kerberos_domain_name=None,
    sasl_oauth_token_provider=None,
)
```

Decorator registering the callback called when delivery report for a produced message is received

This function decorator is also responsible for registering topics for AsyncAPI specificiation and documentation.

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `topic` | `Optional[str]` | Kafka topic that the producer will send returned values fromthe decorated function to, default: None- If the topic is notspecified, topic name will be inferred from the decorated functionname by stripping the defined prefix. | `None` |
| `encoder` | `Union[str, Callable[[pydantic.main.BaseModel], bytes]]` | Encoder to use to encode messages before sending it to topic,default: json - By default, it uses json encoder to convertpydantic basemodel to json string and then encodes the string to bytesusing 'utf-8' encoding. It also accepts custom encoder function. | `'json'` |
| `prefix` | `str` | Prefix stripped from the decorated function to define a topicname if the topic argument is not passed, default: "to_". If thedecorated function name is not prefixed with the defined prefixand topic argument is not passed, then this method will throw ValueError | `'to_'` |
| `brokers` | `Union[Dict[str, Any], fastkafka._components.asyncapi.KafkaBrokers, NoneType]` | Optional argument specifying multiple broker clusters for consumingmessages from different Kafka clusters in FastKafka. | `None` |
| `description` | `Optional[str]` | Optional description of the producing function async docs.If not provided, producing function __doc__ attr will be used. | `None` |
| `bootstrap_servers` |  | a ``host[:port]`` string or list of``host[:port]`` strings that the producer should contact tobootstrap initial cluster metadata. This does not have to be thefull node list.  It just needs to have at least one broker that willrespond to a Metadata API Request. Default port is 9092. If noservers are specified, will default to ``localhost:9092``. | `'localhost'` |
| `client_id` |  | a name for this client. This string is passed ineach request to servers and can be used to identify specificserver-side log entries that correspond to this client.Default: ``aiokafka-producer-#`` (appended with a unique numberper instance) | `None` |
| `key_serializer` |  | used to convert user-supplied keys to bytesIf not :data:`None`, called as ``f(key),`` should return:class:`bytes`.Default: :data:`None`. | `None` |
| `value_serializer` |  | used to convert user-supplied messagevalues to :class:`bytes`. If not :data:`None`, called as``f(value)``, should return :class:`bytes`.Default: :data:`None`. | `None` |
| `acks` |  | one of ``0``, ``1``, ``all``. The number of acknowledgmentsthe producer requires the leader to have received before considering arequest complete. This controls the durability of records that aresent. The following settings are common:* ``0``: Producer will not wait for any acknowledgment from the server  at all. The message will immediately be added to the socket  buffer and considered sent. No guarantee can be made that the  server has received the record in this case, and the retries  configuration will not take effect (as the client won't  generally know of any failures). The offset given back for each  record will always be set to -1.* ``1``: The broker leader will write the record to its local log but  will respond without awaiting full acknowledgement from all  followers. In this case should the leader fail immediately  after acknowledging the record but before the followers have  replicated it then the record will be lost.* ``all``: The broker leader will wait for the full set of in-sync  replicas to acknowledge the record. This guarantees that the  record will not be lost as long as at least one in-sync replica  remains alive. This is the strongest available guarantee.If unset, defaults to ``acks=1``. If `enable_idempotence` is:data:`True` defaults to ``acks=all`` | `<object object at 0x7ff10d5f9100>` |
| `compression_type` |  | The compression type for all data generated bythe producer. Valid values are ``gzip``, ``snappy``, ``lz4``, ``zstd``or :data:`None`.Compression is of full batches of data, so the efficacy of batchingwill also impact the compression ratio (more batching means bettercompression). Default: :data:`None`. | `None` |
| `max_batch_size` |  | Maximum size of buffered data per partition.After this amount :meth:`send` coroutine will block until batch isdrained.Default: 16384 | `16384` |
| `linger_ms` |  | The producer groups together any records that arrivein between request transmissions into a single batched request.Normally this occurs only under load when records arrive fasterthan they can be sent out. However in some circumstances the clientmay want to reduce the number of requests even under moderate load.This setting accomplishes this by adding a small amount ofartificial delay; that is, if first request is processed faster,than `linger_ms`, producer will wait ``linger_ms - process_time``.Default: 0 (i.e. no delay). | `0` |
| `partitioner` |  | Callable used to determine which partitioneach message is assigned to. Called (after key serialization):``partitioner(key_bytes, all_partitions, available_partitions)``.The default partitioner implementation hashes each non-None keyusing the same murmur2 algorithm as the Java client so thatmessages with the same key are assigned to the same partition.When a key is :data:`None`, the message is delivered to a random partition(filtered to partitions with available leaders only, if possible). | `<kafka.partitioner.default.DefaultPartitioner object at 0x7ff10c16e2d0>` |
| `max_request_size` |  | The maximum size of a request. This is alsoeffectively a cap on the maximum record size. Note that the serverhas its own cap on record size which may be different from this.This setting will limit the number of record batches the producerwill send in a single request to avoid sending huge requests.Default: 1048576. | `1048576` |
| `metadata_max_age_ms` |  | The period of time in milliseconds afterwhich we force a refresh of metadata even if we haven't seen anypartition leadership changes to proactively discover any newbrokers or partitions. Default: 300000 | `300000` |
| `request_timeout_ms` |  | Produce request timeout in milliseconds.As it's sent as part of:class:`~kafka.protocol.produce.ProduceRequest` (it's a blockingcall), maximum waiting time can be up to ``2 *request_timeout_ms``.Default: 40000. | `40000` |
| `retry_backoff_ms` |  | Milliseconds to backoff when retrying onerrors. Default: 100. | `100` |
| `api_version` |  | specify which kafka API version to use.If set to ``auto``, will attempt to infer the broker version byprobing various APIs. Default: ``auto`` | `'auto'` |
| `security_protocol` |  | Protocol used to communicate with brokers.Valid values are: ``PLAINTEXT``, ``SSL``, ``SASL_PLAINTEXT``,``SASL_SSL``. Default: ``PLAINTEXT``. | `'PLAINTEXT'` |
| `ssl_context` |  | pre-configured :class:`~ssl.SSLContext`for wrapping socket connections. Directly passed into asyncio's:meth:`~asyncio.loop.create_connection`. For moreinformation see :ref:`ssl_auth`.Default: :data:`None` | `None` |
| `connections_max_idle_ms` |  | Close idle connections after the numberof milliseconds specified by this config. Specifying :data:`None` willdisable idle checks. Default: 540000 (9 minutes). | `540000` |
| `enable_idempotence` |  | When set to :data:`True`, the producer willensure that exactly one copy of each message is written in thestream. If :data:`False`, producer retries due to broker failures,etc., may write duplicates of the retried message in the stream.Note that enabling idempotence acks to set to ``all``. If it is notexplicitly set by the user it will be chosen. If incompatiblevalues are set, a :exc:`ValueError` will be thrown.New in version 0.5.0. | `False` |
| `sasl_mechanism` |  | Authentication mechanism when security_protocolis configured for ``SASL_PLAINTEXT`` or ``SASL_SSL``. Valid valuesare: ``PLAIN``, ``GSSAPI``, ``SCRAM-SHA-256``, ``SCRAM-SHA-512``,``OAUTHBEARER``.Default: ``PLAIN`` | `'PLAIN'` |
| `sasl_plain_username` |  | username for SASL ``PLAIN`` authentication.Default: :data:`None` | `None` |
| `sasl_plain_password` |  | password for SASL ``PLAIN`` authentication.Default: :data:`None` | `None` |

**Returns**:

|  Type | Description |
|---|---|
| `Callable[[Union[Callable[..., Union[pydantic.main.BaseModel, fastkafka.KafkaEvent[pydantic.main.BaseModel], List[pydantic.main.BaseModel], fastkafka.KafkaEvent[List[pydantic.main.BaseModel]]]], Callable[..., Awaitable[Union[pydantic.main.BaseModel, fastkafka.KafkaEvent[pydantic.main.BaseModel], List[pydantic.main.BaseModel], fastkafka.KafkaEvent[List[pydantic.main.BaseModel]]]]]]], Union[Callable[..., Union[pydantic.main.BaseModel, fastkafka.KafkaEvent[pydantic.main.BaseModel], List[pydantic.main.BaseModel], fastkafka.KafkaEvent[List[pydantic.main.BaseModel]]]], Callable[..., Awaitable[Union[pydantic.main.BaseModel, fastkafka.KafkaEvent[pydantic.main.BaseModel], List[pydantic.main.BaseModel], fastkafka.KafkaEvent[List[pydantic.main.BaseModel]]]]]]]` | : A function returning the same function |

**Exceptions**:

|  Type | Description |
|---|---|
| `ValueError` | when needed |

### run_in_background {#fastkafka._application.app.FastKafka.run_in_background}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_application/app.py#L676-L709" class="link-to-source" target="_blank">View source</a>

```py
run_in_background(
    self
)
```

Decorator to schedule a task to be run in the background.

This decorator is used to schedule a task to be run in the background when the app's `_on_startup` event is triggered.

**Returns**:

|  Type | Description |
|---|---|
| `Callable[[Callable[..., Coroutine[Any, Any, Any]]], Callable[..., Coroutine[Any, Any, Any]]]` | A decorator function that takes a background task as an input and stores it to be run in the backround. |

### set_kafka_broker {#fastkafka._application.app.FastKafka.set_kafka_broker}

<a href="https://github.com/airtai/fastkafka/blob/0.8.0/fastkafka/_application/app.py#L321-L337" class="link-to-source" target="_blank">View source</a>

```py
set_kafka_broker(
    self, kafka_broker_name
)
```

Sets the Kafka broker to start FastKafka with

**Parameters**:

|  Name | Type | Description | Default |
|---|---|---|---|
| `kafka_broker_name` | `str` | The name of the Kafka broker to start FastKafka | *required* |

**Exceptions**:

|  Type | Description |
|---|---|
| `ValueError` | If the provided kafka_broker_name is not found in dictionary of kafka_brokers |


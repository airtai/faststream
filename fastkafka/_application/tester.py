# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/016_Tester.ipynb.

# %% auto 0
__all__ = ['Tester', 'mirror_producer', 'mirror_consumer', 'ambigious_warning', 'set_sugar']

# %% ../../nbs/016_Tester.ipynb 1
import asyncio
import collections
import inspect
from unittest.mock import AsyncMock, MagicMock
import json
from contextlib import asynccontextmanager
from itertools import groupby
from typing import *

from pydantic import BaseModel

from .. import KafkaEvent
from .app import FastKafka, AwaitedMock, _get_kafka_brokers
from .._components.asyncapi import KafkaBroker, KafkaBrokers
from .._components.helpers import unwrap_list_type
from .._components.meta import delegates, export, patch
from .._components.producer_decorator import unwrap_from_kafka_event
from .._testing.apache_kafka_broker import ApacheKafkaBroker
from .._testing.in_memory_broker import InMemoryBroker
from .._testing.local_redpanda_broker import LocalRedpandaBroker
from .._components.helpers import remove_suffix

# %% ../../nbs/016_Tester.ipynb 7
def _get_broker_spec(bootstrap_server: str) -> KafkaBroker:
    url = bootstrap_server.split(":")[0]
    port = bootstrap_server.split(":")[1]
    return KafkaBroker(url=url, port=port)

# %% ../../nbs/016_Tester.ipynb 9
@export("fastkafka.testing")
class Tester(FastKafka):
    __test__ = False

    @delegates(ApacheKafkaBroker.__init__)
    def __init__(
        self,
        app: Union[FastKafka, List[FastKafka]],
        *,
        broker: Optional[
            Union[ApacheKafkaBroker, LocalRedpandaBroker, InMemoryBroker]
        ] = None,
    ):
        """Mirror-like object for testing a FastFafka application

        Can be used as context manager

        """
        self.apps = app if isinstance(app, list) else [app]

        for app in self.apps:
            app.create_mocks()

        super().__init__()
        self.mirrors: Dict[Any, Any] = {}
        self.create_mirrors()
        self.create_mocks()
        self.arrange_mirrors()
        self.broker = broker

        unique_broker_configs = []
        for app in self.apps:
            for broker_config in app._override_brokers:
                if broker_config not in unique_broker_configs:
                    unique_broker_configs.append(broker_config)
        self.num_brokers = len(unique_broker_configs)

        self.overriden_brokers: List[Union[ApacheKafkaBroker, LocalRedpandaBroker]] = []

    @delegates(LocalRedpandaBroker.__init__)
    def using_local_redpanda(self, **kwargs: Any) -> "Tester":
        """Starts local Redpanda broker used by the Tester instance

        Args:
            listener_port: Port on which the clients (producers and consumers) can connect
            tag: Tag of Redpanda image to use to start container
            seastar_core: Core(s) to use byt Seastar (the framework Redpanda uses under the hood)
            memory: The amount of memory to make available to Redpanda
            mode: Mode to use to load configuration properties in container
            default_log_level: Log levels to use for Redpanda
            topics: List of topics to create after sucessfull redpanda broker startup
            retries: Number of retries to create redpanda service
            apply_nest_asyncio: set to True if running in notebook
            port allocation if the requested port was taken

        Returns:
            An instance of tester with Redpanda as broker
        """
        topics = set().union(*(app.get_topics() for app in self.apps))
        kwargs["topics"] = (
            topics.union(kwargs["topics"]) if "topics" in kwargs else topics
        )
        self.broker = LocalRedpandaBroker(**kwargs)
        self.overriden_brokers = [
            LocalRedpandaBroker(**kwargs) for _ in range(self.num_brokers)
        ]
        return self

    @delegates(ApacheKafkaBroker.__init__)
    def using_local_kafka(self, **kwargs: Any) -> "Tester":
        """Starts local Kafka broker used by the Tester instance

        Args:
            data_dir: Path to the directory where the zookeepeer instance will save data
            zookeeper_port: Port for clients (Kafka brokes) to connect
            listener_port: Port on which the clients (producers and consumers) can connect
            topics: List of topics to create after sucessfull Kafka broker startup
            retries: Number of retries to create kafka and zookeeper services using random
            apply_nest_asyncio: set to True if running in notebook
            port allocation if the requested port was taken

        Returns:
            An instance of tester with Kafka as broker
        """
        topics = set().union(*(app.get_topics() for app in self.apps))
        kwargs["topics"] = (
            topics.union(kwargs["topics"]) if "topics" in kwargs else topics
        )
        self.broker = ApacheKafkaBroker(**kwargs)
        self.overriden_brokers = [
            ApacheKafkaBroker(**kwargs) for _ in range(self.num_brokers)
        ]

        return self

    async def _start_tester(self) -> None:
        """Starts the Tester"""
        for app in self.apps:
            await app.__aenter__()
        await super().__aenter__()
        await asyncio.sleep(3)

    async def _stop_tester(self) -> None:
        """Shuts down the Tester"""
        await super().__aexit__(None, None, None)
        for app in self.apps[::-1]:
            await app.__aexit__(None, None, None)

    def create_mirrors(self) -> None:
        pass

    def arrange_mirrors(self) -> None:
        pass

    @asynccontextmanager
    async def _create_ctx(self) -> AsyncGenerator["Tester", None]:
        if self.broker is None:
            topics = set().union(*(app.get_topics() for app in self.apps))
            self.broker = InMemoryBroker()

        broker_spec = _get_broker_spec(await self.broker._start())

        try:
            if isinstance(self.broker, (ApacheKafkaBroker, LocalRedpandaBroker)):
                override_broker_configs = [
                    list(grp)
                    for k, grp in groupby(
                        [
                            broker_config
                            for app in self.apps + [self]
                            for broker_config in app._override_brokers
                        ]
                    )
                ]

                for override_brokers_config_groups, broker in zip(
                    override_broker_configs, self.overriden_brokers
                ):
                    b_s = _get_broker_spec(await broker._start())
                    for override_broker_config in override_brokers_config_groups:
                        override_broker_config["fastkafka_tester_broker"] = b_s

                for app in self.apps + [self]:
                    app._kafka_brokers.brokers["fastkafka_tester_broker"] = broker_spec
                    app.set_kafka_broker("fastkafka_tester_broker")
            await self._start_tester()
            try:
                yield self
            finally:
                await self._stop_tester()
        finally:
            await self.broker._stop()
            for broker in self.overriden_brokers:
                await broker._stop()

    async def __aenter__(self) -> "Tester":
        self._ctx = self._create_ctx()
        return await self._ctx.__aenter__()

    async def __aexit__(self, *args: Any) -> None:
        await self._ctx.__aexit__(*args)

# %% ../../nbs/016_Tester.ipynb 20
def mirror_producer(
    topic: str, producer_f: Callable[..., Any], brokers: KafkaBrokers
) -> Callable[..., Any]:
    msg_type = inspect.signature(producer_f).return_annotation

    msg_type_unwrapped = unwrap_list_type(unwrap_from_kafka_event(msg_type))

    async def skeleton_func(msg: BaseModel) -> None:
        pass

    mirror_func = skeleton_func
    sig = inspect.signature(skeleton_func)

    # adjust name, take into consideration the origin app and brokers
    # configuration so that we can differentiate those two
    mirror_func.__name__ = f"mirror_{id(app)}_on_{remove_suffix(topic).replace('.', '_')}_{abs(hash(brokers))}"

    # adjust arg and return val
    sig = sig.replace(
        parameters=[
            inspect.Parameter(
                name="msg",
                annotation=msg_type_unwrapped,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
    )

    mirror_func.__signature__ = sig  # type: ignore

    return mirror_func

# %% ../../nbs/016_Tester.ipynb 23
def mirror_consumer(
    topic: str, consumer_f: Callable[..., Any], brokers: KafkaBrokers
) -> Callable[..., Any]:
    msg_type = inspect.signature(consumer_f).parameters["msg"]

    msg_type_unwrapped = unwrap_list_type(msg_type)

    async def skeleton_func(msg: BaseModel) -> BaseModel:
        return msg

    mirror_func = skeleton_func
    sig = inspect.signature(skeleton_func)

    # adjust name, take into consideration the origin app and brokers
    # configuration so that we can differentiate those two
    mirror_func.__name__ = f"mirror_{id(app)}_to_{remove_suffix(topic).replace('.', '_')}_{abs(hash(brokers))}"

    # adjust arg and return val
    sig = sig.replace(
        parameters=[msg_type], return_annotation=msg_type_unwrapped.annotation
    )

    mirror_func.__signature__ = sig  # type: ignore
    return mirror_func

# %% ../../nbs/016_Tester.ipynb 25
@patch
def create_mirrors(self: Tester) -> None:
    for app in self.apps:
        for topic, (consumer_f, _, _, brokers, _) in app._consumers_store.items():
            mirror_f = mirror_consumer(
                topic,
                consumer_f,
                brokers.json() if brokers is not None else app._kafka_brokers.json(),
            )
            mirror_f = self.produces(  # type: ignore
                topic=remove_suffix(topic),
                brokers=brokers,
            )(mirror_f)
            self.mirrors[consumer_f] = mirror_f
            setattr(self, mirror_f.__name__, mirror_f)
        for topic, (producer_f, _, brokers, _) in app._producers_store.items():
            mirror_f = mirror_producer(
                topic,
                producer_f,
                brokers.json() if brokers is not None else app._kafka_brokers.json(),
            )
            mirror_f = self.consumes(  # type: ignore
                topic=remove_suffix(topic),
                brokers=brokers,
            )(mirror_f)
            self.mirrors[producer_f] = mirror_f
            setattr(self, mirror_f.__name__, mirror_f)

# %% ../../nbs/016_Tester.ipynb 30
class ambigious_warning:
    def __getattribute__(self, attr) -> Any:
        raise Exception(
            "Ambigious topic, please use Tester.mirrors[app.function] to find your topic"
        )

    def __call__(self, *args, **kwargs) -> Any:
        raise Exception(
            "Ambigious topic, please use Tester.mirrors[app.function] to find your topic"
        )

# %% ../../nbs/016_Tester.ipynb 32
def set_sugar(
    *,
    tester: Tester,
    prefix: str,
    topic_brokers: Dict[str, str],
    topic: str,
    brokers: str,
    function,
) -> None:
    brokers_for_topic = topic_brokers.get(topic, [])
    if brokers not in brokers_for_topic:
        brokers_for_topic.append(brokers)
        topic_brokers[topic] = brokers_for_topic
    if len(brokers_for_topic) == 1:
        setattr(tester, f"{prefix}{topic}", function)
    else:
        setattr(tester, f"{prefix}{topic}", ambigious_warning())

# %% ../../nbs/016_Tester.ipynb 33
@patch
def arrange_mirrors(self: Tester) -> None:
    topic_brokers = {}
    mocks = {}
    awaited_mocks = {}
    for app in self.apps:
        for topic, (consumer_f, _, _, brokers, _) in app._consumers_store.items():
            mirror_f = self.mirrors[consumer_f]
            self.mirrors[getattr(app, consumer_f.__name__)] = mirror_f
            #             delattr(self, mirror_f.__name__)   Do we delete the function from tester to not create noise?
            set_sugar(
                tester=self,
                prefix="to_",
                topic_brokers=topic_brokers,
                topic=remove_suffix(topic),
                brokers=brokers.json()
                if brokers is not None
                else app._kafka_brokers.json(),
                function=mirror_f,
            )

            mocks[f"to_{remove_suffix(topic)}"] = getattr(self.mocks, mirror_f.__name__)
            awaited_mocks[f"to_{remove_suffix(topic)}"] = getattr(
                self.awaited_mocks, mirror_f.__name__
            )

        for topic, (producer_f, _, brokers, _) in app._producers_store.items():
            mirror_f = self.mirrors[producer_f]
            self.mirrors[getattr(app, producer_f.__name__)] = getattr(
                self.awaited_mocks, mirror_f.__name__
            )
            set_sugar(
                tester=self,
                prefix="on_",
                topic_brokers=topic_brokers,
                topic=remove_suffix(topic),
                brokers=brokers.json()
                if brokers is not None
                else app._kafka_brokers.json(),
                function=getattr(self.awaited_mocks, mirror_f.__name__),
            )
            mocks[f"on_{remove_suffix(topic)}"] = getattr(self.mocks, mirror_f.__name__)
            awaited_mocks[f"on_{remove_suffix(topic)}"] = getattr(
                self.awaited_mocks, mirror_f.__name__
            )

    AppMocks = collections.namedtuple(  # type: ignore
        f"{self.__class__.__name__}Mocks", [f_name for f_name in mocks]
    )
    setattr(self, "mocks", AppMocks(**mocks))
    setattr(self, "awaited_mocks", AppMocks(**awaited_mocks))

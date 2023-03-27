# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/016_Tester.ipynb.

# %% auto 0
__all__ = ['Tester', 'mirror_producer', 'mirror_consumer']

# %% ../../nbs/016_Tester.ipynb 1
import asyncio
import inspect
from contextlib import asynccontextmanager
from typing import *

from .._components.basics import patch
from .._components.meta import delegates
from pydantic import BaseModel

from .app import FastKafka
from .._testing.local_broker import LocalKafkaBroker
from .._testing.local_redpanda_broker import LocalRedpandaBroker

# %% ../../nbs/016_Tester.ipynb 6
class Tester(FastKafka):
    @delegates(LocalKafkaBroker.__init__)
    def __init__(
        self,
        app: Union[FastKafka, List[FastKafka]],
        *,
        broker: Union[str, LocalKafkaBroker, LocalRedpandaBroker] = "kafka",
        **kwargs: Any,
    ):
        """Mirror-like object for testing a FastFafka application

        Can be used as context manager

        """
        self.apps = app if isinstance(app, list) else [app]
        host, port = self.apps[0]._kafka_config["bootstrap_servers"].split(":")
        super().__init__(kafka_brokers={"localhost": {"url": host, "port": port}})
        self.create_mirrors()

        if isinstance(broker, LocalKafkaBroker) or isinstance(
            broker, LocalRedpandaBroker
        ):
            self.broker = broker
        else:
            topics = set().union(*(app.get_topics() for app in self.apps))
            kwargs["topics"] = topics
            self.broker = (
                LocalRedpandaBroker(**kwargs)
                if broker == "redpanda"
                else LocalKafkaBroker(**kwargs)
            )

    async def startup(self) -> None:
        """Starts the Tester"""
        for app in self.apps:
            app.create_mocks()
            await app.startup()
        self.create_mocks()
        await super().startup()
        await asyncio.sleep(3)

    async def shutdown(self) -> None:
        """Shuts down the Tester"""
        await super().shutdown()
        for app in self.apps[::-1]:
            await app.shutdown()

    def create_mirrors(self) -> None:
        pass

    @asynccontextmanager
    async def _create_ctx(self) -> AsyncGenerator["Tester", None]:
        bootstrap_server = await self.broker._start()
        try:
            self._set_bootstrap_servers(bootstrap_servers=bootstrap_server)
            for app in self.apps:
                app._set_bootstrap_servers(bootstrap_server)
            await self.startup()
            try:
                yield self
            finally:
                await self.shutdown()
        finally:
            await self.broker._stop()

    async def __aenter__(self) -> "Tester":
        self._ctx = self._create_ctx()
        return await self._ctx.__aenter__()

    async def __aexit__(self, *args: Any) -> None:
        await self._ctx.__aexit__(*args)


Tester.__module__ = "fastkafka.testing"

# %% ../../nbs/016_Tester.ipynb 9
def mirror_producer(topic: str, producer_f: Callable[..., Any]) -> Callable[..., Any]:
    msg_type = inspect.signature(producer_f).return_annotation

    async def skeleton_func(msg: BaseModel) -> None:
        pass

    mirror_func = skeleton_func
    sig = inspect.signature(skeleton_func)

    # adjust name
    mirror_func.__name__ = "on_" + topic

    # adjust arg and return val
    sig = sig.replace(
        parameters=[
            inspect.Parameter(
                name="msg",
                annotation=msg_type,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
    )

    mirror_func.__signature__ = sig  # type: ignore

    return mirror_func

# %% ../../nbs/016_Tester.ipynb 11
def mirror_consumer(topic: str, consumer_f: Callable[..., Any]) -> Callable[..., Any]:
    msg_type = inspect.signature(consumer_f).parameters["msg"]

    async def skeleton_func(msg: BaseModel) -> BaseModel:
        return msg

    mirror_func = skeleton_func
    sig = inspect.signature(skeleton_func)

    # adjust name
    mirror_func.__name__ = "to_" + topic

    # adjust arg and return val
    sig = sig.replace(parameters=[msg_type], return_annotation=msg_type.annotation)

    mirror_func.__signature__ = sig  # type: ignore
    return mirror_func

# %% ../../nbs/016_Tester.ipynb 13
@patch  # type: ignore
def create_mirrors(self: Tester):
    for app in self.apps:
        for topic, (consumer_f, _) in app._consumers_store.items():
            mirror_f = mirror_consumer(topic, consumer_f)
            mirror_f = self.produces()(mirror_f)  # type: ignore
            setattr(self, mirror_f.__name__, mirror_f)
        for topic, (producer_f, _, _) in app._producers_store.items():
            mirror_f = mirror_producer(topic, producer_f)
            mirror_f = self.consumes()(mirror_f)  # type: ignore
            setattr(self, mirror_f.__name__, mirror_f)

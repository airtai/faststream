# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/000_FastKafkaAPI.ipynb.

# %% auto 0
__all__ = ['logger', 'FastKafkaAPI', 'produce_decorator', 'filter_using_signature']

# %% ../nbs/000_FastKafkaAPI.ipynb 1
import asyncio
import functools
import json
import tempfile
import time
from asyncio import iscoroutinefunction  # do not use the version from inspect
from contextlib import asynccontextmanager, contextmanager
from copy import deepcopy
from datetime import datetime, timedelta
from enum import Enum
from inspect import signature
from os import environ
from pathlib import Path
from typing import *
from typing import get_type_hints

import anyio
import asyncer
import confluent_kafka
import httpx
import yaml
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from confluent_kafka import KafkaError, Message, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastcore.foundation import patch
from fastcore.meta import delegates
from pydantic import BaseModel, EmailStr, Field, HttpUrl, PositiveInt
from pydantic.json import timedelta_isoformat
from pydantic.schema import schema

import fast_kafka_api._components.logger

fast_kafka_api._components.logger.should_supress_timestamps = True

import fast_kafka_api
from ._components.aiokafka_consumer_loop import aiokafka_consumer_loop
from ._components.aiokafka_producer_manager import AIOKafkaProducerManager
from fast_kafka_api._components.asyncapi import (
    ConsumeCallable,
    ContactInfo,
    KafkaBroker,
    KafkaBrokers,
    KafkaMessage,
    KafkaServiceInfo,
    ProduceCallable,
    export_async_spec,
)
from ._components.logger import get_logger, supress_timestamps

# %% ../nbs/000_FastKafkaAPI.ipynb 2
logger = get_logger(__name__)

# %% ../nbs/000_FastKafkaAPI.ipynb 9
def _get_fast_api_app(
    fast_api_app: Optional[FastAPI] = None,
    title: str = "FastKafkaAPI",
    description: str = "FastKafkaAPI application handling Kafka consumers and producers",
) -> FastAPI:
    if fast_api_app is None:
        return FastAPI(title=title, description=description)
    else:
        return fast_api_app

# %% ../nbs/000_FastKafkaAPI.ipynb 11
def _get_func_with_combined_sig(
    fx: List[Callable[[Any], Any]], keep: bool = False
) -> Callable[[Any], Any]:
    def _f(**kwargs):
        pass

    retval = _f
    for f in fx:
        retval = delegates(f, keep=True)(retval)
    if not keep:
        retval = delegates(_f, keep=False)(retval)
    return retval  # type: ignore

# %% ../nbs/000_FastKafkaAPI.ipynb 14
@delegates(  # type: ignore
    _get_func_with_combined_sig([AIOKafkaConsumer.__init__, AIOKafkaProducer.__init__])
)
def _get_kafka_config(
    **kwargs,
) -> Dict[str, Any]:
    allowed_keys = set(signature(_get_kafka_config).parameters.keys())
    if not set(kwargs.keys()) <= allowed_keys:
        unallowed_keys = ", ".join(
            sorted([f"'{x}'" for x in set(kwargs.keys()).difference(allowed_keys)])
        )
        raise ValueError(f"Unallowed key arguments passed: {unallowed_keys}")
    retval = kwargs.copy()

    # todo: check this values
    config_defaults = {
        "bootstrap_servers": "localhost:9092",
        "auto_offset_reset": "earliest",
        "max_poll_records": 100,
        #         "max_buffer_size": 10_000,
    }
    for key, value in config_defaults.items():
        if key not in retval:
            retval[key] = value

    return retval

# %% ../nbs/000_FastKafkaAPI.ipynb 17
def _get_kafka_brokers(kafka_brokers: Optional[Dict[str, Any]] = None) -> KafkaBrokers:
    if kafka_brokers is None:
        retval: KafkaBrokers = KafkaBrokers(
            brokers={
                "localhost": KafkaBroker(
                    url="https://localhost",
                    description="Local (dev) Kafka broker",
                    port="9092",
                )
            }
        )
    else:
        retval = KafkaBrokers(
            brokers={
                k: KafkaBroker.parse_raw(
                    v.json() if hasattr(v, "json") else json.dumps(v)
                )
                for k, v in kafka_brokers.items()
            }
        )

    return retval

# %% ../nbs/000_FastKafkaAPI.ipynb 21
def _get_topic_name(
    topic_callable: Union[ConsumeCallable, ProduceCallable], prefix: str = "on_"
) -> str:
    topic = topic_callable.__name__
    if not topic.startswith(prefix) or len(topic) <= len(prefix):
        raise ValueError(f"Function name '{topic}' must start with {prefix}")
    topic = topic[len(prefix) :]

    return topic

# %% ../nbs/000_FastKafkaAPI.ipynb 23
class FastKafkaAPI:
    @delegates(  # type: ignore
        _get_func_with_combined_sig(
            [AIOKafkaConsumer.__init__, AIOKafkaProducer.__init__]
        )
    )
    def __init__(
        self,
        *,
        fast_api_app: Optional[FastAPI] = None,
        title: str = "FastKafkaAPI",
        description: str = "FastKafkaAPI application handling Kafka consumers and producers",
        #         kafka_config: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        contact: Optional[Dict[str, Union[str, Any]]] = None,
        kafka_brokers: Optional[Dict[str, Any]] = None,
        root_path: Optional[Union[Path, str]] = None,
        **kwargs,
    ):
        """Combined REST and Kafka service

        Params:
            fast_api_app: the FastAPI app, if None, one will be created
            title: name of the service, used for generating documentation
            description: description of the service used for generating documentation
            contact:
            kafka_brokers: dictionary describing kafka brokers used for generating documentation
            root_path: path to where documentation will be created
        """
        self._fast_api_app = _get_fast_api_app(fast_api_app, title, description)
        self._title = title
        self._description = description

        if version is None:
            version = "0.0.1"
        self._version = version

        if contact is None:
            contact = dict(
                name="author", url="https://www.google.com", email="noreply@gmail.com"
            )
        self._contact_info = ContactInfo(**contact)

        self._kafka_config = _get_kafka_config(**kwargs)

        if root_path is None:
            root_path = Path(".")
        self._root_path = Path(root_path)

        #         super().__init__(title=title, contact=contact, **kwargs)  # type: ignore

        self._consumers_store: Dict[str, Tuple[ConsumeCallable, Dict[str, Any]]] = {}

        self._producers_list: List[  # type: ignore
            Union[AIOKafkaProducer, AIOKafkaProducerManager]
        ] = []
        self._producers_store: Dict[  # type: ignore
            str, Tuple[ProduceCallable, AIOKafkaProducer, Dict[str, Any]]
        ] = {}
        self._on_error_topic: Optional[str] = None

        #         contact_info = ContactInfo(**contact)
        self._kafka_service_info = KafkaServiceInfo(
            title=self._title,
            version=self._version,
            description=self._description,
            contact=self._contact_info,
        )

        self._kafka_brokers = _get_kafka_brokers(kafka_brokers)

        self._asyncapi_path = self._root_path / "asyncapi"
        (self._asyncapi_path / "docs").mkdir(exist_ok=True, parents=True)
        (self._asyncapi_path / "spec").mkdir(exist_ok=True, parents=True)
        self._fast_api_app.mount(
            "/asyncapi",
            StaticFiles(directory=self._asyncapi_path / "docs"),
            name="asyncapi",
        )

        self._is_shutting_down: bool = False
        self._kafka_consumer_tasks: List[asyncio.Task[Any]] = []
        self._kafka_producer_tasks: List[asyncio.Task[Any]] = []

        @self._fast_api_app.get("/", include_in_schema=False)
        def redirect_root_to_asyncapi():
            return RedirectResponse("/asyncapi")

        @self._fast_api_app.get("/asyncapi", include_in_schema=False)
        async def redirect_asyncapi_docs():
            return RedirectResponse("/asyncapi/index.html")

        @self._fast_api_app.get("/asyncapi.yml", include_in_schema=False)
        async def download_asyncapi_yml():
            return FileResponse(self._asyncapi_path / "spec" / "asyncapi.yml")

        @self._fast_api_app.on_event("startup")
        async def on_startup(app=self):
            await app._on_startup()

        @self._fast_api_app.on_event("shutdown")
        async def on_shutdown(app=self):
            await app._on_shutdown()

    async def _on_startup(self) -> None:
        raise NotImplementedError

    async def _on_shutdown(self) -> None:
        raise NotImplementedError

    def consumes(
        self,
        topic: Optional[str] = None,
        *,
        prefix: str = "on_",
        **kwargs: Dict[str, Any],
    ) -> ConsumeCallable:
        raise NotImplementedError

    def produces(  # type: ignore
        self,
        topic: Optional[str] = None,
        *,
        prefix: str = "to_",
        producer: Optional[AIOKafkaProducer] = None,
        **kwargs: Dict[str, Any],
    ) -> ProduceCallable:
        raise NotImplementedError

    def _populate_consumers(
        self,
        is_shutting_down_f: Callable[[], bool],
    ) -> None:
        raise NotImplementedError

    async def _populate_producers(self) -> None:
        raise NotImplementedError

    def generate_async_spec(self) -> None:
        raise NotImplementedError

    async def _shutdown_consumers(self) -> None:
        raise NotImplementedError

    async def _shutdown_producers(self) -> None:
        raise NotImplementedError

# %% ../nbs/000_FastKafkaAPI.ipynb 26
@patch  # type: ignore
def consumes(
    self: FastKafkaAPI,
    topic: Optional[str] = None,
    *,
    prefix: str = "on_",
    **kwargs: Dict[str, Any],
) -> Callable[[ConsumeCallable], ConsumeCallable]:
    """Decorator registering the callback called when a message is received in a topic.

    This function decorator is also responsible for registering topics for AsyncAPI specificiation and documentation.

    Params:
        topic: Kafka topic that the consumer will subscribe to and execute the decorated function when it receives a message from the topic, default: None
            If the topic is not specified, topic name will be inferred from the decorated function name by stripping the defined prefix
        prefix: Prefix stripped from the decorated function to define a topic name if the topic argument is not passed, default: "on_"
            If the decorated function name is not prefixed with the defined prefix and topic argument is not passed, then this method will throw ValueError
        **kwargs: Keyword arguments that will be passed to AIOKafkaConsumer, used to configure the consumer

    Returns:
        A function returning the same function

    Throws:
        ValueError

    """

    def _decorator(
        on_topic: ConsumeCallable,
        topic: Optional[str] = topic,
        kwargs: Dict[str, Any] = kwargs,
    ) -> ConsumeCallable:
        topic_resolved: str = (
            _get_topic_name(topic_callable=on_topic, prefix=prefix)
            if topic is None
            else topic
        )

        self._consumers_store[topic_resolved] = (on_topic, kwargs)

        return on_topic

    return _decorator

# %% ../nbs/000_FastKafkaAPI.ipynb 28
def _to_json_utf8(o: Any) -> bytes:
    """Converts to JSON and then encodes with UTF-8"""
    if hasattr(o, "json"):
        return o.json().encode("utf-8")  # type: ignore
    else:
        return json.dumps(o).encode("utf-8")

# %% ../nbs/000_FastKafkaAPI.ipynb 30
def produce_decorator(
    self: FastKafkaAPI, func: ProduceCallable, topic: str
) -> ProduceCallable:
    @functools.wraps(func)
    async def _produce_async(*args: List[Any], **kwargs: Dict[str, Any]) -> BaseModel:
        f: Callable[..., Awaitable[BaseModel]] = func  # type: ignore
        return_val = await f(*args, **kwargs)
        _, producer, _ = self._producers_store[topic]
        fut = await producer.send(topic, _to_json_utf8(return_val))
        msg = await fut
        return return_val

    @functools.wraps(func)
    def _produce_sync(*args: List[Any], **kwargs: Dict[str, Any]) -> BaseModel:
        f: Callable[..., BaseModel] = func  # type: ignore
        return_val = f(*args, **kwargs)
        _, producer, _ = self._producers_store[topic]
        producer.send(topic, _to_json_utf8(return_val))
        return return_val

    return _produce_async if iscoroutinefunction(func) else _produce_sync  # type: ignore

# %% ../nbs/000_FastKafkaAPI.ipynb 32
@patch  # type: ignore
def produces(
    self: FastKafkaAPI,
    topic: Optional[str] = None,
    *,
    prefix: str = "to_",
    producer: AIOKafkaProducer = None,
    **kwargs: Dict[str, Any],
) -> Callable[[ProduceCallable], ProduceCallable]:
    """Decorator registering the callback called when delivery report for a produced message is received

    This function decorator is also responsible for registering topics for AsyncAPI specificiation and documentation.

    Params:
        topic: Kafka topic that the producer will send returned values from the decorated function to, default: None
            If the topic is not specified, topic name will be inferred from the decorated function name by stripping the defined prefix
        prefix: Prefix stripped from the decorated function to define a topic name if the topic argument is not passed, default: "to_"
            If the decorated function name is not prefixed with the defined prefix and topic argument is not passed, then this method will throw ValueError
        producer:
        **kwargs: Keyword arguments that will be passed to AIOKafkaProducer, used to configure the producer

    Returns:
        A function returning the same function

    Throws:
        ValueError

    """

    def _decorator(
        on_topic: ProduceCallable,
        topic: Optional[str] = topic,
        kwargs: Dict[str, Any] = kwargs,
    ) -> ProduceCallable:
        topic_resolved: str = (
            _get_topic_name(topic_callable=on_topic, prefix=prefix)
            if topic is None
            else topic
        )

        self._producers_store[topic_resolved] = (on_topic, producer, kwargs)

        return produce_decorator(self, on_topic, topic_resolved)

    return _decorator

# %% ../nbs/000_FastKafkaAPI.ipynb 36
def filter_using_signature(f: Callable, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
    param_names = list(signature(f).parameters.keys())
    return {k: v for k, v in kwargs.items() if k in param_names}

# %% ../nbs/000_FastKafkaAPI.ipynb 38
@patch  # type: ignore
def _populate_consumers(
    self: FastKafkaAPI,
    is_shutting_down_f: Callable[[], bool],
) -> None:
    default_config: Dict[str, Any] = filter_using_signature(
        AIOKafkaConsumer, **self._kafka_config
    )
    self._kafka_consumer_tasks = [
        asyncio.create_task(
            aiokafka_consumer_loop(
                topics=[topic],
                callbacks={topic: consumer},
                msg_types={topic: signature(consumer).parameters["msg"].annotation},
                is_shutting_down_f=is_shutting_down_f,
                **{**default_config, **override_config},
            )
        )
        for topic, (consumer, override_config) in self._consumers_store.items()
    ]


@patch  # type: ignore
async def _shutdown_consumers(
    self: FastKafkaAPI,
) -> None:
    if self._kafka_consumer_tasks:
        await asyncio.wait(self._kafka_consumer_tasks)

# %% ../nbs/000_FastKafkaAPI.ipynb 40
# TODO: Add passing of vars
async def _create_producer(  # type: ignore
    *,
    callback: ProduceCallable,
    producer: Optional[AIOKafkaProducer],
    default_config: Dict[str, Any],
    override_config: Dict[str, Any],
    producers_list: List[Union[AIOKafkaProducer, AIOKafkaProducerManager]],
) -> Union[AIOKafkaProducer, AIOKafkaProducerManager]:
    """Creates a producer

    Args:
        callback: A callback function that is called when the producer is ready.
        producer: An existing producer to use.
        default_config: A dictionary of default configuration values.
        override_config: A dictionary of configuration values to override.
        producers_list: A list of producers to add the new producer to.

    Returns:
        A producer.
    """

    if producer is None:
        config = {
            **filter_using_signature(AIOKafkaProducer, **default_config),
            **override_config,
        }
        producer = AIOKafkaProducer(**config)

    if not iscoroutinefunction(callback):
        producer = AIOKafkaProducerManager(producer)

    await producer.start()

    producers_list.append(producer)

    return producer


@patch  # type: ignore
async def _populate_producers(self: FastKafkaAPI) -> None:
    """Populates the producers for the FastKafkaAPI instance.

    Args:
        self: The FastKafkaAPI instance.

    Returns:
        None.

    Raises:
        None.
    """
    default_config: Dict[str, Any] = self._kafka_config
    self._producers_list = []
    self._producers_store = {
        topic: (
            callback,
            await _create_producer(
                callback=callback,
                producer=producer,
                default_config=default_config,
                override_config=override_config,
                producers_list=self._producers_list,
            ),
            override_config,
        )
        for topic, (
            callback,
            producer,
            override_config,
        ) in self._producers_store.items()
    }


@patch  # type: ignore
async def _shutdown_producers(self: FastKafkaAPI) -> None:
    [await producer.stop() for producer in self._producers_list[::-1]]

# %% ../nbs/000_FastKafkaAPI.ipynb 42
@patch  # type: ignore
def generate_async_spec(self: FastKafkaAPI) -> None:
    export_async_spec(
        consumers={
            topic: callback for topic, (callback, _) in self._consumers_store.items()
        },
        producers={
            topic: callback for topic, (callback, _, _) in self._producers_store.items()
        },
        kafka_brokers=self._kafka_brokers,
        kafka_service_info=self._kafka_service_info,
        asyncapi_path=self._asyncapi_path,
    )

# %% ../nbs/000_FastKafkaAPI.ipynb 44
@patch  # type: ignore
async def _on_startup(self: FastKafkaAPI) -> None:

    self._is_shutting_down = False

    def is_shutting_down_f(self: FastKafkaAPI = self) -> bool:
        return self._is_shutting_down

    self.generate_async_spec()
    await self._populate_producers()
    self._populate_consumers(is_shutting_down_f)


@patch  # type: ignore
async def _on_shutdown(self: FastKafkaAPI) -> None:
    self._is_shutting_down = True

    await self._shutdown_consumers()
    await self._shutdown_producers()

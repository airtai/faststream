# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/013_ProducerDecorator.ipynb.

# %% auto 0
__all__ = ['BaseSubmodel', 'ProduceReturnTypes', 'ProduceCallable', 'KafkaEvent', 'producer_decorator']

# %% ../../nbs/013_ProducerDecorator.ipynb 1
import functools
import json
import asyncio
from asyncio import iscoroutinefunction  # do not use the version from inspect
from collections import namedtuple
from dataclasses import dataclass
from typing import *

import nest_asyncio

from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

# %% ../../nbs/013_ProducerDecorator.ipynb 3
BaseSubmodel = TypeVar("BaseSubmodel", bound=BaseModel)
BaseSubmodel


@dataclass
class KafkaEvent(Generic[BaseSubmodel]):
    """
    A generic class for representing Kafka events. Based on BaseSubmodel, bound to pydantic.BaseModel

    Attributes:
        message (BaseSubmodel): The message contained in the Kafka event, can be of type pydantic.BaseModel.
        key (bytes, optional): The optional key used to identify the Kafka event.
    """

    message: BaseSubmodel
    key: Optional[bytes] = None


KafkaEvent.__module__ = "fastkafka"

# %% ../../nbs/013_ProducerDecorator.ipynb 5
ProduceReturnTypes = Union[BaseModel, KafkaEvent[BaseModel]]

ProduceCallable = Union[
    Callable[..., ProduceReturnTypes], Callable[..., Awaitable[ProduceReturnTypes]]
]

# %% ../../nbs/013_ProducerDecorator.ipynb 6
def _to_json_utf8(o: Any) -> bytes:
    """Converts to JSON and then encodes with UTF-8"""
    if hasattr(o, "json"):
        return o.json().encode("utf-8")  # type: ignore
    else:
        return json.dumps(o).encode("utf-8")

# %% ../../nbs/013_ProducerDecorator.ipynb 8
def _wrap_in_event(message: Union[BaseModel, KafkaEvent]) -> KafkaEvent:
    return message if type(message) == KafkaEvent else KafkaEvent(message)

# %% ../../nbs/013_ProducerDecorator.ipynb 11
def producer_decorator(
    producer_store: Dict[str, Any], func: ProduceCallable, topic: str
) -> ProduceCallable:
    """todo: write documentation"""

    try:
        loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    except RuntimeError as e:
        loop = asyncio.new_event_loop()

    if loop.is_running():
        nest_asyncio.apply(loop)

    def release_callback(fut: asyncio.Future) -> None:
        pass

    @functools.wraps(func)
    async def _produce_async(
        *args: List[Any],
        producer_store: Dict[str, Any] = producer_store,
        f: Callable[..., Awaitable[ProduceReturnTypes]] = func,  # type: ignore
        **kwargs: Any
    ) -> ProduceReturnTypes:
        return_val = await f(*args, **kwargs)
        wrapped_val = _wrap_in_event(return_val)
        _, producer, _ = producer_store[topic]
        fut = await producer.send(
            topic, _to_json_utf8(wrapped_val.message), key=wrapped_val.key
        )
        fut.add_done_callback(release_callback)
        return return_val

    @functools.wraps(func)
    def _produce_sync(
        *args: List[Any],
        producer_store: Dict[str, Any] = producer_store,
        f: Callable[..., ProduceReturnTypes] = func,  # type: ignore
        loop: asyncio.AbstractEventLoop = loop,
        **kwargs: Any
    ) -> ProduceReturnTypes:
        return_val = f(*args, **kwargs)
        wrapped_val = _wrap_in_event(return_val)
        _, producer, _ = producer_store[topic]
        fut = loop.run_until_complete(
            producer.send(
                topic, _to_json_utf8(wrapped_val.message), key=wrapped_val.key
            )
        )
        fut.add_done_callback(release_callback)
        return return_val

    return _produce_async if iscoroutinefunction(func) else _produce_sync

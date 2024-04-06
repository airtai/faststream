"""A Python framework for building services interacting with Apache Kafka, RabbitMQ, NATS and Redis."""

from faststream.annotations import ContextRepo, Logger, NoCast
from faststream.app import FastStream
from faststream.broker.middlewares import BaseMiddleware
from faststream.testing.app import TestApp
from faststream.utils import Context, Depends, Header, Path, apply_types, context

__all__ = (
    # app
    "FastStream",
    "TestApp",
    # utils
    "apply_types",
    "context",
    "Context",
    "Header",
    "Path",
    "Depends",
    # annotations
    "Logger",
    "ContextRepo",
    "NoCast",
    # middlewares
    "BaseMiddleware",
)

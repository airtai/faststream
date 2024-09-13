import logging

from typing_extensions import Annotated

from faststream._internal.context import ContextRepo as CR
from faststream.app import FastStream as FS
from faststream.params import Context
from faststream.params import NoCast as NoCast

Logger = Annotated[logging.Logger, Context("logger")]
ContextRepo = Annotated[CR, Context("context")]
FastStream = Annotated[FS, Context("app")]

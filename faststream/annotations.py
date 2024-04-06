import logging
from typing import TypeVar

from typing_extensions import Annotated

from faststream.app import FastStream as FS
from faststream.utils.context import Context
from faststream.utils.context import ContextRepo as CR
from faststream.utils.no_cast import NoCast as NC

_NoCastType = TypeVar("_NoCastType")

Logger = Annotated[logging.Logger, Context("logger")]
ContextRepo = Annotated[CR, Context("context")]
NoCast = Annotated[_NoCastType, NC()]
FastStream = Annotated[FS, Context("app")]

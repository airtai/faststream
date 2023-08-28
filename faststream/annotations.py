import logging
from typing import TypeVar

from faststream._compat import Annotated
from faststream.utils.context import Context as ContextField
from faststream.utils.context import ContextRepo as CR
from faststream.utils.no_cast import NoCast as NC

_NoCastType = TypeVar("_NoCastType")

Logger = Annotated[logging.Logger, ContextField("logger")]
ContextRepo = Annotated[CR, ContextField("context")]
NoCast = Annotated[_NoCastType, NC()]

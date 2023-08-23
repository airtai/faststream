import logging
from typing import TypeVar

from propan._compat import Annotated
from propan.utils.context import Context as ContextField
from propan.utils.context import ContextRepo as CR
from propan.utils.no_cast import NoCast as NC

_NoCastType = TypeVar("_NoCastType")

Logger = Annotated[logging.Logger, ContextField("logger")]
ContextRepo = Annotated[CR, ContextField("context")]
NoCast = Annotated[_NoCastType, NC()]

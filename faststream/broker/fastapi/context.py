import logging
from typing import Any

from fastapi import params

from faststream._compat import Annotated
from faststream.utils.context import ContextRepo as CR
from faststream.utils.context.main import context


def Context(name: str) -> Any:
    return params.Depends(
        lambda: context.resolve(name),
        use_cache=True,
    )


Logger = Annotated[logging.Logger, Context("logger")]
ContextRepo = Annotated[CR, Context("context")]

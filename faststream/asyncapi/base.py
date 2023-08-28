from abc import abstractproperty
from typing import Dict

from faststream.asyncapi.schema.channels import Channel


class AsyncAPIOperation:
    @abstractproperty
    def name(self) -> str:
        raise NotImplementedError()

    def schema(self) -> Dict[str, Channel]:  # pragma: no cover
        return {}

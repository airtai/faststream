from typing import Optional

from faststream.broker.security import BaseSecurity
from faststream.types import AnyDict


def parse_security(security: Optional[BaseSecurity]) -> AnyDict:
    if security is None:
        return {}
    else:
        raise NotImplementedError(f"RabbitBroker does not support {type(security)}")

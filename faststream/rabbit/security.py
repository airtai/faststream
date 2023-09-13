from typing import Any, Dict, Optional

from faststream.broker.security import BaseSecurity


def parse_security(security: Optional[BaseSecurity]) -> Dict[str, Any]:
    if security is None:
        return {}
    else:
        raise NotImplementedError(f"RabbitBroker does not support {type(security)}")

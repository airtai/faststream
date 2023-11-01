from typing import Optional

from faststream.security import (
    BaseSecurity,
    SASLPlaintext,
)
from faststream.types import AnyDict


def parse_security(security: Optional[BaseSecurity]) -> AnyDict:
    type_ = type(security)
    if security is None:
        return {}
    elif type_ == BaseSecurity:
        return _parse_base_security(security)
    elif type_ == SASLPlaintext:
        return _parse_sasl_plaintext(security)
    else:
        raise NotImplementedError(f"RabbitBroker does not support {type_}")


def _parse_base_security(security: BaseSecurity) -> AnyDict:
    return {
        "ssl": security.use_ssl,
        "ssl_context": security.ssl_context,
    }


def _parse_sasl_plaintext(security: SASLPlaintext) -> AnyDict:
    return {
        "ssl": security.use_ssl,
        "ssl_context": security.ssl_context,
        "login": security.username,
        "password": security.password,
    }

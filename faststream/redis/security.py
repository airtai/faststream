from typing import Optional

from faststream.security import BaseSecurity, SASLPlaintext
from faststream.types import AnyDict


def parse_security(security: Optional[BaseSecurity]) -> AnyDict:
    if security is None:
        return {}
    elif isinstance(security, SASLPlaintext):
        return _parse_sasl_plaintext(security)
    elif isinstance(security, BaseSecurity):
        return _parse_base_security(security)
    else:
        raise NotImplementedError(f"RedisBroker does not support {type(security)}")


def _parse_base_security(security: BaseSecurity) -> AnyDict:
    return {
        "ssl": security.use_ssl,
    }


def _parse_sasl_plaintext(security: SASLPlaintext) -> AnyDict:
    return {
        "ssl": security.use_ssl,
        "username": security.username,
        "password": security.password,
    }


# ssl_keyfile: Optional[str] = None
# ssl_certfile: Optional[str] = None
# ssl_cert_reqs: str = "required"
# ssl_ca_certs: Optional[str] = None
# ssl_ca_data: Optional[str] = None
# ssl_check_hostname: bool = False

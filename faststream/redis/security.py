from typing import TYPE_CHECKING, Any, Optional

from redis.asyncio.connection import Connection

from faststream.security import BaseSecurity, SASLPlaintext

if TYPE_CHECKING:
    from faststream.types import AnyDict


def parse_security(security: Optional[BaseSecurity]) -> "AnyDict":
    if security is None:
        return {}
    elif isinstance(security, SASLPlaintext):
        return _parse_sasl_plaintext(security)
    elif isinstance(security, BaseSecurity):
        return _parse_base_security(security)
    else:
        raise NotImplementedError(f"RedisBroker does not support {type(security)}")


def _parse_base_security(security: BaseSecurity) -> "AnyDict":
    if security.use_ssl:

        class SSLConnection(Connection):
            def __init__(
                self,
                _security: BaseSecurity = security,
                **kwargs: Any,
            ) -> None:
                self._security = _security
                super().__init__(**kwargs)

            def _connection_arguments(self) -> Any:
                return {
                    **super()._connection_arguments(),  # type: ignore[misc]
                    "ssl": self._security.ssl_context,
                }

        return {"connection_class": SSLConnection}
    else:
        return {}


def _parse_sasl_plaintext(security: SASLPlaintext) -> "AnyDict":
    return {
        **_parse_base_security(security),
        "username": security.username,
        "password": security.password,
    }

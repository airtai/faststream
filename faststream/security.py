from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from ssl import SSLContext

    from faststream.types import AnyDict

ssl_not_set_error_msg = """
SSL context is not set; if you don't want to use SSL encryption without sseing this warning, set use_ssl to False.
Warning: This will send your data to the broker unencrypted!
"""


class BaseSecurity:
    """Base class for defining security configurations.

    This class provides a base for defining security configurations for communication with a broker. It allows setting
    SSL encryption and provides methods to retrieve security requirements and schemas.
    """

    ssl_context: Optional["SSLContext"]
    use_ssl: bool

    def __init__(
        self,
        ssl_context: Optional["SSLContext"] = None,
        use_ssl: Optional[bool] = None,
    ) -> None:
        if ssl_context is not None:
            use_ssl = True

        if use_ssl is None:
            use_ssl = False

        self.use_ssl = use_ssl
        self.ssl_context = ssl_context

    def get_requirement(self) -> List["AnyDict"]:
        """Get the security requirements."""
        return []

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """Get the security schema."""
        return {}


class SASLPlaintext(BaseSecurity):
    """Security configuration for SASL/PLAINTEXT authentication.

    This class defines security configuration for SASL/PLAINTEXT authentication, which includes a username and password.
    """

    # TODO: mv to SecretStr
    __slots__ = (
        "use_ssl",
        "ssl_context",
        "username",
        "password",
    )

    def __init__(
        self,
        username: str,
        password: str,
        ssl_context: Optional["SSLContext"] = None,
        use_ssl: Optional[bool] = None,
    ) -> None:
        super().__init__(
            ssl_context=ssl_context,
            use_ssl=use_ssl,
        )

        self.username = username
        self.password = password

    def get_requirement(self) -> List["AnyDict"]:
        """Get the security requirements for SASL/PLAINTEXT authentication."""
        return [{"user-password": []}]

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """Get the security schema for SASL/PLAINTEXT authentication."""
        return {"user-password": {"type": "userPassword"}}


class SASLScram256(BaseSecurity):
    """Security configuration for SASL/SCRAM-SHA-256 authentication.

    This class defines security configuration for SASL/SCRAM-SHA-256 authentication, which includes a username and password.
    """

    # TODO: mv to SecretStr
    __slots__ = (
        "use_ssl",
        "ssl_context",
        "username",
        "password",
    )

    def __init__(
        self,
        username: str,
        password: str,
        ssl_context: Optional["SSLContext"] = None,
        use_ssl: Optional[bool] = None,
    ) -> None:
        super().__init__(
            ssl_context=ssl_context,
            use_ssl=use_ssl,
        )

        self.username = username
        self.password = password

    def get_requirement(self) -> List["AnyDict"]:
        """Get the security requirements for SASL/SCRAM-SHA-256 authentication."""
        return [{"scram256": []}]

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """Get the security schema for SASL/SCRAM-SHA-256 authentication."""
        return {"scram256": {"type": "scramSha256"}}


class SASLScram512(BaseSecurity):
    """Security configuration for SASL/SCRAM-SHA-512 authentication.

    This class defines security configuration for SASL/SCRAM-SHA-512 authentication, which includes a username and password.
    """

    # TODO: mv to SecretStr
    __slots__ = (
        "use_ssl",
        "ssl_context",
        "username",
        "password",
    )

    def __init__(
        self,
        username: str,
        password: str,
        ssl_context: Optional["SSLContext"] = None,
        use_ssl: Optional[bool] = None,
    ) -> None:
        super().__init__(
            ssl_context=ssl_context,
            use_ssl=use_ssl,
        )

        self.username = username
        self.password = password

    def get_requirement(self) -> List["AnyDict"]:
        """Get the security requirements for SASL/SCRAM-SHA-512 authentication."""
        return [{"scram512": []}]

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """Get the security schema for SASL/SCRAM-SHA-512 authentication."""
        return {"scram512": {"type": "scramSha512"}}

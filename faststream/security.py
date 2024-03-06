from ssl import SSLContext
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from faststream._compat import PYDANTIC_V2
from faststream.types import AnyDict

ssl_not_set_error_msg = """
SSL context is not set; if you don't want to use SSL encryption without sseing this warning, set use_ssl to False.
Warning: This will send your data to the broker unencrypted!
"""


class BaseSecurity(BaseModel):
    """Base class for defining security configurations.

    This class provides a base for defining security configurations for communication with a broker. It allows setting
    SSL encryption and provides methods to retrieve security requirements and schemas.

    Args:
        ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. If None, SSL encryption is disabled.
        use_ssl (Optional[bool]): A boolean indicating whether to use SSL encryption. Defaults to True.

    Attributes:
        use_ssl (bool): A boolean indicating whether SSL encryption is enabled.
        ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. None if SSL is not used.

    Methods:
        get_requirement(self) -> List[AnyDict]:
            Get the security requirements in the form of a list of dictionaries.

        get_schema(self) -> Dict[str, Dict[str, str]]:
            Get the security schema as a dictionary.

    """

    ssl_context: Optional[SSLContext]
    use_ssl: bool

    if PYDANTIC_V2:
        model_config = {"arbitrary_types_allowed": True}

    else:
        class Config:
            arbitrary_types_allowed = True

    def __init__(
        self,
        ssl_context: Optional[SSLContext] = None,
        use_ssl: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the security configuration.

        Args:
            ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. If None, SSL encryption is disabled.
            use_ssl (Optional[bool]): A boolean indicating whether to use SSL encryption. Defaults to True.
            **kwargs (Any): inheritance options.
        """
        if ssl_context is not None:
            use_ssl = True

        super().__init__(
            use_ssl=use_ssl or False,
            ssl_context=ssl_context,
            **kwargs,
        )

    def get_requirement(self) -> List[AnyDict]:
        """Get the security requirements.

        Returns:
            List[AnyDict]: A list of dictionaries representing security requirements.
        """
        return []

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """Get the security schema.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary representing the security schema.
        """
        return {}


class SASLPlaintext(BaseSecurity):
    """Security configuration for SASL/PLAINTEXT authentication.

    This class defines security configuration for SASL/PLAINTEXT authentication, which includes a username and password.

    Args:
        username (str): The username for authentication.
        password (str): The password for authentication.
        ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. If None, SSL encryption is disabled.
        use_ssl (Optional[bool]): A boolean indicating whether to use SSL encryption. Defaults to True.

    Methods:
        get_requirement(self) -> List[AnyDict]:
            Get the security requirements for SASL/PLAINTEXT authentication.

        get_schema(self) -> Dict[str, Dict[str, str]]:
            Get the security schema for SASL/PLAINTEXT authentication.

    """

    # TODO: mv to SecretStr
    username: str
    password: str

    def __init__(
        self,
        username: str,
        password: str,
        ssl_context: Optional[SSLContext] = None,
        use_ssl: Optional[bool] = None,
    ) -> None:
        """Initialize the SASL/PLAINTEXT security configuration.

        Args:
            username (str): The username for authentication.
            password (str): The password for authentication.
            ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. If None, SSL encryption is disabled.
            use_ssl (Optional[bool]): A boolean indicating whether to use SSL encryption. Defaults to True.
        """
        super().__init__(
            ssl_context=ssl_context,
            use_ssl=use_ssl,
            username=username,
            password=password,
        )

    def get_requirement(self) -> List[AnyDict]:
        """Get the security requirements for SASL/PLAINTEXT authentication.

        Returns:
            List[AnyDict]: A list of dictionaries representing security requirements.
        """
        return [{"user-password": []}]

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """Get the security schema for SASL/PLAINTEXT authentication.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary representing the security schema.
        """
        return {"user-password": {"type": "userPassword"}}


class SASLScram256(BaseSecurity):
    """Security configuration for SASL/SCRAM-SHA-256 authentication.

    This class defines security configuration for SASL/SCRAM-SHA-256 authentication, which includes a username and password.

    Args:
        username (str): The username for authentication.
        password (str): The password for authentication.
        ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. If None, SSL encryption is disabled.
        use_ssl (Optional[bool]): A boolean indicating whether to use SSL encryption. Defaults to True.

    Methods:
        get_requirement(self) -> List[AnyDict]:
            Get the security requirements for SASL/SCRAM-SHA-256 authentication.

        get_schema(self) -> Dict[str, Dict[str, str]]:
            Get the security schema for SASL/SCRAM-SHA-256 authentication.

    """

    # TODO: mv to SecretStr
    username: str
    password: str

    def __init__(
        self,
        username: str,
        password: str,
        ssl_context: Optional[SSLContext] = None,
        use_ssl: Optional[bool] = None,
    ) -> None:
        """Initialize the SASL/SCRAM-SHA-256 security configuration.

        Args:
            username (str): The username for authentication.
            password (str): The password for authentication.
            ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. If None, SSL encryption is disabled.
            use_ssl (Optional[bool]): A boolean indicating whether to use SSL encryption. Defaults to True.
        """
        super().__init__(
            ssl_context=ssl_context,
            use_ssl=use_ssl,
            username=username,
            password=password,
        )

    def get_requirement(self) -> List[AnyDict]:
        """Get the security requirements for SASL/SCRAM-SHA-256 authentication.

        Returns:
            List[AnyDict]: A list of dictionaries representing security requirements.
        """
        return [{"scram256": []}]

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """Get the security schema for SASL/SCRAM-SHA-256 authentication.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary representing the security schema.
        """
        return {"scram256": {"type": "scramSha256"}}


class SASLScram512(BaseSecurity):
    """Security configuration for SASL/SCRAM-SHA-512 authentication.

    This class defines security configuration for SASL/SCRAM-SHA-512 authentication, which includes a username and password.

    Args:
        username (str): The username for authentication.
        password (str): The password for authentication.
        ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. If None, SSL encryption is disabled.
        use_ssl (Optional[bool]): A boolean indicating whether to use SSL encryption. Defaults to True.

    Methods:
        get_requirement(self) -> List[AnyDict]:
            Get the security requirements for SASL/SCRAM-SHA-512 authentication.

        get_schema(self) -> Dict[str, Dict[str, str]]:
            Get the security schema for SASL/SCRAM-SHA-512 authentication.
    """

    # TODO: mv to SecretStr
    username: str
    password: str

    def __init__(
        self,
        username: str,
        password: str,
        ssl_context: Optional[SSLContext] = None,
        use_ssl: Optional[bool] = None,
    ) -> None:
        """Initialize the SASL/SCRAM-SHA-512 security configuration.

        Args:
            username (str): The username for authentication.
            password (str): The password for authentication.
            ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. If None, SSL encryption is disabled.
            use_ssl (Optional[bool]): A boolean indicating whether to use SSL encryption. Defaults to True.
        """
        super().__init__(
            ssl_context=ssl_context,
            use_ssl=use_ssl,
            username=username,
            password=password,
        )

    def get_requirement(self) -> List[AnyDict]:
        """Get the security requirements for SASL/SCRAM-SHA-512 authentication.

        Returns:
            List[AnyDict]: A list of dictionaries representing security requirements.
        """
        return [{"scram512": []}]

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """Get the security schema for SASL/SCRAM-SHA-512 authentication.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary representing the security schema.
        """
        return {"scram512": {"type": "scramSha512"}}

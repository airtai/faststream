from ssl import SSLContext
from typing import Any, Dict, List, Optional

ssl_not_set_error_msg = """
SSL context is not set; if you don't want to use SSL encryption, set use_ssl to False.
Warning: This will send your data to the broker unencrypted!
"""


class BaseSecurity:
    """
    Base class for defining security configurations.

    This class provides a base for defining security configurations for communication with a broker. It allows setting
    SSL encryption and provides methods to retrieve security requirements and schemas.

    Args:
        ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. If None, SSL encryption is disabled.
        use_ssl (Optional[bool]): A boolean indicating whether to use SSL encryption. Defaults to True.

    Attributes:
        use_ssl (bool): A boolean indicating whether SSL encryption is enabled.
        ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. None if SSL is not used.

    Methods:
        get_requirement(self) -> List[Dict[str, Any]]:
            Get the security requirements in the form of a list of dictionaries.

        get_schema(self) -> Dict[str, Dict[str, str]]:
            Get the security schema as a dictionary.

    """

    def __init__(
        self,
        ssl_context: Optional[SSLContext] = None,
        use_ssl: Optional[bool] = None,
    ):
        if use_ssl is None:
            use_ssl = True

        if use_ssl and ssl_context is None:
            raise RuntimeError(ssl_not_set_error_msg)

        self.use_ssl = use_ssl
        self.ssl_context = ssl_context

    def get_requirement(self) -> List[Dict[str, Any]]:
        """
        Get the security requirements.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing security requirements.
        """
        return []

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the security schema.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary representing the security schema.
        """
        return {}


class SASLPlaintext(BaseSecurity):
    """
    Security configuration for SASL/PLAINTEXT authentication.

    This class defines security configuration for SASL/PLAINTEXT authentication, which includes a username and password.

    Args:
        username (str): The username for authentication.
        password (str): The password for authentication.
        ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. If None, SSL encryption is disabled.
        use_ssl (Optional[bool]): A boolean indicating whether to use SSL encryption. Defaults to True.

    Methods:
        get_requirement(self) -> List[Dict[str, Any]]:
            Get the security requirements for SASL/PLAINTEXT authentication.

        get_schema(self) -> Dict[str, Dict[str, str]]:
            Get the security schema for SASL/PLAINTEXT authentication.

    """

    def __init__(
        self,
        username: str,
        password: str,
        ssl_context: Optional[SSLContext] = None,
        use_ssl: Optional[bool] = None,
    ):
        super().__init__(ssl_context, use_ssl)
        self.username = username
        self.password = password

    def get_requirement(self) -> List[Dict[str, Any]]:
        """
        Get the security requirements for SASL/PLAINTEXT authentication.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing security requirements.
        """
        return [{"user-password": []}]

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the security schema for SASL/PLAINTEXT authentication.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary representing the security schema.
        """
        return {"user-password": {"type": "userPassword"}}


class SASLScram256(BaseSecurity):
    """
    Security configuration for SASL/SCRAM-SHA-256 authentication.

    This class defines security configuration for SASL/SCRAM-SHA-256 authentication, which includes a username and password.

    Args:
        username (str): The username for authentication.
        password (str): The password for authentication.
        ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. If None, SSL encryption is disabled.
        use_ssl (Optional[bool]): A boolean indicating whether to use SSL encryption. Defaults to True.

    Methods:
        get_requirement(self) -> List[Dict[str, Any]]:
            Get the security requirements for SASL/SCRAM-SHA-256 authentication.

        get_schema(self) -> Dict[str, Dict[str, str]]:
            Get the security schema for SASL/SCRAM-SHA-256 authentication.

    """

    def __init__(
        self,
        username: str,
        password: str,
        ssl_context: Optional[SSLContext] = None,
        use_ssl: Optional[bool] = None,
    ):
        super().__init__(ssl_context, use_ssl)
        self.username = username
        self.password = password

    def get_requirement(self) -> List[Dict[str, Any]]:
        """
        Get the security requirements for SASL/SCRAM-SHA-256 authentication.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing security requirements.
        """
        return [{"scram256": []}]

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the security schema for SASL/SCRAM-SHA-256 authentication.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary representing the security schema.
        """
        return {"scram256": {"type": "scramSha256"}}


class SASLScram512(BaseSecurity):
    """
    Security configuration for SASL/SCRAM-SHA-512 authentication.

    This class defines security configuration for SASL/SCRAM-SHA-512 authentication, which includes a username and password.

    Args:
        username (str): The username for authentication.
        password (str): The password for authentication.
        ssl_context (Optional[SSLContext]): An SSLContext object for SSL encryption. If None, SSL encryption is disabled.
        use_ssl (Optional[bool]): A boolean indicating whether to use SSL encryption. Defaults to True.

    Methods:
        get_requirement(self) -> List[Dict[str, Any]]:
            Get the security requirements for SASL/SCRAM-SHA-512 authentication.

        get_schema(self) -> Dict[str, Dict[str, str]]:
            Get the security schema for SASL/SCRAM-SHA-512 authentication.

    """

    def __init__(
        self,
        username: str,
        password: str,
        ssl_context: Optional[SSLContext] = None,
        use_ssl: Optional[bool] = None,
    ):
        super().__init__(ssl_context, use_ssl)
        self.username = username
        self.password = password

    def get_requirement(self) -> List[Dict[str, Any]]:
        """
        Get the security requirements for SASL/SCRAM-SHA-512 authentication.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing security requirements.
        """
        return [{"scram512": []}]

    def get_schema(self) -> Dict[str, Dict[str, str]]:
        """
        Get the security schema for SASL/SCRAM-SHA-512 authentication.

        Returns:
            Dict[str, Dict[str, str]]: A dictionary representing the security schema.
        """
        return {"scram512": {"type": "scramSha512"}}

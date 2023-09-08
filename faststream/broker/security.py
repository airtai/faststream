from ssl import SSLContext
from typing import Optional

ssl_not_set_error_msg = """
SSL context is not set, if you don't want to use SSL encryption, set use_ssl to False.
Warning: This will send your data to the broker unencrypted!
"""


class BaseSecurity:
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


class SASLPlaintext(BaseSecurity):
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

    def get_requirement(self):
        return [{"user-password": []}]

    def get_schema(self):
        return {"user-password": {"type": "userPassword"}}


class SASLScram256(BaseSecurity):
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

    def get_requirement(self):
        return [{"scram256": []}]

    def get_schema(self):
        return {"scram256": {"type": "scramSha256"}}


class SASLScram512(BaseSecurity):
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

    def get_requirement(self):
        return [{"scram512": []}]

    def get_schema(self):
        return {"scram512": {"type": "scramSha512"}}

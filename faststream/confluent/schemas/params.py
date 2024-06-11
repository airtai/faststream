from asyncio import AbstractEventLoop
from typing import List, Literal, Optional, Union

from typing_extensions import TypedDict


class ConsumerConnectionParams(TypedDict, total=False):
    """A class to represent the connection parameters for a consumer."""

    bootstrap_servers: Union[str, List[str]]
    loop: Optional[AbstractEventLoop]
    client_id: str
    retry_backoff_ms: int
    metadata_max_age_ms: int
    security_protocol: Literal[
        "SSL",
        "PLAINTEXT",
    ]
    connections_max_idle_ms: int
    sasl_mechanism: Literal[
        "PLAIN",
        "GSSAPI",
        "SCRAM-SHA-256",
        "SCRAM-SHA-512",
        "OAUTHBEARER",
    ]
    sasl_plain_password: str
    sasl_plain_username: str

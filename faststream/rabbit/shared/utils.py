from typing import Any, Optional, Union

from aio_pika.abc import SSLOptions
from aio_pika.connection import make_url
from pamqp.common import FieldTable
from yarl import URL


def build_url(
    url: Union[str, URL, None] = None,
    *,
    host: Optional[str] = None,
    port: Optional[int] = None,
    login: Optional[str] = None,
    password: Optional[str] = None,
    virtualhost: Optional[str] = None,
    ssl: Optional[bool] = None,
    ssl_options: Optional[SSLOptions] = None,
    client_properties: Optional[FieldTable] = None,
    **kwargs: Any,
) -> URL:
    original_url = make_url(url)

    use_ssl = ssl or original_url.scheme == "amqps"
    default_port = 5671 if use_ssl else 5672

    return make_url(
        host=host or original_url.host or "localhost",
        port=port or original_url.port or default_port,
        login=login or original_url.user or "guest",
        password=password or original_url.password or "guest",
        virtualhost=virtualhost or removeprefix(original_url.path, "/"),
        ssl=use_ssl,
        ssl_options=ssl_options,
        client_properties=client_properties,
        **{
            **kwargs,
            **dict(original_url.query),
        },
    )


def removeprefix(string: str, prefix: str) -> str:
    if string.startswith(prefix):
        return string[len(prefix) :]
    return string

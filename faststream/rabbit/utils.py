from typing import TYPE_CHECKING, Any, Dict, Optional, Union, cast

from aio_pika.connection import make_url

from faststream.rabbit.schemas.constants import ExchangeType

if TYPE_CHECKING:
    import aio_pika
    from aio_pika.abc import SSLOptions
    from pamqp.common import FieldTable
    from yarl import URL

    from faststream.rabbit.schemas import RabbitExchange, RabbitQueue


class RabbitDeclarer:
    """An utility class to declare RabbitMQ queues and exchanges."""

    channel: "aio_pika.RobustChannel"
    queues: Dict["RabbitQueue", "aio_pika.RobustQueue"]
    exchanges: Dict["RabbitExchange", "aio_pika.RobustExchange"]

    def __init__(self, channel: "aio_pika.RobustChannel") -> None:
        self.channel = channel
        self.queues = {}
        self.exchanges = {}

    async def declare_queue(
        self,
        queue: "RabbitQueue",
    ) -> "aio_pika.RobustQueue":
        """Declare a queue."""
        if (q := self.queues.get(queue)) is None:
            self.queues[queue] = q = cast(
                "aio_pika.RobustQueue",
                await self.channel.declare_queue(
                    name=queue.name,
                    durable=queue.durable,
                    exclusive=queue.exclusive,
                    passive=queue.passive,
                    auto_delete=queue.auto_delete,
                    arguments=queue.arguments,
                    timeout=queue.timeout,
                    robust=queue.robust,
                ),
            )
        return q

    async def declare_exchange(
        self,
        exchange: "RabbitExchange",
    ) -> "aio_pika.RobustExchange":
        """Declare an exchange, parent exchanges and bind them each other."""
        if (exch := self.exchanges.get(exchange)) is None:
            self.exchanges[exchange] = exch = cast(
                "aio_pika.RobustExchange",
                await self.channel.declare_exchange(
                    name=exchange.name,
                    type=exchange.type.value,
                    durable=exchange.durable,
                    auto_delete=exchange.auto_delete,
                    passive=exchange.passive,
                    arguments=exchange.arguments,
                    timeout=exchange.timeout,
                    robust=exchange.robust,
                    internal=False,  # deprecated RMQ option
                ),
            )

        if exchange.bind_to is not None:
            parent = await self.declare_exchange(exchange.bind_to)
            await exch.bind(
                exchange=parent,
                routing_key=exchange.routing_key,
                arguments=exchange.bind_arguments,
                timeout=exchange.timeout,
                robust=exchange.robust,
            )

        return exch


def build_url(
    url: Union[str, "URL", None] = None,
    *,
    host: Optional[str] = None,
    port: Optional[int] = None,
    login: Optional[str] = None,
    password: Optional[str] = None,
    virtualhost: Optional[str] = None,
    ssl: Optional[bool] = None,
    ssl_options: Optional["SSLOptions"] = None,
    client_properties: Optional["FieldTable"] = None,
    **kwargs: Any,
) -> "URL":
    """Construct URL object from attributes."""
    original_url = make_url(url)

    use_ssl = ssl or original_url.scheme == "amqps"
    default_port = 5671 if use_ssl else 5672

    return make_url(
        host=host or original_url.host or "localhost",
        port=port or original_url.port or default_port,
        login=login or original_url.user or "guest",
        password=password or original_url.password or "guest",
        virtualhost=virtualhost or original_url.path.lstrip("/"),
        ssl=use_ssl,
        ssl_options=ssl_options,
        client_properties=client_properties,
        **{
            **kwargs,
            **dict(original_url.query),
        },
    )


def is_routing_exchange(exchange: Optional["RabbitExchange"]) -> bool:
    """Check if an exchange requires routing_key to deliver message."""
    return not exchange or exchange.type in (
        ExchangeType.DIRECT.value,
        ExchangeType.TOPIC.value,
    )

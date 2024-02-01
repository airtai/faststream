from typing import TYPE_CHECKING, Any, Dict, Optional, Union, cast

from aio_pika.connection import make_url

from faststream.utils.classes import Singleton

if TYPE_CHECKING:
    import aio_pika
    from aio_pika.abc import SSLOptions
    from pamqp.common import FieldTable
    from yarl import URL

    from faststream.rabbit.schemas.schemas import RabbitExchange, RabbitQueue


class RabbitDeclarer(Singleton):
    """A class to declare RabbitMQ queues and exchanges.

    Attributes:
        channel : aio_pika.RobustChannel
            The RabbitMQ channel to use for declaration.
        queues : Dict[Union[RabbitQueue, str], aio_pika.RobustQueue]
            A dictionary to store the declared queues.
        exchanges : Dict[Union[RabbitExchange, str], aio_pika.RobustExchange]
            A dictionary to store the declared exchanges.

    Methods:
        __init__(channel: aio_pika.RobustChannel) -> None
            Initializes the RabbitDeclarer with a channel.

        declare_queue(queue: RabbitQueue) -> aio_pika.RobustQueue
            Declares a queue and returns the declared queue object.

        declare_exchange(exchange: RabbitExchange) -> aio_pika.RobustExchange
            Declares an exchange and returns the declared exchange object.
    """

    channel: "aio_pika.RobustChannel"
    queues: Dict["RabbitQueue", "aio_pika.RobustQueue"]
    exchanges: Dict["RabbitExchange", "aio_pika.RobustExchange"]

    def __init__(self, channel: "aio_pika.RobustChannel") -> None:
        """Initialize the class.

        Args:
            channel: Aio_pika RobustChannel object

        Attributes:
            channel: Aio_pika RobustChannel object
            queues: A dictionary to store queues
            exchanges: A dictionary to store exchanges
        """
        self.channel = channel
        self.queues = {}
        self.exchanges = {}

    async def declare_queue(
        self,
        queue: "RabbitQueue",
    ) -> "aio_pika.RobustQueue":
        """Declare a queue.

        Args:
            queue: RabbitQueue object representing the queue to be declared.

        Returns:
            aio_pika.RobustQueue: The declared queue.
        """
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
        """Declare an exchange.

        Args:
            exchange: RabbitExchange object representing the exchange to be declared.

        Returns:
            aio_pika.RobustExchange: The declared exchange.
        """
        if (exch := self.exchanges.get(exchange)) is None:
            self.exchanges[exchange] = exch = cast(
                "aio_pika.RobustExchange",
                await self.channel.declare_exchange(
                    name=exchange.name,
                    type=exchange.type,
                    durable=exchange.durable,
                    auto_delete=exchange.auto_delete,
                    internal=exchange.internal,
                    passive=exchange.passive,
                    arguments=exchange.arguments,
                    timeout=exchange.timeout,
                    robust=exchange.robust,
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
    original_url = make_url(url)

    return make_url(
        host=host or original_url.host or "localhost",
        port=port or original_url.port or 5672,
        login=login or original_url.user or "guest",
        password=password or original_url.password or "guest",
        virtualhost=virtualhost or original_url.path.lstrip("/"),
        ssl=ssl or original_url.scheme == "amqps",
        ssl_options=ssl_options,
        client_properties=client_properties,
        **{
            **kwargs,
            **dict(original_url.query),
        },
    )

from faststream._internal.subscriber.specified import (
    SpecificationSubscriber as SpecificationSubscriberMixin,
)
from faststream.rabbit.schemas.proto import BaseRMQInformation as RMQSpecificationMixin
from faststream.rabbit.schemas.subscribers import (
    BaseOptions,
    LogicOptions,
    SpecificationOptions,
)
from faststream.rabbit.subscriber.usecase import LogicSubscriber
from faststream.specification.asyncapi.utils import resolve_payloads
from faststream.specification.schema import (
    AsyncAPIOptions,
    Message,
    Operation,
    SubscriberSpec,
)
from faststream.specification.schema.bindings import (
    ChannelBinding,
    OperationBinding,
    amqp,
)


class SpecificationSubscriber(
    SpecificationSubscriberMixin,
    RMQSpecificationMixin,
    LogicSubscriber,
):
    """AsyncAPI-compatible Rabbit Subscriber class."""

    def __init__(
        self,
        *,
        logic_options: LogicOptions,
        specification_options: SpecificationOptions,
    ) -> None:
        base_options = BaseOptions(
            queue=specification_options.queue, exchange=specification_options.exchange
        )
        async_api_options = AsyncAPIOptions(
            title_=specification_options.title_,
            description_=specification_options.description_,
            include_in_schema=specification_options.include_in_schema,
        )
        super().__init__(
            async_api_options=async_api_options,
            # propagate to RMQSpecificationMixin
            base_init_options=base_options,
        )

        LogicSubscriber.__init__(self, init_options=logic_options)

    def get_default_name(self) -> str:
        return f"{self.queue.name}:{getattr(self.exchange, 'name', None) or '_'}:{self.call_name}"

    def get_schema(self) -> dict[str, SubscriberSpec]:
        payloads = self.get_payloads()

        exchange_binding = amqp.Exchange.from_exchange(self.exchange)
        queue_binding = amqp.Queue.from_queue(self.queue)

        return {
            self.name: SubscriberSpec(
                description=self.description,
                operation=Operation(
                    bindings=OperationBinding(
                        amqp=amqp.OperationBinding(
                            routing_key=self.queue.routing,
                            queue=queue_binding,
                            exchange=exchange_binding,
                            ack=True,
                            reply_to=None,
                            persist=None,
                            mandatory=None,
                            priority=None,
                        ),
                    ),
                    message=Message(
                        title=f"{self.name}:Message",
                        payload=resolve_payloads(payloads),
                    ),
                ),
                bindings=ChannelBinding(
                    amqp=amqp.ChannelBinding(
                        virtual_host=self.virtual_host,
                        queue=queue_binding,
                        exchange=exchange_binding,
                    ),
                ),
            ),
        }

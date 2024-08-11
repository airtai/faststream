from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, List, Union

from faststream import specification as spec
from faststream._compat import DEF_KEY
from faststream.asyncapi.proto import AsyncAPIApplication
from faststream.asyncapi.v2_6_0.schema import (
    Channel,
    Components,
    ExternalDocs,
    Info,
    Operation,
    Reference,
    Schema,
    Server,
    Tag,
    TagDict,
)
from faststream.asyncapi.v2_6_0.schema.bindings import (
    ChannelBinding,
    OperationBinding,
    amqp,
    kafka,
    nats,
    redis,
    sqs,
)
from faststream.asyncapi.v2_6_0.schema.message import CorrelationId, Message
from faststream.constants import ContentTypes

if TYPE_CHECKING:
    from faststream.asyncapi.proto import AsyncAPIApplication
    from faststream.broker.core.usecase import BrokerUsecase
    from faststream.broker.types import ConnectionType, MsgType


def get_app_schema(app: AsyncAPIApplication) -> Schema:
    """Get the application schema."""
    broker = app.broker
    if broker is None:  # pragma: no cover
        raise RuntimeError()
    broker.setup()

    servers = get_broker_server(broker)
    channels = get_broker_channels(broker)

    messages: Dict[str, Message] = {}
    payloads: Dict[str, Dict[str, Any]] = {}
    for channel_name, ch in channels.items():
        ch.servers = list(servers.keys())

        if ch.subscribe is not None:
            m = ch.subscribe.message

            if isinstance(m, Message):  # pragma: no branch
                ch.subscribe.message = _resolve_msg_payloads(
                    m,
                    channel_name,
                    payloads,
                    messages,
                )

        if ch.publish is not None:
            m = ch.publish.message

            if isinstance(m, Message):  # pragma: no branch
                ch.publish.message = _resolve_msg_payloads(
                    m,
                    channel_name,
                    payloads,
                    messages,
                )

    schema = Schema(
        info=Info(
            title=app.title,
            version=app.version,
            description=app.description,
            termsOfService=app.terms_of_service,
            contact=app.contact,
            license=app.license,
        ),
        defaultContentType=ContentTypes.json.value,
        id=app.identifier,
        tags=_specs_tags_to_asyncapi(list(app.asyncapi_tags)) if app.asyncapi_tags else None,
        externalDocs=_specs_external_docs_to_asyncapi(app.external_docs) if app.external_docs else None,
        servers=servers,
        channels=channels,
        components=Components(
            messages=messages,
            schemas=payloads,
            securitySchemes=None
            if broker.security is None
            else broker.security.get_schema(),
        ),
    )
    return schema


def get_broker_server(
        broker: "BrokerUsecase[MsgType, ConnectionType]",
) -> Dict[str, Server]:
    """Get the broker server for an application."""
    servers = {}

    tags: List[Union[Tag, Dict[str, Any]]] = []

    if broker.tags:
        for tag in broker.tags:
            if isinstance(tag, spec.tag.Tag):
                tags.append(Tag(**asdict(tag)))
            elif isinstance(tag, dict):
                tags.append(dict(tag))
            else:
                raise NotImplementedError(f"Unsupported tag type: {tag}; {type(tag)}")

    broker_meta: Dict[str, Any] = {
        "protocol": broker.protocol,
        "protocolVersion": broker.protocol_version,
        "description": broker.description,
        "tags": tags if tags else None,
        # TODO
        # "variables": "",
        # "bindings": "",
    }

    if broker.security is not None:
        broker_meta["security"] = broker.security.get_requirement()

    if isinstance(broker.url, str):
        servers["development"] = Server(
            url=broker.url,
            **broker_meta,
        )

    elif len(broker.url) == 1:
        servers["development"] = Server(
            url=broker.url[0],
            **broker_meta,
        )

    else:
        for i, url in enumerate(broker.url, 1):
            servers[f"Server{i}"] = Server(
                url=url,
                **broker_meta,
            )

    return servers


def get_broker_channels(
        broker: "BrokerUsecase[MsgType, ConnectionType]",
) -> Dict[str, Channel]:
    """Get the broker channels for an application."""
    channels = {}

    for h in broker._subscribers.values():
        schema = h.schema()
        channels.update({
            key: _specs_channel_to_asyncapi(channel)
            for key, channel in schema.items()
        })

    for p in broker._publishers.values():
        schema = p.schema()
        channels.update({
            key: _specs_channel_to_asyncapi(channel)
            for key, channel in schema.items()
        })

    return channels


def _specs_channel_to_asyncapi(channel: spec.channel.Channel) -> Channel:
    return Channel(
        description=channel.description,
        servers=channel.servers,

        bindings=_specs_channel_binding_to_asyncapi(channel.bindings)
        if channel.bindings else None,

        subscribe=_specs_operation_to_asyncapi(channel.subscribe)
        if channel.subscribe else None,

        publish=_specs_operation_to_asyncapi(channel.publish)
        if channel.publish else None,
    )


def _specs_channel_binding_to_asyncapi(binding: spec.bindings.ChannelBinding) -> ChannelBinding:
    return ChannelBinding(
        amqp=amqp.ChannelBinding(**{
            "is": binding.amqp.is_,
            "bindingVersion": binding.amqp.bindingVersion,

            "queue": amqp.Queue(
                name=binding.amqp.queue.name,
                durable=binding.amqp.queue.durable,
                exclusive=binding.amqp.queue.exclusive,
                autoDelete=binding.amqp.queue.autoDelete,
                vhost=binding.amqp.queue.vhost,
            )
            if binding.amqp.queue else None,

            "exchange": amqp.Exchange(
                name=binding.amqp.exchange.name,
                type=binding.amqp.exchange.type,
                durable=binding.amqp.exchange.durable,
                autoDelete=binding.amqp.exchange.autoDelete,
                vhost=binding.amqp.exchange.vhost
            )
            if binding.amqp.exchange else None,
        }
    )
        if binding.amqp else None,

        kafka=kafka.ChannelBinding(**asdict(binding.kafka))
        if binding.kafka else None,

        sqs=sqs.ChannelBinding(**asdict(binding.sqs))
        if binding.sqs else None,

        nats=nats.ChannelBinding(**asdict(binding.nats))
        if binding.nats else None,

        redis=redis.ChannelBinding(**asdict(binding.redis))
        if binding.redis else None,
    )


def _specs_operation_to_asyncapi(operation: spec.operation.Operation) -> Operation:
    return Operation(
        operationId=operation.operationId,
        summary=operation.summary,
        description=operation.description,

        bindings=_specs_operation_binding_to_asyncapi(operation.bindings)
        if operation.bindings else None,

        message=Message(
            title=operation.message.title,
            name=operation.message.name,
            summary=operation.message.summary,
            description=operation.message.description,
            messageId=operation.message.messageId,
            payload=operation.message.payload,

            correlationId=CorrelationId(**asdict(operation.message.correlationId))
            if operation.message.correlationId else None,

            contentType=operation.message.contentType,

            tags=_specs_tags_to_asyncapi(operation.tags)
            if operation.tags else None,

            externalDocs=_specs_external_docs_to_asyncapi(operation.externalDocs)
            if operation.externalDocs else None,
        ),

        security=operation.security,

        tags=_specs_tags_to_asyncapi(operation.tags)
        if operation.tags else None,

        externalDocs=_specs_external_docs_to_asyncapi(operation.externalDocs)
        if operation.externalDocs else None,
    )


def _specs_operation_binding_to_asyncapi(binding: spec.bindings.OperationBinding) -> OperationBinding:
    return OperationBinding(
        amqp=amqp.OperationBinding(**asdict(binding.amqp))
        if binding.amqp else None,

        kafka=kafka.OperationBinding(**asdict(binding.kafka))
        if binding.kafka else None,

        sqs=kafka.OperationBinding(**asdict(binding.sqs))
        if binding.sqs else None,

        nats=kafka.OperationBinding(**asdict(binding.nats))
        if binding.nats else None,

        redis=kafka.OperationBinding(**asdict(binding.redis))
        if binding.redis else None,
    )


def _specs_tags_to_asyncapi(
        tags: List[Union[spec.tag.Tag, spec.tag.TagDict, Dict[str, Any]]]
) -> List[Union[Tag, TagDict, Dict[str, Any]]]:
    asyncapi_tags: List[Union[Tag, TagDict, Dict[str, Any]]] = []

    for tag in tags:
        if isinstance(tag, spec.tag.Tag):
            asyncapi_tags.append(Tag(
                name=tag.name,
                description=tag.description,

                externalDocs=_specs_external_docs_to_asyncapi(tag.externalDocs)
                if tag.externalDocs else None,
            ))
        elif isinstance(tag, dict):
            asyncapi_tags.append(dict(tag))
        else:
            raise NotImplementedError

    return asyncapi_tags


def _specs_external_docs_to_asyncapi(
        externalDocs: Union[spec.docs.ExternalDocs, spec.docs.ExternalDocsDict, Dict[str, Any]]
) -> Union[ExternalDocs, Dict[str, Any]]:
    if isinstance(externalDocs, spec.docs.ExternalDocs):
        return ExternalDocs(
            **asdict(externalDocs)
        )
    else:
        return dict(externalDocs)


def _resolve_msg_payloads(
        m: Message,
        channel_name: str,
        payloads: Dict[str, Any],
        messages: Dict[str, Any],
) -> Reference:
    """Replace message payload by reference and normalize payloads.

    Payloads and messages are editable dicts to store schemas for reference in AsyncAPI.
    """
    one_of_list: List[Reference] = []
    m.payload = _move_pydantic_refs(m.payload, DEF_KEY)

    if DEF_KEY in m.payload:
        payloads.update(m.payload.pop(DEF_KEY))

    one_of = m.payload.get("oneOf")
    if isinstance(one_of, dict):
        for p_title, p in one_of.items():
            payloads.update(p.pop(DEF_KEY, {}))
            if p_title not in payloads:
                payloads[p_title] = p
            one_of_list.append(Reference(**{"$ref": f"#/components/schemas/{p_title}"}))

    elif one_of is not None:
        for p in one_of:
            p_title = next(iter(p.values())).split("/")[-1]
            if p_title not in payloads:
                payloads[p_title] = p
            one_of_list.append(Reference(**{"$ref": f"#/components/schemas/{p_title}"}))

    if not one_of_list:
        payloads.update(m.payload.pop(DEF_KEY, {}))
        p_title = m.payload.get("title", f"{channel_name}Payload")
        if p_title not in payloads:
            payloads[p_title] = m.payload
        m.payload = {"$ref": f"#/components/schemas/{p_title}"}

    else:
        m.payload["oneOf"] = one_of_list

    assert m.title  # nosec B101
    messages[m.title] = m
    return Reference(**{"$ref": f"#/components/messages/{m.title}"})


def _move_pydantic_refs(
        original: Any,
        key: str,
) -> Any:
    """Remove pydantic references and replacem them by real schemas."""
    if not isinstance(original, Dict):
        return original

    data = original.copy()

    for k in data:
        item = data[k]

        if isinstance(item, str):
            if key in item:
                data[k] = data[k].replace(key, "components/schemas")

        elif isinstance(item, dict):
            data[k] = _move_pydantic_refs(data[k], key)

        elif isinstance(item, List):
            for i in range(len(data[k])):
                data[k][i] = _move_pydantic_refs(item[i], key)

    if isinstance(discriminator := data.get("discriminator"), dict):
        data["discriminator"] = discriminator["propertyName"]

    return data

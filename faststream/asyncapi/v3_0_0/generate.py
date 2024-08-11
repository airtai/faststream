from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, List, Union
from urllib.parse import urlparse

from faststream import specification as spec
from faststream._compat import DEF_KEY
from faststream.asyncapi.proto import AsyncAPIApplication
from faststream.asyncapi.v2_6_0.generate import (
    _specs_channel_binding_to_asyncapi,
    _specs_contact_to_asyncapi,
    _specs_license_to_asyncapi,
    _specs_operation_binding_to_asyncapi,
    _specs_tags_to_asyncapi,
)
from faststream.asyncapi.v2_6_0.schema import (
    ExternalDocs,
    ExternalDocsDict,
    Reference,
    Tag,
)
from faststream.asyncapi.v2_6_0.schema.message import CorrelationId, Message
from faststream.asyncapi.v3_0_0.schema import (
    Channel,
    Components,
    Info,
    Operation,
    Schema,
    Server,
)
from faststream.constants import ContentTypes

if TYPE_CHECKING:
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
    operations = get_broker_operations(broker)

    messages: Dict[str, Message] = {}
    payloads: Dict[str, Dict[str, Any]] = {}

    for channel_name, channel in channels.items():
        msgs: Dict[str, Union[Message, Reference]] = {}
        for message_name, message in channel.messages.items():
            assert isinstance(message, Message)

            msgs[message_name] = _resolve_msg_payloads(
                message_name,
                message,
                channel_name,
                payloads,
                messages
            )

        channel.messages = msgs

        channel.servers = [{"$ref": f"#/servers/{server_name}"} for server_name in list(servers.keys())]

    schema = Schema(
        info=Info(
            title=app.title,
            version=app.version,
            description=app.description,
            termsOfService=app.terms_of_service,
            contact=_specs_contact_to_asyncapi(app.contact)
            if app.contact else None,
            license=_specs_license_to_asyncapi(app.license)
            if app.license else None,
            tags=_specs_tags_to_asyncapi(list(app.asyncapi_tags)) if app.asyncapi_tags else None,
            externalDocs=_specs_external_docs_to_asyncapi(app.external_docs) if app.external_docs else None,
        ),
        defaultContentType=ContentTypes.json.value,
        id=app.identifier,
        servers=servers,
        channels=channels,
        operations=operations,
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
        broker_url = broker.url
        if "://" not in broker_url:
            broker_url = "//" + broker_url

        url = urlparse(broker_url)
        servers["development"] = Server(
            host=url.netloc,
            pathname=url.path,
            **broker_meta,
        )

    elif len(broker.url) == 1:
        broker_url = broker.url[0]
        if "://" not in broker_url:
            broker_url = "//" + broker_url

        url = urlparse(broker_url)
        servers["development"] = Server(
            host=url.netloc,
            pathname=url.path,
            **broker_meta,
        )

    else:
        for i, broker_url in enumerate(broker.url, 1):
            if "://" not in broker_url:
                broker_url = "//" + broker_url

            parsed_url = urlparse(broker_url)
            servers[f"Server{i}"] = Server(
                host=parsed_url.netloc,
                pathname=parsed_url.path,
                **broker_meta,
            )

    return servers


def get_broker_operations(
        broker: "BrokerUsecase[MsgType, ConnectionType]",
) -> Dict[str, Operation]:
    """Get the broker operations for an application."""
    operations = {}

    for h in broker._subscribers.values():
        for channel_name, specs_channel in h.schema().items():
            if specs_channel.subscribe is not None:
                op = Operation(
                    action="receive",
                    summary=specs_channel.subscribe.summary,
                    description=specs_channel.subscribe.description,
                    bindings=_specs_operation_binding_to_asyncapi(specs_channel.subscribe.bindings)
                    if specs_channel.subscribe.bindings else None,
                    messages=[
                        Reference(
                            **{"$ref": f"#/channels/{channel_name}/messages/SubscribeMessage"},
                        )
                    ],
                    channel=Reference(
                        **{"$ref": f"#/channels/{channel_name}"},
                    ),
                    security=specs_channel.subscribe.security,
                )
                operations[f"{channel_name}Subscribe"] = op

    for p in broker._publishers.values():
        for channel_name, specs_channel in p.schema().items():
            if specs_channel.publish is not None:
                op = Operation(
                    action="send",
                    summary=specs_channel.publish.summary,
                    description=specs_channel.publish.description,
                    bindings=_specs_operation_binding_to_asyncapi(specs_channel.publish.bindings)
                    if specs_channel.publish.bindings else None,
                    messages=[
                        Reference(
                            **{"$ref": f"#/channels/{channel_name}/messages/Message"},
                        )
                    ],
                    channel=Reference(
                        **{"$ref": f"#/channels/{channel_name}"},
                    ),
                    security=specs_channel.publish.security,
                )
                operations[f"{channel_name}"] = op

    return operations


def get_broker_channels(
        broker: "BrokerUsecase[MsgType, ConnectionType]",
) -> Dict[str, Channel]:
    """Get the broker channels for an application."""
    channels = {}

    for h in broker._subscribers.values():
        channels_schema_v3_0 = {}
        for channel_name, specs_channel in h.schema().items():
            if specs_channel.subscribe:
                channel_v3_0 = Channel(
                    address=channel_name,
                    messages={
                        "SubscribeMessage": Message(
                            title=specs_channel.subscribe.message.title,
                            name=specs_channel.subscribe.message.name,
                            summary=specs_channel.subscribe.message.summary,
                            description=specs_channel.subscribe.message.description,
                            messageId=specs_channel.subscribe.message.messageId,
                            payload=specs_channel.subscribe.message.payload,

                            correlationId=CorrelationId(**asdict(specs_channel.subscribe.message.correlationId))
                            if specs_channel.subscribe.message.correlationId else None,

                            contentType=specs_channel.subscribe.message.contentType,

                            tags=_specs_tags_to_asyncapi(specs_channel.subscribe.message.tags)  # type: ignore
                            if specs_channel.subscribe.message.tags else None,

                            externalDocs=_specs_external_docs_to_asyncapi(specs_channel.subscribe.message.externalDocs)
                            if specs_channel.subscribe.message.externalDocs else None,
                        ),
                    },
                    description=specs_channel.description,
                    servers=specs_channel.servers,
                    bindings=_specs_channel_binding_to_asyncapi(specs_channel.bindings)
                    if specs_channel.bindings else None,
                )

                channels_schema_v3_0[channel_name] = channel_v3_0

        channels.update(channels_schema_v3_0)

    for p in broker._publishers.values():
        channels_schema_v3_0 = {}
        for channel_name, specs_channel in p.schema().items():
            if specs_channel.publish:
                channel_v3_0 = Channel(
                    address=channel_name,
                    messages={
                        "Message": Message(
                            title=specs_channel.publish.message.title,
                            name=specs_channel.publish.message.name,
                            summary=specs_channel.publish.message.summary,
                            description=specs_channel.publish.message.description,
                            messageId=specs_channel.publish.message.messageId,
                            payload=specs_channel.publish.message.payload,

                            correlationId=CorrelationId(**asdict(specs_channel.publish.message.correlationId))
                            if specs_channel.publish.message.correlationId else None,

                            contentType=specs_channel.publish.message.contentType,

                            tags=_specs_tags_to_asyncapi(specs_channel.publish.message.tags)  # type: ignore
                            if specs_channel.publish.message.tags else None,

                            externalDocs=_specs_external_docs_to_asyncapi(specs_channel.publish.message.externalDocs)
                            if specs_channel.publish.message.externalDocs else None,
                        ),
                    },
                    description=specs_channel.description,
                    servers=specs_channel.servers,
                    bindings=_specs_channel_binding_to_asyncapi(specs_channel.bindings)
                    if specs_channel.bindings else None,
                )

                channels_schema_v3_0[channel_name] = channel_v3_0

        channels.update(channels_schema_v3_0)

    return channels


def _specs_external_docs_to_asyncapi(
        externalDocs: Union[spec.docs.ExternalDocs, spec.docs.ExternalDocsDict, Dict[str, Any]]
) -> Union[ExternalDocs, ExternalDocsDict, Dict[str, Any]]:
    if isinstance(externalDocs, spec.docs.ExternalDocs):
        return ExternalDocs(
            **asdict(externalDocs)
        )
    else:
        return dict(externalDocs)


def _resolve_msg_payloads(
        message_name: str,
        m: Message,
        channel_name: str,
        payloads: Dict[str, Any],
        messages: Dict[str, Any],
) -> Reference:
    assert isinstance(m.payload, dict)

    m.payload = _move_pydantic_refs(m.payload, DEF_KEY)

    if DEF_KEY in m.payload:
        payloads.update(m.payload.pop(DEF_KEY))

    one_of = m.payload.get("oneOf", None)
    if isinstance(one_of, dict):
        one_of_list = []
        processed_payloads: Dict[str, Dict[str, Any]] = {}
        for name, payload in one_of.items():
            processed_payloads[name] = payload
            one_of_list.append(Reference(**{"$ref": f"#/components/schemas/{name}"}))

        payloads.update(processed_payloads)
        m.payload["oneOf"] = one_of_list
        assert m.title
        messages[m.title] = m
        return Reference(**{"$ref": f"#/components/messages/{channel_name}:{message_name}"})

    else:
        payloads.update(m.payload.pop(DEF_KEY, {}))
        payload_name = m.payload.get("title", f"{channel_name}:{message_name}:Payload")
        payloads[payload_name] = m.payload
        m.payload = {"$ref": f"#/components/schemas/{payload_name}"}
        assert m.title
        messages[m.title] = m
        return Reference(**{"$ref": f"#/components/messages/{channel_name}:{message_name}"})


def _move_pydantic_refs(
        original: Any,
        key: str,
) -> Any:
    """Remove pydantic references and replace them by real schemas."""
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
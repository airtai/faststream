from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, List, Union
from urllib.parse import urlparse

from faststream._compat import DEF_KEY
from faststream.constants import ContentTypes
from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.generate import (
    specs_contact_to_asyncapi,
)
from faststream.specification.asyncapi.v2_6_0.schema import (
    ExternalDocs,
    Reference,
    Tag,
)
from faststream.specification.asyncapi.v2_6_0.schema.bindings import (
    ChannelBinding,
    OperationBinding,
)
from faststream.specification.asyncapi.v2_6_0.schema.license import (
    from_spec as license_from_spec,
)
from faststream.specification.asyncapi.v2_6_0.schema.message import (
    Message,
)
from faststream.specification.asyncapi.v2_6_0.schema.message import (
    from_spec as message_from_spec,
)
from faststream.specification.asyncapi.v2_6_0.schema.tag import (
    from_spec as tag_from_spec,
)
from faststream.specification.asyncapi.v3_0_0.schema import (
    Channel,
    Components,
    Info,
    Operation,
    Schema,
    Server,
)
from faststream.specification.proto import Application
from faststream.types import AnyDict

if TYPE_CHECKING:
    from faststream.broker.core.usecase import BrokerUsecase
    from faststream.broker.types import ConnectionType, MsgType


def get_app_schema(app: Application) -> Schema:
    """Get the application schema."""
    broker = app.broker
    if broker is None:  # pragma: no cover
        raise RuntimeError()
    broker.setup()

    servers = get_broker_server(broker)
    channels = get_broker_channels(broker)
    operations = get_broker_operations(broker)

    messages: Dict[str, Message] = {}
    payloads: Dict[str, AnyDict] = {}

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

            contact=specs_contact_to_asyncapi(app.contact)
            if app.contact else None,

            license=license_from_spec(app.license)
            if app.license else None,

            tags=[tag_from_spec(tag) for tag in app.specs_tags]
            if app.specs_tags else None,

            externalDocs=specs_external_docs_to_asyncapi(app.external_docs)
            if app.external_docs else None,
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

    tags: List[Union[Tag, AnyDict]] = []
    if broker.tags:

        for tag in broker.tags:
            if isinstance(tag, spec.tag.Tag):
                tags.append(Tag(**asdict(tag)))
            elif isinstance(tag, dict):
                tags.append(dict(tag))
            else:
                raise NotImplementedError(f"Unsupported tag type: {tag}; {type(tag)}")

    broker_meta: AnyDict = {
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
                    bindings=OperationBinding.from_spec(specs_channel.subscribe.bindings)
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
                    bindings=OperationBinding.from_spec(specs_channel.publish.bindings)
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
                        "SubscribeMessage": message_from_spec(specs_channel.subscribe.message),
                    },
                    description=specs_channel.description,
                    servers=specs_channel.servers,
                    bindings=ChannelBinding.from_spec(specs_channel.bindings)
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
                        "Message": message_from_spec(specs_channel.publish.message),
                    },
                    description=specs_channel.description,
                    servers=specs_channel.servers,
                    bindings=ChannelBinding.from_spec(specs_channel.bindings)
                    if specs_channel.bindings else None,
                )

                channels_schema_v3_0[channel_name] = channel_v3_0

        channels.update(channels_schema_v3_0)

    return channels


def specs_external_docs_to_asyncapi(
        externalDocs: Union[spec.docs.ExternalDocs, spec.docs.ExternalDocsDict, AnyDict]
) -> Union[ExternalDocs, AnyDict]:
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
        payloads: AnyDict,
        messages: AnyDict,
) -> Reference:
    assert isinstance(m.payload, dict)

    m.payload = _move_pydantic_refs(m.payload, DEF_KEY)

    if DEF_KEY in m.payload:
        payloads.update(m.payload.pop(DEF_KEY))

    one_of = m.payload.get("oneOf", None)
    if isinstance(one_of, dict):
        one_of_list = []
        processed_payloads: Dict[str, AnyDict] = {}
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

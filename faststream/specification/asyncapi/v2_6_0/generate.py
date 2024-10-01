from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Union

from faststream._internal._compat import DEF_KEY
from faststream._internal.basic_types import AnyDict, AnyHttpUrl
from faststream._internal.constants import ContentTypes
from faststream.specification.asyncapi.utils import clear_key
from faststream.specification.asyncapi.v2_6_0.schema import (
    Channel,
    Components,
    Info,
    Reference,
    Schema,
    Server,
    Tag,
    channel_from_spec,
    contact_from_spec,
    docs_from_spec,
    license_from_spec,
    tag_from_spec,
)
from faststream.specification.asyncapi.v2_6_0.schema.message import Message

if TYPE_CHECKING:
    from faststream._internal.broker.broker import BrokerUsecase
    from faststream._internal.types import ConnectionType, MsgType
    from faststream.specification.schema.contact import Contact, ContactDict
    from faststream.specification.schema.docs import ExternalDocs, ExternalDocsDict
    from faststream.specification.schema.license import License, LicenseDict
    from faststream.specification.schema.tag import (
        Tag as SpecsTag,
    )
    from faststream.specification.schema.tag import (
        TagDict as SpecsTagDict,
    )


def get_app_schema(
        broker: "BrokerUsecase[Any, Any]",
        /,
        title: str,
        app_version: str,
        schema_version: str,
        description: str,
        terms_of_service: Optional["AnyHttpUrl"],
        contact: Optional[Union["Contact", "ContactDict", "AnyDict"]],
        license: Optional[Union["License", "LicenseDict", "AnyDict"]],
        identifier: Optional[str],
        tags: Optional[Sequence[Union["SpecsTag", "SpecsTagDict", "AnyDict"]]],
        external_docs: Optional[Union["ExternalDocs", "ExternalDocsDict", "AnyDict"]],
) -> Schema:
    """Get the application schema."""
    broker._setup()

    servers = get_broker_server(broker)
    channels = get_broker_channels(broker)

    messages: Dict[str, Message] = {}
    payloads: Dict[str, AnyDict] = {}

    for channel in channels.values():
        channel.servers = list(servers.keys())

    for channel_name, ch in channels.items():
        resolve_channel_messages(ch, channel_name, payloads, messages)

    schema = Schema(
        info=Info(
            title=title,
            version=app_version,
            description=description,
            termsOfService=terms_of_service,
            contact=contact_from_spec(contact) if contact else None,
            license=license_from_spec(license) if license else None,
        ),
        asyncapi=schema_version,
        defaultContentType=ContentTypes.json.value,
        id=identifier,
        tags=[tag_from_spec(tag) for tag in tags] if tags else None,
        externalDocs=docs_from_spec(external_docs) if external_docs else None,
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


def resolve_channel_messages(
    channel: Channel,
    channel_name: str,
    payloads: Dict[str, AnyDict],
    messages: Dict[str, Message],
) -> None:
    if channel.subscribe is not None:
        assert isinstance(channel.subscribe.message, Message)

        channel.subscribe.message = _resolve_msg_payloads(
            channel.subscribe.message,
            channel_name,
            payloads,
            messages,
        )

    if channel.publish is not None:
        assert isinstance(channel.publish.message, Message)

        channel.publish.message = _resolve_msg_payloads(
            channel.publish.message,
            channel_name,
            payloads,
            messages,
        )


def get_broker_server(
    broker: "BrokerUsecase[MsgType, ConnectionType]",
) -> Dict[str, Server]:
    """Get the broker server for an application."""
    servers = {}

    tags: Optional[List[Union[Tag, AnyDict]]] = None
    if broker.tags:
        tags = [tag_from_spec(tag) for tag in broker.tags]

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

    urls = broker.url if isinstance(broker.url, list) else [broker.url]

    for i, url in enumerate(urls, 1):
        server_name = "development" if len(urls) == 1 else f"Server{i}"
        servers[server_name] = Server(
            url=url,
            **broker_meta,
        )

    return servers


def get_broker_channels(
    broker: "BrokerUsecase[MsgType, ConnectionType]",
) -> Dict[str, Channel]:
    """Get the broker channels for an application."""
    channels = {}

    for h in broker._subscribers:
        schema = h.schema()
        channels.update(
            {key: channel_from_spec(channel) for key, channel in schema.items()}
        )

    for p in broker._publishers:
        schema = p.schema()
        channels.update(
            {key: channel_from_spec(channel) for key, channel in schema.items()}
        )

    return channels


def _resolve_msg_payloads(
    m: Message,
    channel_name: str,
    payloads: AnyDict,
    messages: AnyDict,
) -> Reference:
    """Replace message payload by reference and normalize payloads.

    Payloads and messages are editable dicts to store schemas for reference in AsyncAPI.
    """
    one_of_list: List[Reference] = []
    m.payload = move_pydantic_refs(m.payload, DEF_KEY)

    if DEF_KEY in m.payload:
        payloads.update(m.payload.pop(DEF_KEY))

    one_of = m.payload.get("oneOf")
    if isinstance(one_of, dict):
        for p_title, p in one_of.items():
            p_title = clear_key(p_title)
            payloads.update(p.pop(DEF_KEY, {}))
            if p_title not in payloads:
                payloads[p_title] = p
            one_of_list.append(Reference(**{"$ref": f"#/components/schemas/{p_title}"}))

    elif one_of is not None:
        # Descriminator case
        for p in one_of:
            p_value = next(iter(p.values()))
            p_title = p_value.split("/")[-1]
            p_title = clear_key(p_title)
            if p_title not in payloads:
                payloads[p_title] = p
            one_of_list.append(Reference(**{"$ref": f"#/components/schemas/{p_title}"}))

    if not one_of_list:
        payloads.update(m.payload.pop(DEF_KEY, {}))
        p_title = m.payload.get("title", f"{channel_name}Payload")
        p_title = clear_key(p_title)
        if p_title not in payloads:
            payloads[p_title] = m.payload
        m.payload = {"$ref": f"#/components/schemas/{p_title}"}

    else:
        m.payload["oneOf"] = one_of_list

    assert m.title  # nosec B101
    message_title = clear_key(m.title)
    messages[message_title] = m
    return Reference(**{"$ref": f"#/components/messages/{message_title}"})


def move_pydantic_refs(
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
            data[k] = move_pydantic_refs(data[k], key)

        elif isinstance(item, List):
            for i in range(len(data[k])):
                data[k][i] = move_pydantic_refs(item[i], key)

    if isinstance(discriminator := data.get("discriminator"), dict):
        data["discriminator"] = discriminator["propertyName"]

    return data

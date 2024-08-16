from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, List, Union

from faststream._compat import DEF_KEY
from faststream.constants import ContentTypes
from faststream.specification import schema as spec
from faststream.specification.asyncapi.v2_6_0.schema import (
    Channel,
    Components,
    Info,
    Operation,
    Reference,
    Schema,
    Server,
    Tag,
)
from faststream.specification.asyncapi.v2_6_0.schema.bindings import (
    ChannelBinding,
    OperationBinding,
)
from faststream.specification.asyncapi.v2_6_0.schema.contact import (
    from_spec as contact_from_spec,
)
from faststream.specification.asyncapi.v2_6_0.schema.docs import (
    from_spec as docs_from_spec,
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

    messages: Dict[str, Message] = {}
    payloads: Dict[str, AnyDict] = {}
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
            contact=contact_from_spec(app.contact)
            if app.contact else None,
            license=license_from_spec(app.license)
            if app.license else None,
        ),
        defaultContentType=ContentTypes.json.value,
        id=app.identifier,

        tags=[tag_from_spec(tag) for tag in app.specs_tags]
        if app.specs_tags else None,

        externalDocs=docs_from_spec(app.external_docs)
        if app.external_docs else None,

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
            key: specs_channel_to_asyncapi(channel)
            for key, channel in schema.items()
        })

    for p in broker._publishers.values():
        schema = p.schema()
        channels.update({
            key: specs_channel_to_asyncapi(channel)
            for key, channel in schema.items()
        })

    return channels



def specs_channel_to_asyncapi(channel: spec.channel.Channel) -> Channel:
    return Channel(
        description=channel.description,
        servers=channel.servers,

        bindings=ChannelBinding.from_spec(channel.bindings)
        if channel.bindings else None,

        subscribe=specs_operation_to_asyncapi(channel.subscribe)
        if channel.subscribe else None,

        publish=specs_operation_to_asyncapi(channel.publish)
        if channel.publish else None,
    )


def specs_operation_to_asyncapi(operation: spec.operation.Operation) -> Operation:
    return Operation(
        operationId=operation.operationId,
        summary=operation.summary,
        description=operation.description,

        bindings=OperationBinding.from_spec(operation.bindings)
        if operation.bindings else None,

        message=message_from_spec(operation.message),
        security=operation.security,

        tags=[tag_from_spec(tag) for tag in operation.tags]
        if operation.tags else None,
    )


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

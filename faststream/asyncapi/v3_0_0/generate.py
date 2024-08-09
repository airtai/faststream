from typing import TYPE_CHECKING, Any, Dict, List, Union
from urllib.parse import urlparse

from faststream._compat import DEF_KEY, HAS_FASTAPI
from faststream.asyncapi.v2_6_0.schema import Reference
from faststream.asyncapi.v2_6_0.schema.message import Message
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
    from faststream.app import FastStream
    from faststream.broker.core.usecase import BrokerUsecase
    from faststream.broker.types import ConnectionType, MsgType

    if HAS_FASTAPI:
        from faststream.broker.fastapi.router import StreamRouter


def get_app_schema(app: Union["FastStream", "StreamRouter[Any]"]) -> Schema:
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
            contact=app.contact,
            license=app.license,
            tags=list(app.asyncapi_tags) if app.asyncapi_tags else None,
            externalDocs=app.external_docs,
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

    broker_meta: Dict[str, Any] = {
        "protocol": broker.protocol,
        "protocolVersion": broker.protocol_version,
        "description": broker.description,
        "tags": broker.tags,
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
        for channel_name, channel_2_6 in h.schema().items():
            if channel_2_6.subscribe is not None:
                op = Operation(
                    action="receive",
                    summary=channel_2_6.subscribe.summary,
                    description=channel_2_6.subscribe.description,
                    bindings=channel_2_6.subscribe.bindings,
                    messages=[
                        Reference(
                            **{"$ref": f"#/channels/{channel_name}/messages/SubscribeMessage"},
                        )
                    ],
                    channel=Reference(
                        **{"$ref": f"#/channels/{channel_name}"},
                    ),
                    security=channel_2_6.subscribe.security,
                )
                operations[f"{channel_name}Subscribe"] = op

            elif channel_2_6.publish is not None:
                op = Operation(
                    action="send",
                    summary=channel_2_6.publish.summary,
                    description=channel_2_6.publish.description,
                    bindings=channel_2_6.publish.bindings,
                    messages=[
                        Reference(
                            **{"$ref": f"#/channels/{channel_name}/messages/Message"},
                        )]
                    ,
                    channel=Reference(
                        **{"$ref": f"#/channels/{channel_name}"},
                    ),
                    security=channel_2_6.publish.bindings,
                )
                operations[f"{channel_name}"] = op

    for p in broker._publishers.values():
        for channel_name, channel_2_6 in p.schema().items():
            if channel_2_6.subscribe is not None:
                op = Operation(
                    action="send",
                    summary=channel_2_6.subscribe.summary,
                    description=channel_2_6.subscribe.description,
                    bindings=channel_2_6.subscribe.bindings,
                    messages=[
                        Reference(
                            **{"$ref": f"#/channels/{channel_name}/messages/SubscribeMessage"},
                        )
                    ],
                    channel=Reference(
                        **{"$ref": f"#/channels/{channel_name}"},
                    ),
                    security=channel_2_6.subscribe.security,
                )
                operations[f"{channel_name}Subscribe"] = op

            elif channel_2_6.publish is not None:
                op = Operation(
                    action="send",
                    summary=channel_2_6.publish.summary,
                    description=channel_2_6.publish.description,
                    bindings=channel_2_6.publish.bindings,
                    messages=[
                        Reference(
                            **{"$ref": f"#/channels/{channel_name}/messages/Message"},
                        )
                    ],
                    channel=Reference(
                        **{"$ref": f"#/channels/{channel_name}"},
                    ),
                    security=channel_2_6.publish.security,
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
        for channel_name, channel_v2_6 in h.schema().items():
            if channel_v2_6.subscribe:
                channel_v3_0 = Channel(
                    address=channel_name,
                    messages={
                        "SubscribeMessage": channel_v2_6.subscribe.message,
                    },
                    description=channel_v2_6.description,
                    servers=channel_v2_6.servers,
                    bindings=channel_v2_6.bindings,
                )

                channels_schema_v3_0[channel_name] = channel_v3_0

        channels.update(channels_schema_v3_0)

    for p in broker._publishers.values():
        channels_schema_v3_0 = {}
        for channel_name, channel_v2_6 in p.schema().items():
            if channel_v2_6.publish:
                channel_v3_0 = Channel(
                    address=channel_name,
                    messages={
                        "Message": channel_v2_6.publish.message,
                    },
                    description=channel_v2_6.description,
                    servers=channel_v2_6.servers,
                    bindings=channel_v2_6.bindings,
                )

                channels_schema_v3_0[channel_name] = channel_v3_0

        channels.update(channels_schema_v3_0)

    return channels


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
        p: Dict[str, Dict[str, Any]] = {}
        for name, payload in one_of.items():
            payloads.update(p.pop(DEF_KEY, {}))
            p[name] = payload
            one_of_list.append(Reference(**{"$ref": f"#/components/schemas/{name}"}))

        payloads.update(p)
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

    if isinstance(desciminator := data.get("discriminator"), dict):
        data["discriminator"] = desciminator["propertyName"]

    return data

from typing import TYPE_CHECKING, Any, Dict, List, Union

from faststream._compat import DEF_KEY, HAS_FASTAPI
from faststream.app import FastStream
from faststream.asyncapi.schema import (
    Channel,
    Components,
    Info,
    Message,
    Reference,
    Schema,
    Server,
)
from faststream.constants import ContentTypes

if TYPE_CHECKING:
    if HAS_FASTAPI:
        from faststream.broker.fastapi.router import StreamRouter


def get_app_schema(app: Union[FastStream, "StreamRouter[Any]"]) -> Schema:
    """Get the application schema.

    Args:
        app: An instance of FastStream or StreamRouter.

    Returns:
        The schema object.

    """
    servers = get_app_broker_server(app)
    channels = get_app_broker_channels(app)

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

    broker = app.broker
    if broker is None:  # pragma: no cover
        raise RuntimeError()

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
        tags=list(app.asyncapi_tags) if app.asyncapi_tags else None,
        externalDocs=app.external_docs,
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


def get_app_broker_server(
    app: Union[FastStream, "StreamRouter[Any]"],
) -> Dict[str, Server]:
    """Get the broker server for an application.

    Args:
        app: An instance of `FastStream` or `StreamRouter` representing the application.

    Returns:
        A dictionary containing the broker servers. The keys are the server names and the values are instances of `Server` class.

    Raises:
        AssertionError: If the `broker` attribute of the app is not present.

    Note:
        This function is currently incomplete and the following fields in the `broker_meta` dictionary are not populated: "security", "variables", "bindings".

    """
    servers = {}

    broker = app.broker
    assert broker  # nosec B101

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


def get_app_broker_channels(
    app: Union[FastStream, "StreamRouter[Any]"],
) -> Dict[str, Channel]:
    """Get the broker channels for an application.

    Args:
        app: An instance of FastStream or StreamRouter.

    Returns:
        A dictionary of channel names and their corresponding Channel objects.

    Raises:
        AssertionError: If the app does not have a broker.

    """
    channels = {}
    assert app.broker  # nosec B101

    for h in app.broker.handlers.values():
        channels.update(h.schema())

    for p in app.broker._publishers.values():
        channels.update(p.schema())

    return channels


def _resolve_msg_payloads(
    m: Message,
    channel_name: str,
    payloads: Dict[str, Any],
    messages: Dict[str, Any],
) -> Reference:
    one_of_list: List[Reference] = []

    m.payload = _move_pydantic_refs(m.payload, DEF_KEY)
    if DEF_KEY in m.payload:
        payloads.update(m.payload.pop(DEF_KEY))
    if "discriminator" in m.payload:
        m.payload["discriminator"] = m.payload["discriminator"]["propertyName"]

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

    return data

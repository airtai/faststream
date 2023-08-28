from typing import List

from faststream.types import AnyDict


def to_camelcase(*names: str) -> str:
    return " ".join(names).replace("_", " ").title().replace(" ", "")


def resolve_payloads(payloads: List[AnyDict]) -> AnyDict:
    ln = len(payloads)
    payload: AnyDict
    if ln > 1:
        payload = {"oneOf": {body["title"]: body for body in payloads}}
    elif ln == 1:
        payload = payloads[0]
    else:
        payload = {}
    return payload

from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from faststream.types import AnyDict


def to_camelcase(*names: str) -> str:
    return " ".join(names).replace("_", " ").title().replace(" ", "")


def resolve_payloads(
    payloads: List[Tuple["AnyDict", str]],
    extra: str = "",
    served_words: int = 1,
) -> "AnyDict":
    ln = len(payloads)
    payload: AnyDict
    if ln > 1:
        one_of_payloads = {}

        for body, handler_name in payloads:
            title = body["title"]
            words = title.split(":")

            if len(words) > 1:  # not pydantic model case
                body["title"] = title = ":".join(
                    filter(
                        lambda x: bool(x),
                        (
                            handler_name,
                            extra if extra not in words else "",
                            *words[served_words:],
                        ),
                    )
                )

            one_of_payloads[title] = body

        payload = {"oneOf": one_of_payloads}

    elif ln == 1:
        payload = payloads[0][0]

    else:
        payload = {}

    return payload

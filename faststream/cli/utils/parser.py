import re
from functools import reduce
from typing import TYPE_CHECKING, Dict, List, Tuple

if TYPE_CHECKING:
    from faststream.types import SettingField


def is_bind_arg(arg: str) -> bool:
    """Determine whether the received argument refers to --bind.

    bind arguments are like: 0.0.0.0:8000, [::]:8000, fd://2, /tmp/socket.sock

    """
    bind_regex = re.compile(r":\d+$|:/+\d|:/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+")
    return bool(bind_regex.search(arg))


def parse_cli_args(*args: str) -> Tuple[str, Dict[str, "SettingField"]]:
    """Parses command line arguments."""
    extra_kwargs: Dict[str, SettingField] = {}

    k: str = ""
    v: SettingField

    field_args: List[str] = []
    app = ""
    for item in [
        *reduce(
            lambda acc, x: acc + x.split("="),  # type: ignore
            args,
            [],
        ),
        "-",
    ]:
        if ":" in item and not is_bind_arg(item):
            app = item

        else:
            if "-" in item:
                if k:
                    k = k.strip().lstrip("-").replace("-", "_")

                    if len(field_args) == 0:
                        v = not k.startswith("no_")
                    elif len(field_args) == 1:
                        v = field_args[0]
                    else:
                        v = field_args

                    key = remove_prefix(k, "no_")
                    if (exists := extra_kwargs.get(key)) is not None:
                        v = [
                            *(exists if isinstance(exists, list) else [exists]),
                            *(v if isinstance(v, list) else [v]),
                        ]

                    extra_kwargs[key] = v
                    field_args = []

                k = item

            else:
                field_args.append(item)

    return app, extra_kwargs


def remove_prefix(text: str, prefix: str) -> str:
    """Removes a prefix from a given text.

    Python 3.8 compatibility function

    Args:
        text (str): The text from which the prefix will be removed.
        prefix (str): The prefix to be removed from the text.

    Returns:
        str: The text with the prefix removed. If the text does not start with the prefix, the original text is returned.
    """
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text

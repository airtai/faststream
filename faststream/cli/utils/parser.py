from functools import reduce
from typing import Dict, List, Tuple

from faststream.types import SettingField


def parse_cli_args(*args: str) -> Tuple[str, Dict[str, SettingField]]:
    extra_kwargs: Dict[str, SettingField] = {}

    k: str = ""
    v: SettingField

    field_args: List[str] = []
    app = ""
    for item in reduce(
        lambda acc, x: acc + x.split("="),  # type: ignore
        args,
        [],
    ) + ["-"]:
        if ":" in item:
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

                    extra_kwargs[remove_prefix(k, "no_")] = v
                    field_args = []

                k = item

            else:
                field_args.append(item)

    return app, extra_kwargs


def remove_prefix(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text

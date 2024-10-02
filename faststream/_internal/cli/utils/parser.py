from functools import reduce
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from faststream._internal.basic_types import SettingField


def parse_cli_args(*args: str) -> tuple[str, dict[str, "SettingField"]]:
    """Parses command line arguments."""
    extra_kwargs: dict[str, SettingField] = {}

    k: str = ""
    v: SettingField

    field_args: list[str] = []
    app = ""
    for item in [
        *reduce(
            lambda acc, x: acc + x.split("="),
            args,
            cast(list[str], []),
        ),
        "-",
    ]:
        if ":" in item:
            app = item

        elif "-" in item:
            if k:
                k = k.strip().lstrip("-").replace("-", "_")

                if len(field_args) == 0:
                    v = not k.startswith("no_")
                elif len(field_args) == 1:
                    v = field_args[0]
                else:
                    v = field_args

                key = k.removeprefix("no_")
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

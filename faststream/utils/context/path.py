import re
from typing import Optional, Pattern, Tuple

PARAM_REGEX = re.compile("{([a-zA-Z_]+)}")


def compile_path(
    path: str,
    replace_symbol: str,
) -> Tuple[Optional[Pattern[str]], str]:
    path_regex = "^"
    path_format = ""

    idx = 0
    params = set()
    duplicated_params = set()
    for match in PARAM_REGEX.finditer(path):
        param_name = match.groups("str")[0]

        path_regex += re.escape(path[idx : match.start()])
        path_regex += f"(?P<{param_name.replace('+', '')}>[^/]+)"

        path_format += path[idx : match.start()]
        path_format += replace_symbol

        if param_name in params:
            duplicated_params.add(param_name)
        else:
            params.add(param_name)

        idx = match.end()

    if duplicated_params:
        names = ", ".join(sorted(duplicated_params))
        ending = "s" if len(duplicated_params) > 1 else ""
        raise ValueError(f"Duplicated param name{ending} {names} at path {path}")

    if idx == 0:
        regex = None
    else:
        path_regex += re.escape(path[idx:]) + "$"
        regex = re.compile(path_regex)

    path_format += path[idx:]
    return regex, path_format

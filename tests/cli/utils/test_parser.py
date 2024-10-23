import pytest

from faststream._internal.cli.utils.parser import parse_cli_args

APPLICATION = "module:app"

ARG1 = (
    "--k",
    "1",
)
ARG2 = (
    "-k2",
    "1",
)
ARG3 = ("--k3",)
ARG4 = ("--no-k4",)
ARG5 = (
    "--k5",
    "1",
    "1",
)
ARG6 = ("--some-key",)
ARG7 = ("--k7", "1", "2", "--k7", "3")


@pytest.mark.parametrize(
    "args",
    (
        pytest.param(
            (APPLICATION, *ARG1, *ARG2, *ARG3, *ARG4, *ARG5, *ARG6, *ARG7),
            id="app first",
        ),
        pytest.param(
            (*ARG1, *ARG2, *ARG3, APPLICATION, *ARG4, *ARG5, *ARG6, *ARG7),
            id="app middle",
        ),
        pytest.param(
            (*ARG1, *ARG2, *ARG3, *ARG4, *ARG5, *ARG6, *ARG7, APPLICATION),
            id="app last",
        ),
    ),
)
def test_custom_argument_parsing(args: tuple[str]) -> None:
    app_name, extra = parse_cli_args(*args)
    assert app_name == APPLICATION
    assert extra == {
        "k": "1",
        "k2": "1",
        "k3": True,
        "k4": False,
        "k5": ["1", "1"],
        "some_key": True,
        "k7": ["1", "2", "3"],
    }

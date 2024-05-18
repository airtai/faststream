import logging
import sys
import warnings
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import anyio
import typer
from click.exceptions import MissingParameter
from typer.core import TyperOption

from faststream import FastStream
from faststream.__about__ import INSTALL_WATCHFILES, __version__
from faststream.cli.docs.app import docs_app
from faststream.cli.utils.imports import import_from_string
from faststream.cli.utils.logs import LogLevels, get_log_level, set_log_level
from faststream.cli.utils.parser import parse_cli_args
from faststream.exceptions import SetupError, ValidationError

if TYPE_CHECKING:
    from faststream.broker.core.usecase import BrokerUsecase
    from faststream.types import AnyDict, SettingField

cli = typer.Typer(pretty_exceptions_short=True)
cli.add_typer(docs_app, name="docs", help="AsyncAPI schema commands")


def version_callback(version: bool) -> None:
    """Callback function for displaying version information."""
    if version:
        import platform

        typer.echo(
            f"Running FastStream {__version__} with {platform.python_implementation()} "
            f"{platform.python_version()} on {platform.system()}"
        )

        raise typer.Exit()


@cli.callback()
def main(
    version: Optional[bool] = typer.Option(
        False,
        "-v",
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show current platform, python and FastStream version",
    ),
) -> None:
    """Generate, run and manage FastStream apps to greater development experience."""


@cli.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def run(
    ctx: typer.Context,
    app: str = typer.Argument(
        ...,
        help="[python_module:FastStream] - path to your application",
    ),
    workers: int = typer.Option(
        1,
        show_default=False,
        help="Run [workers] applications with process spawning",
    ),
    log_level: LogLevels = typer.Option(
        LogLevels.info,
        case_sensitive=False,
        show_default=False,
        help="[INFO] default",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        is_flag=True,
        help="Restart app at directory files changes",
    ),
    watch_extensions: List[str] = typer.Option(
        (),
        "--extension",
        "--ext",
        "--reload-extension",
        "--reload-ext",
        help="List of file extensions to watch by",
    ),
    app_dir: str = typer.Option(
        ".",
        "--app-dir",
        help=(
            "Look for APP in the specified directory, by adding this to the PYTHONPATH."
            " Defaults to the current working directory."
        ),
    ),
    is_factory: bool = typer.Option(
        False,
        "--factory",
        is_flag=True,
        help="Treat APP as an application factory",
    ),
) -> None:
    """Run [MODULE:APP] FastStream application."""
    if watch_extensions and not reload:
        typer.echo(
            "Extra reload extensions has no effect without `--reload` flag."
            "\nProbably, you forgot it?"
        )

    app, extra = parse_cli_args(app, *ctx.args)
    casted_log_level = get_log_level(log_level)

    if app_dir:  # pragma: no branch
        sys.path.insert(0, app_dir)

    args = (app, extra, is_factory, casted_log_level)

    if reload and workers > 1:
        raise SetupError("You can't use reload option with multiprocessing")

    if reload:
        try:
            from faststream.cli.supervisors.watchfiles import WatchReloader
        except ImportError:
            warnings.warn(INSTALL_WATCHFILES, category=ImportWarning, stacklevel=1)
            _run(*args)

        else:
            module_path, _ = import_from_string(app)

            if app_dir != ".":
                reload_dirs = [str(module_path), app_dir]
            else:
                reload_dirs = [str(module_path)]

            WatchReloader(
                target=_run,
                args=args,
                reload_dirs=reload_dirs,
            ).run()

    elif workers > 1:
        from faststream.cli.supervisors.multiprocess import Multiprocess

        Multiprocess(
            target=_run,
            args=(*args, logging.DEBUG),
            workers=workers,
        ).run()

    else:
        _run(*args)


def _run(
    # NOTE: we should pass `str` due FastStream is not picklable
    app: str,
    extra_options: Dict[str, "SettingField"],
    is_factory: bool,
    log_level: int = logging.INFO,
    app_level: int = logging.INFO,
) -> None:
    """Runs the specified application."""
    _, app_obj = import_from_string(app)
    if is_factory and callable(app_obj):
        app_obj = app_obj()

    if not isinstance(app_obj, FastStream):
        raise typer.BadParameter(
            f'Imported object "{app_obj}" must be "FastStream" type.',
        )

    set_log_level(log_level, app_obj)

    if sys.platform not in ("win32", "cygwin", "cli"):  # pragma: no cover
        with suppress(ImportError):
            import uvloop

            uvloop.install()  # type: ignore[attr-defined]

    try:
        anyio.run(
            app_obj.run,
            app_level,
            extra_options,
        )

    except ValidationError as e:
        ex = MissingParameter(
            param=TyperOption(param_decls=[f"--{x}" for x in e.fields])
        )

        try:
            from typer import rich_utils

            rich_utils.rich_format_error(ex)
        except ImportError:
            ex.show()

        sys.exit(1)


@cli.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def publish(
    ctx: typer.Context,
    app: str = typer.Argument(..., help="FastStream app instance, e.g., main:app"),
    message: str = typer.Argument(..., help="Message to be published"),
    rpc: bool = typer.Option(False, help="Enable RPC mode and system output"),
    is_factory: bool = typer.Option(
        False,
        "--factory",
        is_flag=True,
        help="Treat APP as an application factory",
    ),
) -> None:
    """Publish a message using the specified broker in a FastStream application.

    This command publishes a message to a broker configured in a FastStream app instance.
    It supports various brokers and can handle extra arguments specific to each broker type.
    These are parsed and passed to the broker's publish method.
    """
    app, extra = parse_cli_args(app, *ctx.args)
    extra["message"] = message
    extra["rpc"] = rpc

    try:
        if not app:
            raise ValueError("App parameter is required.")
        if not message:
            raise ValueError("Message parameter is required.")

        _, app_obj = import_from_string(app)
        if callable(app_obj) and is_factory:
            app_obj = app_obj()

        if not app_obj.broker:
            raise ValueError("Broker instance not found in the app.")

        result = anyio.run(publish_message, app_obj.broker, extra)

        if rpc:
            typer.echo(result)

    except Exception as e:
        typer.echo(f"Publish error: {e}")
        sys.exit(1)


async def publish_message(broker: "BrokerUsecase[Any, Any]", extra: "AnyDict") -> Any:
    try:
        async with broker:
            return await broker.publish(**extra)  # type: ignore[union-attr]
    except Exception as e:
        typer.echo(f"Error when broker was publishing: {e}")
        sys.exit(1)

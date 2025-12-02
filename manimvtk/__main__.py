from __future__ import annotations

import click
import cloup

from manimvtk import __version__
from manimvtk._config import cli_ctx_settings, console
from manimvtk.cli.cfg.group import cfg
from manimvtk.cli.checkhealth.commands import checkhealth
from manimvtk.cli.default_group import DefaultGroup
from manimvtk.cli.init.commands import init
from manimvtk.cli.plugins.commands import plugins
from manimvtk.cli.render.commands import render
from manimvtk.constants import EPILOG


def show_splash(ctx: click.Context, param: click.Option, value: str | None) -> None:
    """When giving a value by console, show an initial message with the ManimVTK
    version before executing any other command: ``ManimVTK vA.B.C``.

    Parameters
    ----------
    ctx
        The Click context.
    param
        A Click option.
    value
        A string value given by console, or None.
    """
    if value:
        console.print(f"ManimVTK [green]v{__version__}[/green]\n")


def print_version_and_exit(
    ctx: click.Context, param: click.Option, value: str | None
) -> None:
    """Same as :func:`show_splash`, but also exit when giving a value by
    console.

    Parameters
    ----------
    ctx
        The Click context.
    param
        A Click option.
    value
        A string value given by console, or None.
    """
    show_splash(ctx, param, value)
    if value:
        ctx.exit()


@cloup.group(
    context_settings=cli_ctx_settings,
    cls=DefaultGroup,
    default="render",
    no_args_is_help=True,
    help="Animation engine for explanatory math videos with VTK scientific visualization support.",
    epilog="See 'manimvtk <command>' to read about a specific subcommand.\n\n"
    "Note: the subcommand 'manimvtk render' is called if no other subcommand "
    "is specified. Run 'manimvtk render --help' if you would like to know what the "
    f"'-ql' or '-p' flags do, for example.\n\n{EPILOG}",
)
@cloup.option(
    "--version",
    is_flag=True,
    help="Show version and exit.",
    callback=print_version_and_exit,
    is_eager=True,
    expose_value=False,
)
@click.option(
    "--show-splash/--hide-splash",
    is_flag=True,
    default=True,
    help="Print splash message with version information.",
    callback=show_splash,
    is_eager=True,
    expose_value=False,
)
@cloup.pass_context
def main(ctx: click.Context) -> None:
    """The entry point for ManimVTK.

    Parameters
    ----------
    ctx
        The Click context.
    """
    pass


main.add_command(checkhealth)
main.add_command(cfg)
main.add_command(plugins)
main.add_command(init)
main.add_command(render)

if __name__ == "__main__":
    main()

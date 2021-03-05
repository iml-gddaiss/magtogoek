"""
Author: JeromeJGuay
Date: Mars 2

This module contains the command line applications `mtgk`.

================================================================================
        __  ___    ____    _____ ________ ______ _____  ______ _____  __ __
       /  |/   |  / _  |  / ___//__  ___// __  // ___/ / __  //  __/ / // /
      / /|  /| | / /_| | / /_ \   / /   / /_/ // /_ \ / /_/ //  __/ / _  /
     /_/ |_/ |_|/_/  |_|/_____|  /_/   /_____//_____|/_____//_____//_/ \_\.

================================================================================

Descriptions:
  TODO

Usage:
  In terminal, typing,

    $ mtgk [`config`/`process`] `config_name`

  should return,

    Config file created for `process` processing -> `config_name`.ini

  Each process has specific `--optionals` arguments. Typing

    $ magto_c `process`

  will bring up the `process` page, where all the `--optionals` are listed.

    $ magto_c process config_name [--optionals]

  You can also type,

    $ magto_c

  And follow the instructions.
"""
import click
import typing as tp
import subprocess

from pathlib import Path
from magtogoek.metadata.toolbox import json2dict
from magtogoek.bin.configparser_templates import make_configparser
from magtogoek.bin.command_options import adcp_options, add_options

### Global variable used by some of the module functions.
magtogoek_version = "0.0.1"
valid_sensor_types = ["adcp"]
logo_json_path = "files/logo.json"


CONTEXT_SETTINGS = dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
    help_option_names=["-h", "--help"],
)


class GroupHelp(click.Group):
    """Custom help for magtogoek_config"""

    def format_help(self, ctx, formatter):

        print()
        subprocess.run(["printf", "'\e[8;40;80t'"])
        click.clear()
        _print_logo(logojson=logo_json_path, group=ctx.info_name)
        click.secho("\nDescriptions:", fg="red")
        _print_description(ctx.info_name)
        click.secho("\nCommands:", fg="red")
        _print_arguments(ctx.info_name)
        click.secho("\nHelp", fg="cyan")
        _print_help_commands()


# ---------------------------#
#      mtgk entry point      #
# ---------------------------#
@click.group(cls=GroupHelp, context_settings=CONTEXT_SETTINGS)
def magtogoek():
    pass


### config sub-group
@magtogoek.group(cls=GroupHelp, context_settings=CONTEXT_SETTINGS)
def config():
    pass


### process sub-group
@magtogoek.group(cls=GroupHelp, context_settings=CONTEXT_SETTINGS)
def process():
    pass


### adcp: config sub-command
@config.command("adcp")
@click.argument(
    "config_name", metavar="config_name", required=False, default=None, type=str
)
@add_options(adcp_options())
@click.pass_context
def config_adcp(
    ctx,
    config_name,
    input_files,
    netcdf_output,
    odf_output,
    platform_file,
    merge,
    gps,
    sonar,
    yearbase,
    up,
    start_time,
    end_time,
    qc,
    amplitude_threshold,
    percentgood_threshold,
    correlation_threshold,
    horizontal_velocity_threshold,
    vertical_velocity_threshold,
    error_velocity_threshold,
    side_lobe,
    m_corr,
    pitch_threshold,
    roll_threshold,
    drop_pg,
    drop_corr,
    drop_amp,
    mk_fig,
    mk_log,
    bodc_name,
):
    """\033[F \033[F \033[K"""  # \033[F \033[F \033[K deletes default click help
    if not config_name:
        click.clear()
        _print_logo(logojson=logo_json_path, process="adcp", group="config")
        click.secho("\nDescription:", fg="red")
        _print_description("adcp")
        click.secho("\nRequired argument:", fg="red")
        click.secho(
            "  config_name\t\t file name (path/to/file) for the configuration file."
        )
        click.secho("\nTo show options", fg="cyan")
        click.secho("  $ mtgk config adcp -h")
        if len(click.get_os_args()) > 2:
            click.secho(
                "\nERROR: A `config_name` is required before the  options.\n", fg="red"
            )

        exit()

    click.secho("Options:", fg="green")
    _print_passed_options(ctx.params)

    config_name = _validate_config_name(ctx.params["config_name"])

    # Change 'up' value from bool to str.
    ctx.params["up"] = (lambda x: "up" * x + "down" * (not x))(ctx.params["up"])

    # Translate options names to those used in the configparser.
    translator = dict(
        adcp_orientation="up",
        GPS_file="gps",
        quality_control="qc",
        side_lobe_correction="side_lobe",
        trim_leading_data="start_time",
        trim_trailling_data="end_time",
        platform_motion_correction="m_corr",
        merge_output_file="merge",
        drop_percent_good="drop_pg",
        drop_correlation="drop_corr",
        drop_amplitude="drop_amp",
        make_figures="mk_fig",
        make_log="mk_log",
    )
    for key, item in translator.items():
        ctx.params[key] = ctx.params.pop(item)

    make_configparser(
        filename=config_name,
        sensor_type="adcp",
        options=ctx.params,
    )
    click.echo(
        click.style(
            f"Config file created for adcp processing -> {config_name}", bold=True
        )
    )
    exit()


def _validate_config_name(config_name: str) -> str:
    """Check if directory or/and file name exist.

    Ask to make the directories if they don't exist.
    Ask  to ovewrite the file if a file already exist.

    Appends a `.ini` suffix (extension) none was given.
    But keeps other suffixes.
    Ex. path/to/file.ext1.ext2.ini

    """
    if Path(config_name).suffix != ".ini":
        config_name += ".ini"

    while not Path(config_name).parents[0].is_dir():
        if click.confirm(
            click.style(
                "Directory does not exist. Do you want to create it ?", bold=True
            ),
            default=False,
        ):
            Path(config_name).parents[0].mkdir(parents=True)
        else:
            config_name = _ask_for_config_name()

    if Path(config_name).is_file():
        if not click.confirm(
            click.style(
                "A `.ini` file with this name already exists. Overwrite ?", bold=True
            ),
            default=True,
        ):
            return _validate_config_name(_ask_for_config_name())
    return config_name


def _ask_for_config_name() -> str:
    """ckick.prompt that ask for `config_name`"""
    return click.prompt(
        click.style(
            "\nEnter a filename (path/to/file) for the config `.ini` file. ", bold=True
        )
    )


def _print_passed_options(ctx_params: tp.Dict):
    for key, item in ctx_params.items():
        if item is not None:
            if item is True:
                click.echo(key + ": " + click.style(str(item), fg="green"))
            elif item is False:
                click.echo(key + ": " + click.style(str(item), fg="red"))
            elif type(item) is str:
                click.echo(key + ": " + click.style(str(item), fg="yellow"))
            else:
                click.echo(key + ": " + click.style(str(item), fg="blue"))


def _print_logo(process: str = None, logojson: str = "file/logo.json", group: str = ""):
    """open and print logo from logo.json
    If a process is given, prints the process logo.
    """
    click.echo(click.style("=" * 80, fg="white", bold=True))

    try:
        logos = json2dict(Path(__file__).parents[0] / Path(logojson))

        click.echo(click.style(logos["magtogoek"], fg="blue", bold=True))
        if process == "adcp":
            click.echo(click.style(logos["adcp"], fg="red", bold=True))

    except FileNotFoundError:
        click.echo(click.style("WARNING: logo.json not found", fg="yellow"))
    except KeyError:
        click.echo(click.style("WARNING: key in logo.json not found", fg="yellow"))

    click.echo(
        click.style(
            f"version: {magtogoek_version}" + f" {group} ".rjust(67, " "),
            fg="green",
            bold=True,
        )
    )
    click.echo(click.style("=" * 80, fg="white", bold=True))


def _print_arguments(group):
    """print group arguments(command)"""
    if group == "mtgk":
        click.secho(
            "  config".ljust(20, " ") + "Command to make configuration files",
            fg="white",
        )
        click.secho("  process".ljust(20, " ") + "Command to process data", fg="white")
    if group == "config":
        click.secho("  adcp".ljust(20, " ") + "Config file for adcp data. ", fg="white")
    if group == "process":
        click.secho("TODO")


def _print_description(group):
    """print group/command desciptions"""
    if group == "mtgk":
        click.echo("""TODO""")
    if group == "config":
        click.echo(
            """  The config command creates a `.ini`  configuration file. After the command is
  called, a `sensor_type` (type of date to be process) and  a `config_name` for
  the configuration file. The configuration file  can then be passed to  to the
  process command.

  The configuration `.ini` files  contain global and sensor specific parameters.
  These parameters can be edited afterward in a text editor  or set here with
  optionals arguments.""",
        )
    if group == "process":
        click.echo("""TODO""")
    if group == "adcp":
        click.echo("""TODO""")


def _print_help_commands():
    click.echo("\n  -h/--help".ljust(20, " ") + "Show this help page")


def _print_command_help(command):
    """print command help"""
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))

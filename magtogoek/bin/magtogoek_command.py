"""
Author: JeromeJGuay
Date: Mars 2

This module contains the command line applications `magto_c` that run magtoek_config(). 

Note: A simpler command interface would proably be better.

================================================================================
        __  ___    ____    _____ ________ ______ _____  ______ _____  __ __
       /  |/   |  / _  |  / ___//__  ___// __  // ___/ / __  //  __/ / // /
      / /|  /| | / /_| | / /_ \   / /   / /_/ // /_ \ / /_/ //  __/ / _  /
     /_/ |_/ |_|/_/  |_|/_____|  /_/   /_____//_____|/_____//_____//_/ \_\.


================================================================================

Descriptions:
  `magto_c` (magtogoek_config) is a command line applications that creates
  a `.ini` configuration file. After calling `magto_c`, you have to provide
  a `process` (type of date to be process) and a `config_name` for the
  configuration file. The configuration file can then be passed to
  magtogoek_process.

  The created `.ini` file will contains  global and process specific parameters.
  These parameters can be edited afterward in a text editor or set here with
  optionals arguments

Usage:
  In terminal, typing,

    $ magto_c `process` `config_name`

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
import os
import typing as tp
import sys

from pathlib import Path
from magtogoek.metadata.toolbox import json2dict
from magtogoek.bin.configparser_templates import make_configparser
import subprocess


### Global variable used by some of the module functions.
magtogoek_version = "0.0.1"
valid_sensor_types = ["adcp"]
logo_json_path = "files/logo.json"


CONTEXT_SETTINGS = dict(
    ignore_unknown_options=True,
    allow_extra_args=True,
    help_option_names=["-h", "--help"],
)


class HelpAsArgs(click.Group):
    # change the section head of sub commands to "Arguments"

    def format_commands(self, ctx, formatter):
        rows = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None:
                continue

            help = cmd.short_help or ""
            rows.append((subcommand, help))

        if rows:
            with formatter.section("Arguments"):
                formatter.write_dl(rows)


class MagtogoekHelp(click.Group):
    """Custom help for magtogoek_config"""

    def format_help(self, ctx, formatter):
        click.clear()
        _print_logo(logojson=logo_json_path, group="main")
        _print_doc(["Description", "Help"])


# magtogoek main group
@click.group(cls=MagtogoekHelp, context_settings=CONTEXT_SETTINGS)
def magtogoek():
    pass


class ConfigHelp(click.Group):
    """Custom help for magtogoek_config"""

    def format_help(self, ctx, formatter):
        subprocess.run(["printf", "'\e[8;40;80t'"])
        click.clear()
        _print_logo(logojson=logo_json_path, group="config")
        _print_doc(["Description", "Help"])


### config sub-group
@magtogoek.group(cls=ConfigHelp, context_settings=CONTEXT_SETTINGS)
def config():
    pass


class ProcessHelp(click.Group):
    """Custom help for magtogoek_config"""

    def format_help(self, ctx, formatter):
        click.clear()
        _print_logo(logojson=logo_json_path, group="config")
        _print_doc(["Description", "Help"])


class SetDirHelp(click.Group):
    """Custom help for magtogoek_config"""

    def format_help(self, ctx, formatter):
        click.clear()
        _print_logo(logojson=logo_json_path, group="config")
        _print_doc(["Description", "Help"])


@magtogoek.group(cls=ProcessHelp, context_settings=CONTEXT_SETTINGS)
def process():
    """TODO"""
    pass


@magtogoek.group(cls=SetDirHelp, context_settings=CONTEXT_SETTINGS)
def setdir():
    """TODO"""
    pass


### adcp: config sub-command
@config.command("adcp")
@click.argument(
    "config_name", metavar="config_name", required=False, default=None, type=str
)
@click.option(
    "-i",
    "--input-files",
    nargs=1,
    type=click.STRING,
    help="Expression identifying adcp files",
)
@click.option(
    "-n",
    "--netcdf-output",
    nargs=1,
    type=click.STRING,
    help="Expression for netcdf output file or files name",
)
@click.option(
    "-o",
    "--odf-output",
    nargs=1,
    type=click.STRING,
    help="Expression for odf file or files name",
)
@click.option(
    "--merge/--no-merge",
    help="""Merge input into one output file.,
    Default --merge""",
    default=True,
)
@click.option(
    "-F",
    "--platform-file",
    type=click.Path(exists=True),
    help="path/to/platform_file",
    nargs=1,
)
@click.option(
    "-G",
    "--gps",
    type=click.Path(exists=True),
    help="""path/to/netcdf4 file containing the gps data,
    `longitude`, `latitude`, of the platform. If provided,
    they will be used instead of the GPS data in the adcp file""",
)
@click.option(
    "-s",
    "--sonar",
    type=click.STRING,
    help="""String designating type of adcp. This
    is fed to CODAS Multiread or switches to the RTI
    binary reader. Must be one
    of `wh`, `os`, `bb`, `nb` or `sw`""",
)
@click.option(
    "-y",
    "--yearbase",
    type=click.INT,
    help="""year when the adcp sampling started. exL `1970`""",
)
@click.option(
    "--up/--down",
    help="""Vertical orientation of the adcp. Default [--down].""",
    default=False,
)
@click.option(
    "-l",
    "--start-time",
    type=click.STRING,
    help="Remove leading data before this date. Fomart (YYYYMMDDHHMM).",
    nargs=1,
)
@click.option(
    "-t",
    "--end-time",
    metavar="metavar test",
    type=click.STRING,
    help="Remove trailling data after this date. Format (YYYYMMDDHHMM).",
    nargs=1,
)
@click.option(
    "--qc/--no-qc",
    help="Do quality control. Default [--qc] (True)",
    default=True,
)
@click.option(
    "-a",
    "--amplitude-threshold",
    type=click.FLOAT,
    help="Amplitude threshold (0-255). Defaults to 0.",
    nargs=1,
)
@click.option(
    "-p",
    "--percentgood-threshold",
    type=click.FLOAT,
    help="Percentage of 4 beam threshold (0-100). Defaults to 90.",
)
@click.option(
    "-c",
    "--correlation-threshold",
    type=click.FLOAT,
    help="Correlation threshold (0-255). Defaults to 64.",
    nargs=1,
)
@click.option(
    "-u",
    "--horizontal-velocity-threshold",
    type=click.FLOAT,
    help="Horizontal velocity threshold (u,v).Defaults to 5.",
    nargs=1,
)
@click.option(
    "-w",
    "--vertical-velocity-threshold",
    type=click.FLOAT,
    help="Vertial velocity threshold (u,v).Defaults to 5.",
    nargs=1,
)
@click.option(
    "-E",
    "--error-velocity-threshold",
    type=click.FLOAT,
    help="Error velocity threshold (u,v).Defaults to 5.",
    nargs=1,
)
@click.option(
    "--side-lobe/--no-side-lobe",
    help="Side lobe correction. Default [--side-lobe] (True))",
    default=True,
)
@click.option(
    "--m-corr/--no-m-corr",
    help="""Motion correction. Default[-no-m-corr] (True).
    Uses `bt` if available or GSP data. If the adcp
    file does not contain GPS data. A netcdf
    file with with variable named (`longitude`, `latitude`)
    needs to be provided with options `-G`""",
    default=False,
)
@click.option(
    "-P",
    "--pitch-threshold",
    type=click.FLOAT,
    help="Pitch threshold (0-180).Defaults to 20.",
    nargs=1,
)
@click.option(
    "-R",
    "--roll-threshold",
    type=click.FLOAT,
    help="Roll threshold (0-180).Defaults to 20.",
    nargs=1,
)
@click.option(
    "--drop-pg/--keep-pg",
    help="""Drop the percent good data from the output dataset.
    Default [--drop-pg] (True)""",
    default=True,
)
@click.option(
    "--drop-corr/--keep-corr",
    help="""Drop the correlation data from the output dataset.
    Default [--drop-corr] (True)""",
    default=True,
)
@click.option(
    "--drop-amp/--keep-amp",
    help="""Drop the amplitude data from the output dataset.
    Default [--drop-amp] (True)""",
    default=True,
)
@click.option(
    "--mk-log/--no-mk-log",
    help="""Make an output log of the processing.
    Default [--mk-log] (True)""",
    default=True,
)
@click.option(
    "--mk-fig/--no-mk-fig",
    help="""Make figures to inspect the data.
    Default [--mk-fig] (True)""",
    default=True,
)
@click.option(
    "--bodc-name/--gen-name",
    help="""Name of the output variables. Using --gen-name
    outputs generic variables names instead of BODC P01 name.
    Default [--bodc-name]""",
    default=True,
)
@click.pass_context
def adcp(
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
    """\033[F \033[F \033[K
    Positional argument:\n
    1 - config_name\t\t file name (path/to/file) configuration file.
    """  # \033[F \033[F \033[K deletes default click help

    if not config_name:
        _print_logo(logojson=logo_json_path, process="adcp", group="config")
        _print_help_msg(adcp)
        exit()
    _print_passed_options(ctx.params)

    config_name = _validate_config_name(ctx.params["config_name"])

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


def _ask_for_process(valid_process: tp.List[str]) -> str:
    """ckick.prompt that ask for `process`"""
    process = click.prompt(
        click.style(
            f"What type of data do you want to process: {valid_process} ",
            bold=True,
        )
    )
    while process not in valid_process:
        click.echo(click.style("ERROR: Invalid process", fg="red"))
        process = click.prompt(
            click.style(
                f"What type of data do you want to process. Choose from {valid_process}: ",
                bold=True,
            )
        )
    return process


def _print_invalid_process(valid_process: str):
    """print for invalid process"""
    click.echo(click.style("ERROR: Invalid process", fg="red"))
    click.echo(click.style(f"Valid process: {valid_process}"))
    click.echo("Help: magto_c --help")


def _ask_for_config_name() -> str:
    """ckick.prompt that ask for `config_name`"""
    return click.prompt(
        click.style(
            "\nEnter a filename (path/to/file) for the config `.ini` file. ", bold=True
        )
    )


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

    while Path(config_name).is_file():
        if click.confirm(
            click.style(
                "A `.ini` file with this name already exists. Overwrite ?", bold=True
            ),
            default=True,
        ):
            break
        else:
            config_name = _ask_for_config_name()
    return config_name


def _ask_for_options() -> tp.List[str]:
    """click.prompt that ask for `options`.
    Removes any empty string from list"""
    click.echo(click.style("\nEnter options or press enter to pass:", bold=True))
    return list(
        filter(
            None,
            click.prompt(click.style("\nOptions:", bold=True), default="").split(" "),
        )
    )


def _print_passed_options(ctx_params: tp.Dict):
    for key, item in ctx_params.items():
        if item is not None:
            print(key, item)


def _print_porcess_page(process: str):
    """clear terminal and print process page"""
    click.clear()
    _print_logo(process, logojson=logo_json_path)
    _print_help_msg(
        {
            "adcp": adcp,
        }[process]
    )


def _print_logo(
    process: str = None, logojson: str = "file/logo.json", group: str = "ocean"
):
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


def _print_help_msg(command):
    """print command help"""
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


def _print_doc(docs: tp.List[str]):
    """print formated doc using:

    \t _print_description()
    \t _print_usage()
    \t _print_parameter()
    \t _print_help()

    paramters:
    ----------
    doc:
        list of doc to print. Docs print in the order given.

    """
    doc_functions = dict(
        Description=_print_description,
        Usage=_print_usage,
        Parameters=_print_parameters,
        Help=_print_help,
    )
    for doc in docs:
        click.echo(click.style(f"\n{doc}:", fg="red"))
        click.echo(click.style(doc_functions[doc](), fg="white"))


def _print_description():
    return """
  `magto_c` is a command line applications that creates a `.ini`
  configuration file. After the function is called, you have to provide a
  `process` (type of date to be process) and a `config_name` for the
  configuration file. The configuration file can then be passed to
  magtogoek_process.

  The created `.ini` file will contains  global and process specific parameters.
  These parameters can be edited afterward in a text editor or set here with
  optionals arguments."""


def _print_parameters():
    return """
    process       Type of data to be process. Choose one of `adcp`

    config_name   Name for the configuration_file. The configuration
                  file is made in the current directory unless a path
                  is provided. ex:  `config_file` = path/to/filename"""


def _print_help():
    return """
    $ magto_c -h/--help                                  (C-c C-c to quit)
    """


def _print_usage():
    return """
  Typing,

    $ magto_c `process` `config_name`

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


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options

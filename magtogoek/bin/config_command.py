"""
Author: JeromeJGuay
Date: Mars 2

This module contains the command line applications.
It is not clean. But it works.

FIXME: mag vs magtogoek.
FIXME: COMPARTIMER PLUS

================================================================================
        __  ___    ____    _____ ________ ______ _____  ______ _____  __ __
       /  |/   |  /    |  / ___//__  ___// __  // ___/ / __  //  __/ / // /
      / /|  /| | / /_| | / /_ \   / /   / /_/ // /_ \ / /_/ //  __/ / _  /
     /_/ |_/ |_|/_/  |_|/_____|  /_/   /_____//_____|/_____//_____//_/ \_\.

                                                                       -CONFIG-
================================================================================

Descriptions:
  `magtogoek_config` is a command line applications that creates a `.ini`
  configuration file. After the function is called, you have to provide a
  `process` (type of date to be process) and a `config_name` for the
  configuration file. The configuration file can then be passed to
  magtogoek_process.

  The created `.ini` file will contains  global and process specific parameters.
  These parameters can be edited afterward in a text editor or set here with
  optionals arguments

Usage:
  In terminal, typing,

    $ magtogoek_config `process` `config_name`

  should return,

    Config file created for `process` processing -> `config_name`.ini

  Each process has specific `--optionals` arguments. Typing

    $ magtogoek_config `process`

  will bring up the `process` page, where all the `--optionals` are listed.

    $ magtogoek_config process config_name [--optionals]

  You can also type,

    $ magtogoek_config

  And follow the instructions.
"""
import click
import os
import subprocess
import typing as tp

from pathlib import Path
from magtogoek.metadata.toolbox import json2dict
from magtogoek.config_parser import make_configparser
from magtogoek.adcp.config_parser import adcp_configparser
from magtogoek.toolbox import query_yes_no

### Global variable used by some of the module functions.
magtogoek_version = "0.0.1"
valid_process = ["adcp"]
logo_json_path = "file/logo.json"


class GlobalHelp(click.Command):
    """Custom help for magtogoek_config"""

    def format_help(self, ctx, formatter):
        click.clear()
        _print_logo(logojson=logo_json_path)
        _print_doc(["Description", "Usage", "Parameters", "Help"])


@click.command(
    cls=GlobalHelp,
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("process", required=False, default=None, type=str)
@click.argument("config_name", required=False, default=None, type=str)
@click.argument("options", nargs=-1)
def magtogoek_config(process, config_name, options):
    ### First we checks if a `config_name` was pass. This implies that a process was pass first.
    if config_name:
        if process not in valid_process:
            _print_invalid_process(valid_process)
            exit()

        # the command is then pass to subprocess to process the command.
        command = [f"magtogoek_{process}_config"] + [config_name] + list(options)
        subprocess.run(command)
        exit()

    ### if no config_name was pass, checks if a process was pass.
    if process:
        if process in valid_process:
            # Quick terminal resize, this may not work on every linux. May

            _print_porcess_page(process)

            input_config_name = _ask_for_config_name()

            input_options = _ask_for_options()

            # the command is then pass to subprocess to the process command.
            command = (
                [f"magtogoek_{process}_config"] + [input_config_name] + input_options
            )
            subprocess.run(command)
            exit()

        else:
            _print_invalid_process(valid_process)
            exit()

    ### if no argument was pass we get here.
    else:

        click.clear()
        _print_logo(logojson=logo_json_path)
        _print_doc(["Description", "Parameters", "Help"])

        input_process = _ask_for_process(valid_process)

        _print_porcess_page(input_process)

        input_config_name = _ask_for_config_name()

        input_options = _ask_for_options()

        # the command is then pass to subprocess to the process command.
        command = (
            [f"magtogoek_{input_process}_config"] + [input_config_name] + input_options
        )
        subprocess.run(command)
        exit()


@click.command("adcp")
@click.argument(
    "config_name", metavar="config_name", type=str
)  # metavar="config_name", required=True)
@click.option(
    "-i",
    "--input-files",
    # nargs=1,
    type=str,
    help="Expression identifying adcp files",
)
@click.option(
    "-o",
    "--output-file",
    nargs=1,
    type=str,
    help="Expression for output file or files name",
)
@click.option(
    "--merge/--no-merge",
    help="""Merge input into one output file.,
    Default --merge""",
    default=True,
)
@click.option(
    "-p",
    "--platform-file",
    type=str,
    help="path/to/platform_file",
    nargs=1,
)
@click.option(
    "-a",
    "--amp-thres",
    type=float,
    help="Amplitude threshold (0-255). Defaults to 0.",
    nargs=1,
)
@click.option(
    "-p",
    "--pg-thres",
    type=float,
    help="Percentage of 4 beam threshold (0-100). Defaults to 80.",
)
@click.option(
    "-c",
    "--corr-thres",
    type=float,
    help="Correlation threshold (0-255). Defaults to 64.",
    nargs=1,
)
@click.option(
    "-b",
    "--start-time",
    type=str,
    help="Remove data before this date. Fomart (YYYYMMDDHHMM).",
    nargs=1,
)
@click.option(
    "-e",
    "--end-time",
    metavar="metavar test",
    type=str,
    help="Remove data after this date. Format (YYYYMMDDHHMM).",
    nargs=1,
)
@click.pass_context
def magtogoek_adcp_config(
    ctx,
    config_name,
    input_files,
    output_file,
    merge,
    platform_file,
    amp_thres,
    pg_thres,
    corr_thres,
    start_time,
    end_time,
):
    """\033[F \033[F \033[K
    Positional argument:\n
    1 - config_name\t\t file name (path/to/file) configuration file.
    """  # \033[F \033[F \033[K deletes default click help

    _print_passed_options(ctx.params)

    config_name = _check_config_name(ctx.params["config_name"])

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
    click.echo("Help: magtogoek_config --help")


def _ask_for_config_name() -> str:
    """ckick.prompt that ask for `config_name`"""
    return click.prompt(
        click.style(
            "\nEnter a filename (path/to/file) for the config `.ini` file. ", bold=True
        )
    )


def _check_config_name(config_name: str) -> str:
    """Check if directory a file name exist.

    Ask to make the directories and to file ovewrite.

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
            "adcp": magtogoek_adcp_config,
        }[process]
    )


def _print_logo(process: str = None, logojson: str = "file/logo.json"):
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
            f"version: {magtogoek_version}".ljust(72, " ") + " config ",
            fg="green",
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
  `magtogoek_config` is a command line applications that creates a `.ini`
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
    $ magtogoek_config --help                                  (C-c C-c to quit)
    """


def _print_usage():
    return """
  Typing,

    $ magtogoek_config `process` `config_name`

  should return,

    Config file created for `process` processing -> `config_name`.ini

  Each process has specific `--optionals` arguments. Typing

    $ magtogoek_config `process`

  will bring up the `process` page, where all the `--optionals` are listed.

    $ magtogoek_config process config_name [--optionals]

  You can also type,

    $ magtogoek_config

  And follow the instructions.
"""

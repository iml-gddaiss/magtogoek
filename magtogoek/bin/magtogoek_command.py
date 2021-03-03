"""
Author: JeromeJGuay
Date: Mars 2

This module contains the command line applications.
It is not clean. But it works.

FIXME: mag vs magtogoek.
FIXME: ASK FOR OVERWRITE
FIXME: REMOVE EXENSION
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

from pathlib import Path
from magtogoek.metadata.toolbox import json2dict
from magtogoek.config_parser import make_config_file
from magtogoek.adcp.config_parser import make_adcp_parser

magtogoek_version = "0.0.1"
available_process = ["adcp"]


class GlobalHelp(click.Command):
    """Custom help for magtogoek_config"""

    def format_help(self, ctx, formatter):
        click.clear()
        _print_logo()
        click.echo(click.style("\nDescription:", fg="red"))
        click.echo(click.style(_print_description(), fg="white"))
        click.echo(click.style("\nUsage:", fg="red"))
        click.echo(click.style(_print_usage(), fg="white"))
        click.echo(click.style("\nParameters:", fg="red"))
        click.echo(click.style(_print_parameters(), fg="white"))
        click.echo(click.style("\nHelp:", fg="red"))
        click.echo(click.style(_print_help(), fg="white"))


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
    # checks if a config name was pass. This implies that a process was pass.
    if config_name:
        if process not in available_process:
            click.echo(click.style("ERROR: Invalid process", fg="red"))
            exit()

        # pass command to process sub-command
        command = [f"mag_{process}_config"] + [config_name] + list(options)
        subprocess.run(command)
        exit()

    # if no config_name was pass, checks if a process was pass.
    if process:
        if process in available_process:
            # print the process logo and help page
            click.clear()
            _print_logo(process)
            if process == "adcp":
                print_help_msg(magtogoek_adcp_config)

            # ask for a config name
            config_name = click.prompt(
                "\nEnter a file name for the config `ini` file. "
            )

            # asks for options
            click.echo("\nType options or press enter to pass:")
            options = click.prompt("\nOptions", default="")

            # pass command to process sub-command
            command = [f"mag_{process}_config"] + [config_name] + options.split(" ")
            subprocess.run(command)
            exit()
        else:
            # exit if invalid process
            click.echo(click.style("ERROR: Invalid process", fg="red"))
            click.echo("Help: mag_config --help")
            exit()

    # if no argument was pass, we get here.
    # first some prints
    click.clear()
    _print_logo()
    click.echo(click.style("\nDescription:", fg="red"))
    click.echo(click.style(_print_description(), fg="white"))
    click.echo(click.style("\nParameters:", fg="red"))
    click.echo(click.style(_print_parameters(), fg="white"))
    click.echo(click.style("\nHelp:", fg="red"))
    click.echo(click.style(_print_help(), fg="white"))

    # ask for process
    process = click.prompt(
        f"What type of data do you want to process: {available_process} "
    )
    while process not in available_process:
        click.echo(click.style("ERROR: Invalid process", fg="red"))
        process = click.prompt(
            f"\nWhat type of data do you want to process: {available_process} "
        )

    # ask for a config name
    config_name = click.prompt("\nEnter a file name for the config `ini` file. ")

    # prints process page
    click.clear()
    _print_logo(process)
    if process == "adcp":
        print_help_msg(magtogoek_adcp_config)

        # asks for options
    click.echo("\nType options or press enter to pass:")
    options = click.prompt("\nOptions:", default="")

    # pass command to process sub-command
    command = [f"mag_{process}_config"] + [config_name] + options.split(" ")
    subprocess.run(command)
    exit()


@click.command("adcp")
@click.argument("config_name", type=str)  # metavar="config_name", required=True)
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
    """"""
    for key, item in ctx.params.items():
        if item is not None:
            print(key, item)
    make_config_file(
        Path(ctx.params["config_name"]).stem + ".ini",
        sensor_type="adcp",
        kwargs=ctx.params,
    )
    exit()


def _print_parameters():
    return """
    process       Type of data to be process. Choose one of `adcp`

    config_name   Name for the configuration_file. The configuration
                  file is made in the current directory unless a path
                  is provided. ex:  `config_file` = path/to/filename"""


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


logos = json2dict(Path(__file__).parents[0] / Path("logo.json"))


def _print_logo(process=None):
    """return the string for logo.json"""
    click.echo("=" * 80)
    click.echo(click.style(logos["magtogoek"], fg="blue"))
    if process == "adcp":
        click.echo(click.style(logos["adcp"], fg="red"))
    click.echo(
        click.style(
            f"version: {magtogoek_version}".ljust(72, " ") + " config ", fg="green"
        )
    )
    click.echo("=" * 80)


def print_help_msg(command):
    """print command help"""
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))

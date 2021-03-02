#!/usr/bin/env python3
"""
author: Jérôme Guay
date: Mar. 1, 2021
version: 0.0.1 #TODO AUTO UPDATE VERSION
#TODO put the logos in a separate files.

==============================================================================
       __  ___    ____    _____ ________ ______ _____  ______ _____  __ __
      /  |/   |  /    |  / ___//__  ___// __  // ___/ / __  //  __/ / // /
     / /|  /| | / /_| | / /_ \   / /   / /_/ // /_ \ / /_/ //  __/ / _  /
    /_/ |_/ |_|/_/  |_|/_____|  /_/   /_____//_____|/_____//_____//_/ \_\.

===================================================================== -CONFIG-

Description:
  When called, magtogoek_config makes a `.ini` configuration file. The
  configuration file can then be passed to magtogoek_process.

  The created `.ini` file will contain  global and process specific parameters.
  These parameters can then be edited in a text editor or set here with the
  optional arguments.

Usage:
  In a terminal:

    $: python path/to/magtogoek_config.py process filename [-optional]

  if magtogoek_config.py is added as a bash command:

    $: magtogoek_config process filename [-optionals]

Help:
  magotogoek_config requires 2 positional arguments:

    $: magtogoek_config process filename

  For global help:

    $: magtogoek_config -h

  For help on a process optional arguments:

    $: magtogoek_config process -h

"""
import configparser
import argparse
import sys
import typing as tp
from pathlib import Path

from magtogoek.toolbox import query_yes_no
from magtogoek.config_parser import make_config_file
from magtogoek.adcp.config_parser import make_adcp_parser


def main():
    """parser for the magtogoek_config application"""
    usage_message = _title() + "\n\n" + _description() + "\n\n" + _usage() + "\n\n"
    parser = CustomArgumentParser(
        prog="magtogoek_config",
        usage=usage_message,
        epilog="".ljust(79, "="),
        formatter_class=CustomHelpFormatter,
    )

    subparser = parser.add_subparsers(
        metavar="process",
        dest="process",
        help="",
        required=True,
    )

    # Set parser for specific process
    adcp_parser = make_adcp_parser(subparser, _title())

    # parse
    args = parser.parse_args()

    # Ask for overwriting if file name exists.
    config_name = args.config_name
    if Path(config_name).is_file:
        if not query_yes_no(
            "A file with this name already exists. Overwrite ?",
            default="yes",
        ):
            print("magtogoek_config aborded.")
            exit()

    # Removes `ini` extension, if given, but keeps any others.
    if Path(config_name).suffix == ".ini":
        config_name = Path(config_name).with_suffix("")

    # makes the configuration files
    make_config_file(Path(config_name).stem + ".ini", sensor_type=args.process, **args)

    print(f"Config file created for {args.process} processing -> {config_name}.ini")


def _title(version="0.0.1"):
    return (
        """
==============================================================================
       __  ___    ____    _____ ________ ______ _____  ______ _____  __ __
      /  |/   |  /    |  / ___//__  ___// __  // ___/ / __  //  __/ / // /
     / /|  /| | / /_| | / /_ \   / /   / /_/ // /_ \ / /_/ //  __/ / _  /
    /_/ |_/ |_|/_/  |_|/_____|  /_/   /_____//_____|/_____//_____//_/ \_\.

===================================================================== -CONFIG-"""
        + f"\nversion: {version}\n"
    )


def _description():
    return """Description:
  When called, magtogoek_config makes a `.ini` configuration file. The
  configuration file can then be passed to magtogoek_process.

  The created `.ini` file will contain  global and process specific parameters.
  These parameters can then be edited in a text editor or set here with the
  optional arguments. The configuration file is created in the current directory
  unless a path  is provided: config_file = path/to/filename"""


def _usage():
    return """Usage:
  In a terminal:

    $: python path/to/magtogoek_config.py process filename --optional

  if magtogoek_config.py is added as a bash command:

    $: magtogoek_config process filename [-optionals]

  for help on a process optional arguments:

    $: magtogoek_config process -h
"""


def _help():
    return """Help:
  magotogoek_config requires 2 positional arguments: process and config_name.

    $: magtogoek_config process config_name

  For global help:

    $: magtogoek_config -h

  For help on a process optional arguments:

    $: magtogoek_config process -h

  Available process : adcp"""


class CustomHelpFormatter(argparse.HelpFormatter):
    """
    This formats the help section for magtogoek_config when
    no process is called with -h. When [process] [-h] is called,
    formating from process sub-package are used.
    NOTE: This is not well done.
    """

    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = ""
        return super(CustomHelpFormatter, self).add_usage(
            usage, actions, groups, prefix
        )

    def _format_action(self, action):
        if type(action) == argparse._SubParsersAction:
            # inject new class variable for subcommand formatting
            subactions = action._get_subactions()
            invocations = [self._format_action_invocation(a) for a in subactions]
            self._subcommand_max_length = max(len(i) for i in invocations)

        if type(action) == argparse._SubParsersAction._ChoicesPseudoAction:
            # format subcommand help line
            subcommand = self._format_action_invocation(action)  # type: str
            width = self._subcommand_max_length
            help_text = ""
            if action.help:
                help_text = self._expand_help(action)
            return "{}".format(subcommand, width=width)

        elif type(action) == argparse._SubParsersAction:
            # process subcommand help section
            hspace = 20
            msg = "  1 - process".ljust(hspace, " ")
            msg += "Available process ["
            for subaction in action._get_subactions():
                msg += self._format_action(subaction) + ", "
            msg += "]\n"
            msg += (
                "  2 - config_name".ljust(hspace, " ")
                + "Name for the configuration file. The config file is\n"
                + "".ljust(hspace, " ")
                + "created in the current directory unless a path is\n"
                + "".ljust(hspace, " ")
                + "provided: config_name = path/to/filename"
            )
            return msg
        else:
            return super(CustomHelpFormatter, self)._format_action(action)


class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(_title() + "\n" + _description() + "\n" + _help())
        self.exit(2, "Error: Required positional arguments: process  config_name\n")


if __name__ == "__main__":
    main()

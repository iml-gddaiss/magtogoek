"""
author: Jérôme Guay
date: Feb. 22, 2021


Functions in this script is called by magtogoek/config_parser
and magtogoek/magtogoek_config.

Some of this module is based on https://github.com/jeanlucshaw/adcp2c.

This script strores functions to make the adcp template.

#TODO add more description about the QC.
#TODO Make an overwrite functions
#TODO overwrite should be with process
"""
import configparser
import typing as tp
import getpass
import argparse
import sys


def make_adcp_parser(
    subparser: tp.Type[argparse._SubParsersAction],
    usage: str,
) -> tp.Type[argparse.ArgumentParser]:
    """parser for adcp config"""

    adcp_parser = subparser.add_parser(
        "adcp",
        prog="magtogoek_config",
        usage=_adcp_title(),
        help="configuration files for adcp processing.",
        formatter_class=CustomHelpFormatter,
    )

    adcp_parser.add_argument(
        "config_name",
        metavar="2 - config_name",
        type=str,
        help="""Name for the configuration file.
                The config file is created in the current
                directory unless a path  is provided:
                config_file = path/to/filename""",
    )
    # identifies files
    adcp_parser.add_argument(
        "-i",
        "--input_files",
        metavar="",
        help="Expression identifying adcp files",
        nargs="+",
    )
    # adcp type
    adcp_parser.add_argument(
        "-s",
        "--sonar",
        metavar="",
        help="""String designating type of adcp. This
                        is fed to CODAS Multiread or switches to the RTI
                        binary reader. Must be one
                        of `wh`, `os`, `bb`, `nb` or `sw`""",
    )
    # deployment nickname
    adcp_parser.add_argument(
        "-o",
        "--output-file",
        metavar="",
        help="""Expression for output file or files name""",
        nargs="+",
    )
    adcp_parser.add_argument(
        "-m",
        "--merge-output-file",
        metavar="",
        help="""Merge input into one output file.""",
        nargs="+",
    )
    adcp_parser.add_argument(
        "-p",
        "--platform-file",
        metavar="",
        help="""path/to/platform_file""",
        nargs="+",
    )

    adcp_parser.add_argument(
        "-a",
        "--amp-thres",
        metavar="",
        type=float,
        help="Amplitude threshold (0-255). Defaults to 0.",
    )
    adcp_parser.add_argument(
        "-c",
        "--corr-thres",
        metavar="",
        type=float,
        help="Correlation threshold (0-255). Defaults to 64.",
    )

    adcp_parser.add_argument(
        "-b",
        "--start-time",
        metavar="",
        type=str,
        help="Remove data before this date. Fomart (YYYYMMDDHHMM).",
    )
    adcp_parser.add_argument(
        "-e",
        "--end-time",
        metavar="",
        type=str,
        help="Remove data after this date. Format (YYYYMMDDHHMM).",
    )
    return adcp_parser


def adcp_config(
    config: tp.Type[configparser.ConfigParser], linewidth: int, kwargs: tp.Dict = None
) -> None:
    """set adcp config arguments for configparser"""
    config["ADCP_PROCESSING"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| yearbase: year that the sampling started. ex: `1970`".ljust(linewidth, " ")
        + "|": None,
        ";| adcp_orientation: `down` or `up`. (horizontal no supported)".ljust(
            linewidth, " "
        )
        + "|": None,
        ";| sonar:  Must be one of `wh`, `os`, `bb`, `nb` or `sw".ljust(linewidth, " ")
        + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
        "\t yearbase": "",
        "\t adcp_orientation": "",
        "\t sonar": "",
    }
    config["ADCP_QUALITY_CONTROL"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| If quality_control is `False`, no quality control is carried out .".ljust(
            linewidth, " "
        )
        + "|": None,
        ";| Blanks are omitted or set False.".ljust(linewidth, " ") + "|": None,
        ";| Trims format `YYYYMMDDHHMMSS`".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
        "\t quality_control": True,
        "\t amplitude_threshold": 30,
        "\t correlation_threshold": 64,
        "\t percentgood_threshold": 90,
        "\t horizontal_velocity_threshold": 5,
        "\t vertical_velocity_threshold": 5,
        "\t error_velocity_threshold": 5,
        "\t roll_threshold": 20,
        "\t pitch_threshold": 20,
        "\t side_lobe": True,
        "\t remove_platform_velocity": True,
        "\t trim_leading_start": "",
        "\t trim_trailing_end": "",
    }
    config["ADCP_OUTPUT"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Set True or False. (FIXME)".ljust(linewidth, " ") + "|": None,
        ";| If BODC_variables_name False, comon variable names are used.".ljust(
            linewidth, " "
        )
        + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
        "\t BODC_variable_name": True,
        "\t drop_percent_good": True,
        "\t drop_correlation": True,
        "\t drop_intensity": True,
        "\t make_figures": True,
        "\t make_log": True,
    }

    return _set_parameters(config, kwargs)


def _set_parameters(config, kwargs=None):
    """EMPTY PIPE"""
    return config


def _adcp_title(version="0.0.1"):
    return (
        """
===============================================================================
       __  ___    ____    _____ ________ ______ _____  ______ _____  __ __
      /  |/   |  /    |  / ___//__  ___// __  // ___/ / __  //  __/ / // /
     / /|  /| | / /_| | / /_ \   / /   / /_/ // /_ \ / /_/ //  __/ / _  /
    /_/ |_/ |_|/_/  |_|/_____|  /_/   /_____//_____|/_____//_____//_/ \_\.
                          ____    ____   ______  ______
                         /    |  / __ \ /  ___/ / __  /
                        / /_| | /  _/ //  /__  / ____/
                       /_/  |_|/_____//______\/_/

                    -Supports Teledyne and RowTech files
===================================================================== -CONFIG-"""
        + f"\nversion: {version}\n"
        + "\n Usage:\n"
        + "\n  $ magtogoek_config adcp ..."
    )


class CustomHelpFormatter(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = ""
        return super(CustomHelpFormatter, self).add_usage(
            usage, actions, groups, prefix
        )

    def _format_action_invocation(self, action):
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            default = 80
            (metavar,) = self._metavar_formatter(action, default)(1)
            return metavar

        else:
            parts = []

            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            else:
                default = self._get_default_metavar_for_optional(action)
                args_string = self._format_args(action, default)
                for option_string in action.option_strings[:-1]:
                    parts.append("%s" % (option_string,))
                parts.append("%s %s" % (action.option_strings[-1], args_string))
            return ", ".join(parts)

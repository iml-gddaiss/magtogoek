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


def adcp_configparser(
    config: tp.Type[configparser.ConfigParser], linewidth: int, options: tp.Dict = None
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
        """;| GPS_file: path/to/netcdf4 file containing the gps data, `longitude`, `latitude`, of the platform.\n
        If provided, will be used instead of GPS data in the adcp file. (optional) """.ljust(
            linewidth, " "
        )
        + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
        "\t yearbase": "",
        "\t adcp_orientation": "",
        "\t sonar": "",
        "\t GPS_file:": "",
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
        "\t amplitude_threshold": 0,
        "\t correlation_threshold": 64,
        "\t percentgood_threshold": 90,
        "\t horizontal_velocity_threshold": 5,
        "\t vertical_velocity_threshold": 5,
        "\t error_velocity_threshold": 5,
        "\t roll_threshold": 20,
        "\t pitch_threshold": 20,
        "\t side_lobe_correction": True,
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
        "\t drop_amplitude": True,
        "\t make_figures": True,
        "\t make_log": True,
    }

    return _set_parameters(config, options)


def _set_parameters(config, options=None):
    """EMPTY PIPE TODO"""
    return config

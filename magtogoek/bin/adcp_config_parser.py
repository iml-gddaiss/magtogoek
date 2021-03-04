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
        ";| GPS_file: path/to/netcdf4 containing the gps track,".ljust(linewidth, " ")
        + "|": None,
        ";| `longitude` and `latitude`, of the platform. If provided,".ljust(
            linewidth, " "
        )
        + "|": None,
        ";| will be used instead of GPS data in the adcp file.(optional) ".ljust(
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
        "\t platform_motion_correction": True,
        "\t trim_leading_data": "",
        "\t trim_trailing_data": "",
    }
    config["ADCP_OUTPUT"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Set True or False. (FIXME)".ljust(linewidth, " ") + "|": None,
        ";| If bodc_name False, generic variable names are used.".ljust(linewidth, " ")
        + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
        "\t merge_output_file": True,
        "\t bodc_name": True,
        "\t drop_percent_good": True,
        "\t drop_correlation": True,
        "\t drop_amplitude": True,
        "\t make_figures": True,
        "\t make_log": True,
    }

    return config


def _set_parameters(config, options=None):
    """EMPTY PIPE TODO"""
    return config


base_parser_args = dict(
    input_files=("input_files", str),
    netcdf_output=("netcdf_output", str),
    odf_output=("odf_output", str),
    platform_file=("platform_file", str),
)

adcp_command_converts = dict(
    GPS_file=("gps", str),
    sonar=("sonar", str),
    yearbase=("yearbase", str),
    adcp_orientation=("up", lambda x: "up" * x + "down" * (not x)),
    trim_leading_data=("start_time", str),
    trim_trailling_data=("end_time", str),
    quality_control=("qc", bool),
    amplitude_threshold=("amplitude_threshold", float),
    percentgood_threshold=("percentgood_threshold", float),
    correlation_threshold=("correlation_threshold", float),
    horizontal_velocity_threshol=("horizontal_velocity_threshol", float),
    vertical_velocity_threshold=("vertical_velocity_threshold", float),
    error_velocity_threshold=("error_velocity_threshold", float),
    side_lobe_correction=("side_lobe", bool),
    pitch_threshold=("pitch_threshold", float),
    roll_threshold=("roll_threshold", float),
    platform_motion_correction=("m_corr", bool),
    merge_output_file=("merge", bool),
    bodc_name=("bodc_name", bool),
    drop_percent_good=("drop_pg", bool),
    drop_correlation=("drop_corr", bool),
    drop_amplitude=("drop_amp", bool),
    make_figures=("mk_fig", bool),
    make_log=("mk_log", bool),
)

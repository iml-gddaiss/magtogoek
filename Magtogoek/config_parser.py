#!/usr/bin/python
"""
author: Jérôme Guay
date: Feb. 22, 2021

File to be run in command line:

$: config_parser filename sensor_type

[-h] for help.

TODO move adcp section to adcp sub-module.

"""
import configparser
import argparse
import typing as tp
import pandas as pd
import getpass

if __name__ == "__main__":
    from config_parser import make_config_file  # probably not good practice TODO

    parser = argparse.ArgumentParser(usage=__doc__)

    parser.add_argument(
        "process",
        metavar="1 - process",
        help="""str: Type of the data to process.
        Must be of one: `adcp`""",
    )
    parser.add_argument(
        "filename",
        metavar="2 - filename",
        default="process_config",
        help="""str: name of the config file.
        The config file is place is current the
        directory unless a path is provided.""",
    )
    args = parser.parse_args()

    # remove any extension and check for multiple `.`.
    filename = args.filename.split(".")
    if len(filename) > 2:
        raise parser.error("filename invalid, more than one `.`")
    else:
        filename = filename[0]

    # verify if process is valid.
    valid_process = ["adcp"]
    if args.process not in valid_process:
        raise parser.error("Invalid process. Must be one of : `adcp`")

    make_config_file(filename + ".ini", sensor_type=args.process)
    print(f"Config file created for {args.process}  -> {filename}.ini")


def make_config_file(filename: str, sensor_type: str) -> None:
    """make empty config_files in local directory"""
    linewidth = 70

    config = _init_config(sensor_type, linewidth)
    _input_files(config, linewidth)
    _output_files(config, linewidth)

    if sensor_type == "adcp":
        _adcp_config(config, linewidth)
    else:
        print("Invalid sensor_type. Must be one of : `adcp`")
        exit()

    _project(config, linewidth)
    _cruise(config, linewidth)
    _netcdf_cf(config, linewidth)
    _gloabal_attributes(config, linewidth)
    _additional_global_attributes(config, linewidth)

    configparser2ini(config, filename)


def _init_config(
    sensor_type: str, linewidth: int
) -> tp.Type[configparser.ConfigParser]:
    """init configparser"""
    date = pd.Timestamp.now().strftime("%Y-%m-%d")
    user = getpass.getuser()
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str
    config["HEADER"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        f";| Configurations file for {sensor_type} data processing".ljust(
            linewidth, " "
        )
        + "|": None,
        f";| Created on {date}".ljust(linewidth, " ") + "|": None,
        f";| By {user}".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
    }
    return config


def _input_files(config: tp.Type[configparser.ConfigParser], linewidth: int):
    config["INPUT"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| data_file: (file name) Data to be process.".ljust(linewidth, " ")
        + "|": None,
        ";| platform file: (file name) Can be omitted.".ljust(linewidth, " ")
        + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
        "\t data_file": "",
        "\t platform_file": "",
    }


def _output_files(config: tp.Type[configparser.ConfigParser], linewidth: int):
    config["OUTPUT"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        "; (files name) Leave blank for `False`.".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
        "\t netcdf_output": "",
        "\t odf_output": "",
    }


def _netcdf_cf(config: tp.Type[configparser.ConfigParser], linewidth: int):
    """add netcdf config"""
    config["NETCDF_CF"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Global attibutes for CF conventions".ljust(linewidth, " ") + "|": None,
        ";| Blanks are omitted.".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
        "\t Conventions": "CF 1.8",
        "\t title": "",
        "\t institution": "",
        "\t summary": "",
        "\t references": "https://github.com/JeromeJGuay/magtogoek",
        "\t comments": "",
        "\t naming_authority": "BODC, SDC, CF, MEDS",
    }


def _project(config: tp.Type[configparser.ConfigParser], linewidth: int):
    config["PROJECT"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Global attributes for project".ljust(linewidth, " ") + "|": None,
        ";| Blanks are omitted.".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
        "\t project": "",
        "\t sea_name": "",
        "\t sea_code": "",
    }


def _cruise(config: tp.Type[configparser.ConfigParser], linewidth: int):
    config["CRUISE"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Global attributes for cruise".ljust(linewidth, " ") + "|": None,
        ";| Blanks are omitted".ljust(linewidth, " ") + "|": None,
        ";| chief_scientist: overwrites the value in the platform file.".ljust(
            linewidth, " "
        )
        + "|": None,
        ";| Date format: YYYY-MM-DDTHH:MM:SS FIXME ".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
        "\t country_institue_code": "",
        "\t cruise_number": "",
        "\t organization": "",
        "\t chief_scientist": "",
        "\t start_date": "",
        "\t end_date": "",
    }


def _gloabal_attributes(config: tp.Type[configparser.ConfigParser], linewidth: int):
    config["GLOBAL_ATTRIBUTES"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Global attributes ".ljust(linewidth, " ") + "|": None,
        ";| Blanks are omitted".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
        "\t date_created": "",
        "\t data_type": "",
        "\t data_subtype": "",
        "\t country_code": "",
        "\t keywords": "",
        "\t publisher_email": "",
        "\t creator_type": "",
        "\t publisher_name": "",
        "\t keywords_vocabulary": "",
        "\t standard_name_vocabulary": "CF v.52",  # Note update ?
        "\t aknowledgment": "",
    }


def _additional_global_attributes(
    config: tp.Type[configparser.ConfigParser], linewidth: int
):
    config["ADDITIONAL_GLOBAL_ATTRIBUTES"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Insert addittional attributes below.".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
    }


def _adcp_config(config: tp.Type[configparser.ConfigParser], linewidth: int):
    """set PROCESSING for adcp"""
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
        ";| Threshold left blank are omitted.".ljust(linewidth, " ") + "|": None,
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
    }
    config["ADCP_OUTPUT"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Set True or False.".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
        "\t drop_percent_good": True,
        "\t drop_correlation": True,
        "\t drop_intensity": True,
        "\t make_figures": True,
        "\t make_log": True,
    }
    return config


def configparser2ini(config: tp.Type[configparser.ConfigParser], filename: str):
    """make ini file"""
    with open(filename, "w") as configfile:
        config.write(configfile)

"""
author: Jérôme Guay
date: Feb. 22, 2021

This script is called by magtogoek_config.py

This script strores functions to make the basic templates
and imports specific templates to make the configparser.
"""
import configparser
import typing as tp
import pandas as pd
import getpass
from magtogoek.adcp.config_parser import adcp_config


def make_config_file(filename: str, sensor_type: str, kwargs) -> None:
    """make empty config_files.

    parameters:
    -----------
    filename:
        name of the config(.ini) file

    sensor_type:
        used to return sensor_type config.
    """
    linewidth = 70  # width of the .ini comments sections

    config = _init_config(sensor_type, linewidth)
    _input_files(config, linewidth)
    _output_files(config, linewidth)

    if sensor_type == "adcp":
        adcp_config(config, linewidth, kwargs)
    else:
        print("Invalid sensor_type. Must be one of: `adcp`")
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
    """initialize the configparser"""
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


def _set_parameters(config, kwargs):
    """EMPTY PIPE"""
    return config


def configparser2ini(config: tp.Type[configparser.ConfigParser], filename: str):
    """make .ini file"""
    with open(filename, "w") as configfile:
        config.write(configfile)

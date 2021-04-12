"""
author: Jérôme Guay
date: March 4, 2021

This make_configparser is called by magtogoek_command.py
    $ mtgk config ...

This modules also contains the sections and default parameters values for the configparsers.


NOTE update ?
NOTE: More comments should be added in the configparser files.
NOTE: Missing,fonctions to open the config files.
NOTE: Make a class ? Config(config_name, sensor_type=None).{update(options), .load(), .save()}

INPUT:
Expression identifying the file or files to be process.
platform file: (file name) Can be omitted.

OUTPUT:
Expression for odf and netcdf output files names.
Leave blank for `False`.
If both are left blank, a netcdf file with be made with `input_files`+'mtgk.nc'

ADCP PROCESSING:
-yearbase: year that the sampling started. ex: `1970`
-adcp_orientation: `down` or `up`. (horizontal no supported)
-sonar:  Must be one of `wh`, `os`, `bb`, `nb` or `sw`
-GPS_file: path/to/netcdf4 containing the gps track,
    `longitude` and `latitude`, of the platform. If provided,
    will be used instead of GPS data in the adcp file.(optional).

ADCP_QUALITY_CONTROL:
If quality_control is `False`, no quality control is carried out.
Blanks are omitted or set False.
Trims format `YYYYMMDDTHHMMSS`

ADCP_OUTPUT:
Set True or False.
If bodc_name False, generic variable names are used.
"""

import getpass
import typing as tp
from configparser import ConfigParser

from pandas import Timestamp

BASIC_CONFIG = dict(
    HEADER={
        "sensor_type": "none",
        "made_by": getpass.getuser(),
        "last_updated": Timestamp.now().strftime("%Y-%m-%d"),
    },
    INPUT={
        "input_files": "",
        "platform_file": "",
        "platform_id": "",
        "instrument_id": "",
    },
    OUTPUT={"netcdf_output": "", "odf_output": ""},
    NETCDF_CF={
        "Conventions": "CF 1.8",
        "title": "",
        "institution": "",
        "summary": "",
        "references": "https://github.com/JeromeJGuay/magtogoek",
        "comments": "",
        "naming_authority": "BODC, SDC, CF, MEDS ; comment",
    },
    PROJECT={
        "project": "",
        "sea_name": "",
        "sea_code": "",
    },
    CRUISE={
        "country_institue_code": "",
        "cruise_number": "",
        "organization": "",
        "chief_scientist": "",
        "start_date": "",
        "end_date": "",
    },
    GLOBAL_ATTRIBUTES={
        "date_created": "",
        "date_created": "",
        "data_type": "",
        "data_subtype": "",
        "country_code": "",
        "keywords": "",
        "publisher_email": "",
        "creator_type": "",
        "publisher_name": "",
        "keywords_vocabulary": "",
        "standard_name_vocabulary": "CF v.52",
        "aknowledgment": "",
    },
)

ADCP_CONFIG = dict(
    ADCP_PROCESSING={
        "yearbase": "",
        "adcp_orientation": "down",
        "sonar": "",
        "navigation_file": "",
        "magnetic_declination": "",
        "sensor_depth": "",
    },
    ADCP_QUALITY_CONTROL={
        "quality_control": True,
        "amplitude_threshold": 0,
        "percentgood_threshold": 64,
        "correlation_threshold": 90,
        "horizontal_velocity_threshold": 5,
        "vertical_velocity_threshold": 5,
        "error_velocity_threshold": 5,
        "sidelobes_correction": True,
        "bottom_depth": "",
        "pitch_threshold": 20,
        "roll_threshold": 20,
        "leading_trim": "",
        "trailing_trim": "",
        "motion_correction_mode": "bt",
    },
    ADCP_OUTPUT={
        "merge_output_files": True,
        "bodc_name": True,
        "drop_percent_good": True,
        "drop_correlation": True,
        "drop_amplitude": True,
        "make_figures": True,
        "make_log": True,
    },
)


def make_configfile(filename: str, sensor_type: str, updated_params: tp.Dict = None):
    """make a configfile with default and update it if `updated_params` are passed"""

    # geting the default config as dict
    config_dict = _get_config_default(sensor_type)

    # Building the parser
    parser = ConfigParser()
    parser.optionxform = str
    for section, params in config_dict.items():
        parser.add_section(section)
        for param, value in params.items():
            parser[section][param] = str(value)

    # Overwrite the default values with `updated_params`.
    if updated_params is not None:
        _update_config(parser, updated_params)

    # Writing
    with open(filename, "w") as f:
        parser.write(f)


def load_configfile(filename: str, updated_params: tp.Dict = None):
    """load a configfile and update it if `updated_params` are passed"""
    # Opening the configfile
    parser = ConfigParser()
    parser.optionxform = str
    parser.read(filename)

    # Overwrite the config values with `updated_params`.
    if updated_params is not None:
        _update_config(parser, updated_params)

    # Overiting the configfile with the new values
    with open(filename, "w") as f:
        parser.write(f)

    return parser._sections


def _update_config(parser: tp.Type[ConfigParser], updated_params: tp.Dict):
    """Overwrite the default values with `updated_params`"""
    for section, params in updated_params.items():
        for param, value in params.items():
            parser[section][param] = str(value)


def _get_config_default(sensor_type: str):
    """FIXME"""
    if sensor_type == "adcp":
        config_dict = {**BASIC_CONFIG, **ADCP_CONFIG}
    config_dict["HEADER"]["sensor_type"] = sensor_type

    return config_dict

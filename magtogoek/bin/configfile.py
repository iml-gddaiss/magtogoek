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


class ConfigFileError(Exception):
    pass


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
        "sensor_id": "",
    },
    OUTPUT={"netcdf_output": "", "odf_output": ""},
    NETCDF_CF={
        "Conventions": "CF 1.8",
        "title": "",
        "institution": "",
        "summary": "",
        "references": "https://github.com/JeromeJGuay/magtogoek",
        "comments": "",
        "naming_authority": "BODC, SDC, CF, MEDS",
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
ADCP_CONFIG_TYPE = dict(
    ADCP_PROCESSING={
        "yearbase": int,
        "adcp_orientation": str,
        "sonar": str,
        "navigation_file": str,
        "magnetic_declination": float,
        "sensor_depth": float,
    },
    ADCP_QUALITY_CONTROL={
        "quality_control": bool,
        "amplitude_threshold": float,
        "percentgood_threshold": float,
        "correlation_threshold": float,
        "horizontal_velocity_threshold": float,
        "vertical_velocity_threshold": float,
        "error_velocity_threshold": float,
        "sidelobes_correction": bool,
        "bottom_depth": float,
        "pitch_threshold": float,
        "roll_threshold": float,
        "leading_trim": str,
        "trailing_trim": str,
        "motion_correction_mode": str,
    },
    ADCP_OUTPUT={
        "merge_output_files": bool,
        "bodc_name": bool,
        "drop_percent_good": bool,
        "drop_correlation": bool,
        "drop_amplitude": bool,
        "make_figures": bool,
        "make_log": bool,
    },
)


def make_configfile(filename: str, sensor_type: str, config_params: tp.Dict = None):
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

    # Overwrite the default values with the `updated_params`.
    if config_params:
        _update_config(parser, config_params)

    # Writing
    with open(filename, "w") as f:
        parser.write(f)


def load_configfile(filename: str, updated_params: tp.Dict = None):
    """load a configfile.
    Returns parser as a dictionnary with the appropriate types.
    - Check for missing sections and options.
    - Updates it if `updated_params` are passed"""
    # Opening the configfile
    parser = ConfigParser()
    parser.optionxform = str
    parser.read(filename)

    # Check integrity of the configfile
    _check_config_missing(parser)

    # Overwrite the config values with `updated_params`.
    if updated_params:
        _update_config(parser, updated_params)
        # Overwriting the configfile with the new values
        with open(filename, "w") as f:
            parser.write(f)

    parser = parser._sections

    _convert_options_type(parser)

    return parser


def _check_config_missing(parser: tp.Type[ConfigParser]):
    """Check for missing sections or options compared to the expected parser

    Adds the options or section if needed
    """
    if parser.has_option("HEADER", "sensor_type"):
        sensor_type = parser["HEADER"]["sensor_type"]
        if not sensor_type:
            raise ConfigFileError("`sensor_type` value missing")
    else:
        raise ConfigFileError("`HEADER/sensor_type` Missing from configfile.")

    expected_parser = _get_config_default(sensor_type)

    for section, options in expected_parser.items():
        if not parser.has_section(section):
            parser.add_section(section)
        for option in options.keys():
            if not parser.has_option(section, option):
                parser[section][option] = expected_parser[section][option]


def _convert_options_type(parser: tp.Dict):
    """Convert some config options to the right type for processing.
    Notes
    -----
    Add more sensor_type options for each different sensor processing
    """
    sensor_type = parser["HEADER"]["sensor_type"]

    for section, options in parser.items():
        for option in options.keys():
            if parser[section][option] == "":
                parser[section][option] = None

    if sensor_type == "adcp":
        for section, options in ADCP_CONFIG_TYPE.items():
            for option in options:
                if parser[section][option]:
                    option_value = parser[section][option]
                    option_type = ADCP_CONFIG_TYPE[section][option]
                    parser[section][option] = option_type(parser[section][option])


def _get_config_default(sensor_type: str):
    """FIXME"""
    if sensor_type == "adcp":
        config_dict = {**BASIC_CONFIG, **ADCP_CONFIG}
    config_dict["HEADER"]["sensor_type"] = sensor_type

    return config_dict


def _update_config(parser: tp.Type[ConfigParser], updated_params: tp.Dict):
    """Overwrite the default values with `updated_params`"""
    for section, params in updated_params.items():
        for param, value in params.items():
            parser[section][param] = str(value)

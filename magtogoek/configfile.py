"""
author: Jérôme Guay
date: March 4, 2021

This make_configparser is called by magtogoek_command.py
    $ mtgk config ...

This modules also contains the sections and default parameters values for the configparsers.


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

ADCP_QUALITY_CONTROL:
If quality_control is `False`, no quality control is carried out.
Blanks are omitted or set False.

ADCP_OUTPUT:
Set True or False.
If bodc_name False, generic variable names are used.
FIXME
"""

import getpass
import typing as tp
from configparser import ConfigParser

from pandas import Timestamp


class ConfigFileError(Exception):
    pass


SENSOR_TYPES = ["adcp"]

BASIC_CONFIG = dict(
    HEADER={
        "sensor_type": "",
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
        "source": "",
    },
    PROJECT={
        "project": "",
        "sea_name": "",
        "sea_code": "",
    },
    CRUISE={
        "country_institue_code": "",
        "cruise_number": "",
        "cruise_name": "",
        "organization": "",
        "chief_scientist": "",
        "start_date": "",
        "end_date": "",
        "envent_number": "",
    },
    GLOBAL_ATTRIBUTES={
        "date_created": "",
        "data_type": "",
        "data_subtype": "",
        "cdm_data_type": "",
        "country_code": "",
        "publisher_email": "",
        "creator_type": "",
        "publisher_name": "",
        "keywords": "",
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
        "keep_bt": True,
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
ADCP_CONFIG_TYPES = dict(
    ADCP_PROCESSING={
        "yearbase": int,
        "adcp_orientation": str,
        "sonar": str,
        "navigation_file": str,
        "magnetic_declination": float,
        "sensor_depth": float,
        "keep_bt": bool,
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

    - Add the missing expected sections and options with empty string as value.
    - Updates the value if dictionnary is passed as `updated_params`.
    - saves the edited configuration files.
    - convert the options from string to the correct type for processing.

    """

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

    - Adds the options or section if needed with empty string as value.

    Notes
    -----
    This prevents missing key error later in the processing without needing
    to add tons of conditionnal statements.

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
                parser[section][option] = ""


def _convert_options_type(parser: tp.Dict):
    """Convert some config options to the right type for processing.

    - Replace empty string  by `None`.
    - Convert the sensor specific configuration parameters values to the right
    data type, skipping `None` value set previously.
    - Anything that should be a boolean and not a string in ['True','true','1'] is set to
    `False`.

    Raises
    ------
    ConfigFileError :
        Error are rised if the options value cannot be converted to the right type.
        (str to int or float)

    Notes
    -----
    Setting options to `None` is equivalent to `False` for later processing but does not
    imply that the expected value is a boolean.

    There should be additinal sensor_type options for each different sensor processing
    """
    sensor_type = parser["HEADER"]["sensor_type"]

    for section, options in parser.items():
        for option in options.keys():
            if parser[section][option] == "":
                parser[section][option] = None
            if option == "input_files":
                parser[section][option] = _format_string_sequence_to_list(
                    parser[section][option]
                )

    if sensor_type == "adcp":
        config_types = ADCP_CONFIG_TYPES
    else:
        raise ConfigFileError(
            f"sensor_type {sensor_type} is invalid. Must be one of {SENSOR_TYPES}"
        )

    for section, options in config_types.items():
        for option in options:
            if parser[section][option]:
                if config_types[section][option] == bool:
                    parser[section][option] = (
                        True
                        if parser[section][option] in ["True", "true", "1"]
                        else False
                    )
                if config_types[section][option] == int:
                    try:
                        parser[section][option] = int(parser[section][option])
                    except ValueError:
                        raise ConfigFileError(
                            f"{section}/{option} value, {parser[section][option]}, is invalid. The expected value is an integer."
                        )

                if config_types[section][option] == float:
                    try:
                        parser[section][option] = float(parser[section][option])
                    except ValueError:
                        raise ConfigFileError(
                            f"{section}/{option} value, {parser[section][option]}, is invalid. The expected value is an float."
                        )


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


def _format_string_sequence_to_list(sequence: str) -> tp.List:
    """Decode string containing a sequence of value.

    The sequence can be between brakets, parenthesis or nothing
    and have comma, colon, semi-colon or spaces as separators.

    Example
    -------
     _format_string_list'(arg1, arg2, arg3)' -> [arg1 arg2 arg3]

    """
    stripped = sequence.split("(")[-1].split("[")[-1].split("]")[0].split(")")[0]

    for sep in (":", ";", " ", "\n"):
        comma_formated = stripped.replace(sep, ",")

    return [s for s in comma_formated.split(",") if s != ""]

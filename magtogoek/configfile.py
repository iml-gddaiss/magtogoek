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

import ast
import getpass
import typing as tp
from collections import namedtuple
from configparser import ConfigParser

from pandas import Timestamp


class ConfigFileError(Exception):
    pass


TRUE_VALUES = ["true", "True", "1"]
SENSOR_TYPES = ["adcp"]

option_infos = namedtuple(
    "option_infos",
    ("dtype", "defaults", "nargs", "nargs_min", "nargs_max"),
    defaults=[None] * 5,
)


BASIC_CONFIG = dict(
    HEADER={
        "sensor_type": "",
        "made_by": getpass.getuser(),
        "last_updated": Timestamp.now().strftime("%Y-%m-%d"),
    },
    INPUT={"input_files": "", "platform_file": "", "platform_id": "", "sensor_id": "",},
    OUTPUT={"netcdf_output": "", "odf_output": "",},
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
    PROJECT={"project": "", "sea_name": "", "sea_code": "",},
    CRUISE={
        "country_institute_code": "",
        "cruise_number": "",
        "cruise_name": "",
        "cruise_description": "",
        "organization": "",
        "chief_scientist": "",
        "start_date": "",
        "end_date": "",
        "event_number": "",
        "event_qualifier1": "",
        "event_qualifier2": "",
        "event_comments": "",
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
        "leading_trim": "",
        "trailing_trim": "",
        "sensor_depth": "",
        "depth_range": "",
        "bad_pressure": "",
        "magnetic_declination": "",
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
        "motion_correction_mode": "bt",
    },
    ADCP_OUTPUT={
        "merge_output_files": True,
        "bodc_name": True,
        "force_platform_metadata": False,
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
        "leading_trim": str,
        "trailing_trim": str,
        "sensor_depth": float,
        "depth_range": {"type": float, "exacly": None, "min": 0, "max": 2},
        "bad_pressure": bool,
        "magnetic_declination": float,
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
        "motion_correction_mode": str,
    },
    ADCP_OUTPUT={
        "merge_output_files": bool,
        "bodc_name": bool,
        "force_platform_metadata": bool,
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


def load_configfile(filename: str, updated_params: tp.Dict = None) -> dict:
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
    # Add any missing options in the configfile and adds them
    _check_config_missing(parser)

    # Overwrite the config values with `updated_params`.
    if updated_params:
        _update_config(parser, updated_params)
        # Overwriting the configfile with the new values
        with open(filename, "w") as f:
            parser.write(f)

    configuration = {}
    configuration.update(parser._sections)

    _format_input_output_section(configuration)
    _set_empty_field_to_none(configuration)
    _format_sensor_section_types(configuration)

    return configuration


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


def _format_sensor_section_types(configuration: tp.Dict):
    """Format sensor options to the right type for processing.

    - Convert the sensor specific configuration parameters values to the right
    data type, skipping `None` value set previously.
    - Boolean `True` entry have to be in ['True','true','1'] else, it considere `False`.

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
    sensor_type = configuration["HEADER"]["sensor_type"]

    if sensor_type == "adcp":
        config_types = ADCP_CONFIG_TYPES
    else:
        raise ConfigFileError(
            f"sensor_type {sensor_type} is invalid. Must be one of {SENSOR_TYPES}"
        )

    for section, options in config_types.items():
        for option in options:
            if configuration[section][option]:
                if config_types[section][option] == bool:
                    configuration[section][option] = (
                        configuration[section][option] in TRUE_VALUES
                    )

                elif config_types[section][option] in (int, float):
                    configuration[section][option] = _convert_to_numerical(
                        option_value=configuration[section][option],
                        option_type=config_types[section][option],
                        section=section,
                        option=option,
                    )

                elif isinstance(config_types[section][option], dict):
                    configuration[section][option] = _convert_multiples_valued_options(
                        option_value=configuration[section][option],
                        option_type=config_types[section][option],
                        section=section,
                        option=option,
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
        stripped = stripped.replace(sep, ",")

    return [s for s in stripped.split(",") if s != ""]


def _set_empty_field_to_none(configuration):
    for section, options in configuration.items():
        for option in options.keys():
            if not configuration[section][option]:
                configuration[section][option] = None


def _format_input_output_section(configuration):
    configuration["INPUT"]["input_files"] = _format_string_sequence_to_list(
        configuration["INPUT"]["input_files"]
    )
    for option in ["odf_output", "netcdf_output"]:
        if configuration["OUTPUT"][option] in TRUE_VALUES:
            configuration["OUTPUT"][option] = True


def _convert_to_numerical(option_value, option_type, section, option):
    try:
        option_value = option_type(option_value)
    except ValueError as catched_value_error:
        expected_type = str(option_type).split("'")[1]
        raise ConfigFileError(
            f"""{section}/{option} value, {option_value}, is invalid.
            The expected value type : {expected_type}."""
        ) from catched_value_error

    return option_value


def _convert_multiples_valued_options(option_value, option_type, section, option):
    option_value = ast.literal_eval(option_value)

    if isinstance(option_value, tuple):
        option_value = list(option_value)

    if not isinstance(option_value, list):
        option_value = [option_value]

    for indx in range(len(option_value)):
        option_value[indx] = _convert_to_numerical(
            option_value[indx], option_type["type"], section, option
        )

    if option_type["min"]:
        if len(option_value) < option_type["min"]:
            raise ConfigFileError(
                f"""{section}/{option} value, {option_value} received {len(option_value)} values.
                Expected from {option_type['min']} to {option_type['max']} values."""
            )
    if option_type["max"]:
        if len(option_value) > option_type["max"]:

            raise ConfigFileError(
                f"""{section}/{option} value, {option_value} received {len(option_value)} values.
                Expected from {option_type['min']} to {option_type['max']} values."""
            )
    if option_type["exacly"]:
        if len(option_value) != option_type["exacly"]:
            raise ConfigFileError(
                f"""{section}/{option} value, {option_value} received {len(option_value)} values.
                Expected {option_type[1][0]} values"""
            )
    return option_value

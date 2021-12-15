"""
*** NOTE NOT UP TO DATE ***
author: Jérôme Guay
date: March 4, 2021

This make_configparser is called by magtogoek_command.py
    $ mtgk config ...

This modules also contains the sections and default parameters values for the configparsers.

NOTE: More comments should be added in the configparser files.
NOTE: Missing,functions to open the config files.
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
import sys
import typing as tp
from collections import namedtuple
from configparser import RawConfigParser
from datetime import datetime
from pathlib import Path

import click
import dateutil.parser

REFERENCE = "https://github.com/JeromeJGuay/magtogoek"
TRUE_VALUES = ["True", "true", "1", "On", "on"]
FALSE_VALUES = ["False", "False", "0", "Off", "off", ""]
SENSOR_TYPES = ["adcp"]

OptionInfos = namedtuple(
    "option_infos",
    (
        "dtypes",
        "default",
        "nargs",
        "nargs_min",
        "nargs_max",
        "choice",
        "value_min",
        "value_max",
        "is_path",
        "is_file",
        "is_time_stamp",
        "is_required",
        "null_value",
    ),
    defaults=[[], None, None, None, None, None, None, None, False, False, False, False, None],
)


class ConfigFileError(SystemExit):
    def __init__(self, error, section=None, option=None, option_info=None, value=None):
        self.error = error
        self.section = section
        self.option = option
        if option_info is None:
            option_info = OptionInfos()
        self.option_info = option_info
        self.value = value
        self.msg = ""

        self._get_error_message()
        click.secho("ConfigFileError", fg="red", bold=True)
        print(self.msg)
        print("Exiting magtogoek")

    def _get_error_message(self):
        if self.error == "header_missing":
            self.msg = "Config is missing a `HEADER` section."
        if self.error == "sensor_type":
            self.msg = f"`sensor_type` value is either missing or invalid. `sensor_type` must be one of `{SENSOR_TYPES}`."
        if self.error == "dtype":
            self.msg = f"`{self.section}/{self.option}` expected a `{' or '.join(self.option_info.dtypes)}` but received `{self.value}`."
        if self.error == "nargs":
            self.msg = f"`{self.section}/{self.option}` expected "
            if self.option_info.nargs:
                self.msg = f"`{self.option_info.nargs}` "
            else:
                if self.option_info.nargs_min is not None:
                    self.msg += f"a minimum of `{self.option_info.nargs_min}` "
                    if self.option_info.nargs_max:
                        self.msg += "and "
                if self.option_info.nargs_max:
                    self.msg += f"a maximum of `{self.option_info.nargs_max}` "
            self.msg += f"values, but received `{len(self.value)}`."
        if self.error == "range":
            self.msg = f"`{self.section}/{self.option}` expected a value "
            if self.option_info.value_min is not None:
                self.msg += f">= than `{self.option_info.value_min}` "
                if self.option_info.value_max:
                    self.msg += "and "
            if self.option_info.value_max:
                self.msg += f"<= than `{self.option_info.value_max}` "
            self.msg += f", but received a value of `{self.value}`."
        if self.error == "choice":
            self.msg = f"`{self.section}/{self.option}` expected a value in `{self.option_info.choice}` but received `{self.value}`."
        if self.error == "string_format":
            self.msg = f"`{self.section}/{self.option}` is an invalid datetime format. Use `YYYY-MM-DDThh:mm:ss.ssss`"
        if self.error == "path":
            self.msg = (
                f"`{self.section}/{self.option}` path or path/to/file does not exist."
            )
        if self.error == "file":
            self.msg = (
            f"`{self.section}/{self.option}` file {self.value} does not exist."
            )
        if "bool" in self.option_info.dtypes:
            self.msg += (
                f"\nBoolean have to be express with {TRUE_VALUES} or {FALSE_VALUES}."
            )
        if self.error == "required":
            self.msg = (
                f"`{self.section}/{self.option}` requires a value. None were given."
            )


BASE_CONFIG = dict(
    HEADER={
        "made_by": OptionInfos(dtypes=["str"], default=getpass.getuser()),
        "last_updated": OptionInfos(dtypes=["str"], default=datetime.now().strftime("%Y-%m-%d")),
        "sensor_type": OptionInfos(dtypes=["str"], default="", is_required=True),
        "platform_type": OptionInfos(dtypes=["str"], default="", choice=["buoy", "mooring", "ship"]),
    },
    INPUT={
        "input_files": OptionInfos(
            dtypes=["str"], default="", nargs_min=1, is_file=True, is_required=True
        ),
        "platform_file": OptionInfos(dtypes=["str"], default="", is_file=True),
        "platform_id": OptionInfos(dtypes=["str"], default=""),
        "sensor_id": OptionInfos(dtypes=["str"], default=""),
    },
    OUTPUT={
        "netcdf_output": OptionInfos(dtypes=["str", "bool"], default="", is_path=True),
        "odf_output": OptionInfos(dtypes=["str", "bool"], default="", is_path=True),
    },
    NETCDF_CF={
        "Conventions": OptionInfos(dtypes=["str"], default="CF 1.8"),
        "title": OptionInfos(dtypes=["str"], default=""),
        "institution": OptionInfos(dtypes=["str"], default=""),
        "summary": OptionInfos(dtypes=["str"], default=""),
        "references": OptionInfos(dtypes=["str"], default=REFERENCE),
        "comments": OptionInfos(dtypes=["str"], default=""),
        "naming_authority": OptionInfos(dtypes=["str"], default="BODC, SDC, CF, MEDS"),
        "source": OptionInfos(dtypes=["str"], default=""),
    },
    PROJECT={
        "project": OptionInfos(dtypes=["str"], default=""),
        "sea_name": OptionInfos(dtypes=["str"], default=""),
        "sea_code": OptionInfos(dtypes=["str"], default=""),
    },
    CRUISE={
        "country_institute_code": OptionInfos(dtypes=["str"], default=""),
        "cruise_number": OptionInfos(dtypes=["str"], default="", null_value=""),
        "cruise_name": OptionInfos(dtypes=["str"], default=""),
        "cruise_description": OptionInfos(dtypes=["str"], default=""),
        "organization": OptionInfos(dtypes=["str"], default=""),
        "chief_scientist": OptionInfos(dtypes=["str"], default=""),
        "start_date": OptionInfos(dtypes=["str"], default=""),
        "end_date": OptionInfos(dtypes=["str"], default=""),
        "event_number": OptionInfos(dtypes=["str"], default="", null_value=""),
        "event_qualifier1": OptionInfos(dtypes=["str"], default="", null_value=""),
        # "event_qualifier2": OptionInfos(dtypes=["str"], default=""),
        "event_comments": OptionInfos(dtypes=["str"], default=""),
    },
    GLOBAL_ATTRIBUTES={
        "date_created": OptionInfos(dtypes=["str"], default=""),
        #        "data_type": OptionInfos(dtypes=["str"], default=""),
        #        "data_subtype": OptionInfos(dtypes=["str"], default=""),
        "cdm_data_type": OptionInfos(dtypes=["str"], default=""),
        "country_code": OptionInfos(dtypes=["str"], default=""),
        "publisher_email": OptionInfos(dtypes=["str"], default=""),
        "creator_type": OptionInfos(dtypes=["str"], default=""),
        "publisher_name": OptionInfos(dtypes=["str"], default=""),
        "keywords": OptionInfos(dtypes=["str"], default=""),
        "keywords_vocabulary": OptionInfos(dtypes=["str"], default=""),
        "standard_name_vocabulary": OptionInfos(dtypes=["str"], default="CF v.52"),
        "acknowledgment": OptionInfos(dtypes=["str"], default=""),
    },
)

ADCP_CONFIG = dict(
    ADCP_PROCESSING={
        "yearbase": OptionInfos(dtypes=["int"], default="", is_required=True),
        "adcp_orientation": OptionInfos(dtypes=["str"], choice=["up", "down"]),
        "sonar": OptionInfos(dtypes=["str"], choice=["wh", "sv", "os", "sw", "sw_pd0"], is_required=True),
        "navigation_file": OptionInfos(dtypes=["str"], default="", is_file=True),
        "leading_trim": OptionInfos(dtypes=["str"], default=""),
        "trailing_trim": OptionInfos(dtypes=["str"], default=""),
        "sensor_depth": OptionInfos(dtypes=["float"], default=""),
        "depth_range": OptionInfos(dtypes=["float"], default="()", nargs_min=0, nargs_max=2),
        "bad_pressure": OptionInfos(dtypes=["bool"], default=False),
        "magnetic_declination": OptionInfos(dtypes=["float"], default=""),
        "keep_bt": OptionInfos(dtypes=["bool"], default=True),
        "start_time": OptionInfos(dtypes=["str"], default=""),
        "time_step": OptionInfos(dtypes=["float"], default=""),
    },
    ADCP_QUALITY_CONTROL={
        "quality_control": OptionInfos(dtypes=["bool"], default=True),
        "amplitude_threshold": OptionInfos(dtypes=["int"], default=0, value_min=0, value_max=255),
        "percentgood_threshold": OptionInfos(dtypes=["int"], default=64, value_min=0, value_max=100),
        "correlation_threshold": OptionInfos(dtypes=["int"], default=90, value_min=0, value_max=255),
        "horizontal_velocity_threshold": OptionInfos(dtypes=["float"], default=5),
        "vertical_velocity_threshold": OptionInfos(dtypes=["float"], default=5),
        "error_velocity_threshold": OptionInfos(dtypes=["float"], default=5),
        "sidelobes_correction": OptionInfos(dtypes=["bool"], default=True),
        "bottom_depth": OptionInfos(dtypes=["float"]),
        "pitch_threshold": OptionInfos(dtypes=["int"], default=20, value_min=0, value_max=180),
        "roll_threshold": OptionInfos(dtypes=["int"], default=20, value_min=0, value_max=180),
        "motion_correction_mode": OptionInfos(dtypes=["str"], default="bt", choice=["bt", "nav", "off"]),
    },
    ADCP_OUTPUT={
        "merge_output_files": OptionInfos(dtypes=["bool"], default=True),
        "bodc_name": OptionInfos(dtypes=["bool"], default=True),
        "force_platform_metadata": OptionInfos(dtypes=["bool"], default=False),
        "drop_percent_good": OptionInfos(dtypes=["bool"], default=True),
        "drop_correlation": OptionInfos(dtypes=["bool"], default=True),
        "drop_amplitude": OptionInfos(dtypes=["bool"], default=True),
        "odf_data": OptionInfos(dtypes=['str'], default='both', choice=['vel', 'anc', 'both']),
        "make_figures": OptionInfos(dtypes=["bool"], default=True),
        "make_log": OptionInfos(dtypes=["bool"], default=True),
    },
)

def load_config(self, filename: str, updated_params: dict=None):
        self.parser.read(filename)

        self.sensor_type = _get_sensor_type(self.parser)

        _add_config_missing(self.parser, self.sensor_type)

        if updated_params is not None:
            _update_parser_values(self.parser, updated_params)
            self._write_configfile(filename)

        config = {}
        config.update(self.parser._sections)

        _format_config_options(config, Path(filename).parent)

    def _write_configfile(self, filename: str):
        with open(filename, "w") as f:
            self.parser.write(f)


def make_configfile(filename: str, sensor_type: str, new_values: tp.Dict = None):
    """Make a configfile for the given sensor_type.

     Uses default values and update/adds it if `new_values` are passed"""
    parser = RawConfigParser()
    parser.optionxform = str

    # getting the default config as dict
    default_config = _get_default_config(sensor_type)

    # Building the parser
    parser = RawConfigParser()
    parser.optionxform = str
    for section, options in default_config.items():
        parser.add_section(section)
        for option, value in options.items():
            parser[section][option] = str(value)

    # Overwrite the default values with the `updated_params`.
    if new_values:
        _update_parser_values(parser, new_values)

    _write_configfile(parser, filename)


def _update_parser_values(parser: RawConfigParser, values: tp.Dict):
    """Overwrite the default values with those from `values`."""
    for section, options in values.items():
        for option, value in options.items():
            parser[section][option] = "" if value is None else str(value)


def _write_configfile(parser, filename):
    with open(filename, "w") as f:
        parser.write(f)


def load_configfile(filename: str, updated_params: tp.Dict = None) -> dict:
    """load a configfile.

    Returns parser as a dictionary with the appropriate types.

    - Add the missing expected sections and options with empty string as value.
    - Updates the value if dictionary is passed as `updated_params`.
    - saves the edited configuration files.
    - convert the options from string to the correct type for processing.

    """
    if not Path(filename).exists():
        print(f"Error: {filename} not found")
        sys.exit()

    parser = RawConfigParser()
    parser.optionxform = str
    parser.read(filename)

    sensor_type = _get_sensor_type(parser)

    _add_config_missing(parser, sensor_type)

    if updated_params:
        _update_parser_values(parser, updated_params)
        _write_configfile(parser, filename)

    config = {}
    config.update(parser._sections)

    _format_config_options(config, Path(filename).parent)

    return config


def _get_sensor_type(parser: RawConfigParser):
    if parser.has_option("HEADER", "sensor_type"):
        sensor_type = parser["HEADER"]["sensor_type"]
        if not sensor_type:
            raise ConfigFileError(error="sensor_type")
        return sensor_type
    else:
        raise ConfigFileError(error="sensor_type")


def _add_config_missing(parser: RawConfigParser, sensor_type):
    """Check for missing sections or options compared to the expected parser

    - Adds the options or section if needed with empty string as value.

    Notes
    -----
    This prevents missing key error later in the processing without needing
    to add tons of conditional statements.

    """
    default_config = _get_default_config(sensor_type)
    for section, options in default_config.items():
        if not parser.has_section(section):
            parser.add_section(section)
        for option in options.keys():
            if not parser.has_option(section, option):
                parser[section][option] = ""


def _format_config_options(config: tp.Dict, config_path: Path):
    """Format config options for processing.

    - Convert the sensor specific configuration parameters values to the right
    data type, skipping `None` value set previously.
    - Boolean `True` entry have to be in ['True','true','1'] else, it considered `False`.

    Raises
    ------
    ConfigFileError :
        Error are risen if the options value cannot be converted to the right dtypes,
        length, value, choice,  etc.

    Notes
    -----
    Setting options to `None` is equivalent to `False` for later processing but does not
    imply that the expected value is a boolean.

    There should be additional `sensor_type` options for each different sensor processing
    """
    config_info = _get_config_info(config["HEADER"]["sensor_type"])

    for section, options in config_info.items():
        for option in options:
            option_info = config_info[section][option]
            value = config[section][option]
            if "bool" not in option_info.dtypes:
                if not value and value != 0:
                    value = None
                    if option_info.is_required is True:
                        raise ConfigFileError("required", section, option, option_info, value)
            if value is not None:
                value = _format_option(
                    config[section][option], option_info, section, option, config_path
                )
            elif option_info.null_value is not None:
                    value = option_info.null_value
            config[section][option] = value


def _format_option(value, option_info, section, option, config_path):
    if option_info.nargs or option_info.nargs_min or option_info.nargs_max:
        value = _get_sequence_from_string(value)
        _check_options_length(value, option_info, section, option)
        for i, _value in enumerate(value):
            value[i] = _format_option_type(
                _value, option_info, section, option, config_path
            )
    else:
        value = _format_option_type(value, option_info, section, option, config_path)

    return value


def _format_option_type(value, option_info, section, option, config_path):
    """Format option to the right dtypes.
    - Checks if value is outside option_info.min_value and option_info.max_value.
    - Check if values is within the option_info.choice."""

    try:
        value = _format_value_dtypes(value, option_info.dtypes)
    except ValueError:
        raise ConfigFileError("dtype", section, option, option_info, value)

    if option_info.value_min or option_info.value_max:
        _check_option_min_max(value, option_info, section, option)

    if option_info.choice is not None:
        if value not in option_info.choice:
            raise ConfigFileError("choice", section, option, option_info, value)

    if option_info.is_path is True and isinstance(value, str):
        value = Path(config_path).joinpath(Path(value)).resolve()
        if not any((value.is_dir(), value.parent.is_dir())):
            raise ConfigFileError("path", section, option, option_info, value)
        value = str(value)

    if option_info.is_file is True:
        value = Path(config_path).joinpath(Path(value)).resolve()
        if not value.is_file():
            raise ConfigFileError("file", section, option, option_info, value)
        value = str(value)

    if option_info.is_time_stamp is True:
        try:
            dateutil.parser.parse(value)
        except dateutil.parser._parser.ParserError:
            raise ConfigFileError("string_format", section, option, option_info, value)

    return value


def _format_value_dtypes(value: str, dtypes: str) -> tp.Union[bool, int, float, str]:
    if "bool" in dtypes:
        if value in TRUE_VALUES + FALSE_VALUES:
            return value in TRUE_VALUES
    if "int" in dtypes:
        return int(float(value))
    if "float" in dtypes:
        return float(value)
    if "str" in dtypes:
        for quotes in ["'", '"']:
            value = value.strip(quotes)
        return value
    raise ValueError


def _get_sequence_from_string(sequence: str) -> tp.List:
    """Decode string containing a sequence of value.

    The sequence can be between brackets, parenthesis or nothing
    and have comma, colon, semi-colon, newlines or spaces as separators.

    Example
    -------
    _format_string_list'(arg1, arg2, arg3)' -> [arg1 arg2 arg3]
    """
    for sep in (":", ";", " ", "\n", "(", ")", "[", "]", "'", '"'):
        sequence = sequence.replace(sep, ",")

    return list(filter(None, sequence.split(",")))


def _check_options_length(value, option_info, section, option):
    if option_info.nargs:
        if len(value) != option_info.nargs:
            raise ConfigFileError("nargs", section, option, option_info, value)
    if option_info.nargs_max:
        if len(value) > option_info.nargs_max:
            raise ConfigFileError("nargs", section, option, option_info, value)
    if option_info.nargs_min:
        if len(value) < option_info.nargs_min:
            raise ConfigFileError("nargs", section, option, option_info, value)


def _check_option_min_max(value, option_info, section, option):
    if option_info.value_max is not None:
        if value > option_info.value_max:
            raise ConfigFileError("range", section, option, option_info, value)
    if option_info.value_min is not None:
        if value < option_info.value_min:
            raise ConfigFileError("range", section, option, option_info, value)


def _get_config_info(sensor_type: str):
    if sensor_type == "adcp":
        config_info = {**BASE_CONFIG, **ADCP_CONFIG}
    else:
        raise ConfigFileError(error="sensor_type")

    return config_info


def _get_default_config(sensor_type: str):
    config_info = _get_config_info(sensor_type)
    config_defaults = {}

    for section, options in config_info.items():
        config_defaults[section] = dict()
        for option_name, option_info in options.items():
            config_defaults[section][option_name] = option_info.default

    config_defaults["HEADER"]["sensor_type"] = sensor_type

    return config_defaults


if __name__ == "__main__":
    FILENAME = "../test/data/adcp_iml6_2017.ini"

    configuration = load_configfile(FILENAME)

    make_configfile("test", "adcp", configuration)

"""
December 18, 2021
Made by JeromeJGuay
"""

import typing as tp
from configparser import RawConfigParser
from pathlib import Path

import click
import dateutil.parser

TRUE_VALUES = ["True", "true", "1", "On", "on"]
FALSE_VALUES = ["False", "False", "0", "Off", "off", ""]
VALID_DTYPES = ["str", "int", "float", "bool"]


class TaskParserError(SystemExit):
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
            self.msg = f"`{self.section}/{self.option}` expected a value in `{self.option_info.choice}` but received `{self.value}`. "
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


class OptionInfos:
    dtypes: tp.List[str] = None
    default: tp.Union[str, float, int, bool] = None
    nargs: int = None
    nargs_min: int = None
    nargs_max: int = None
    choice: list = None
    value_min: tp.Union[int, float] = None
    value_max: tp.Union[int, float] = None
    is_path: bool = False
    is_file: bool = False
    is_time_stamp: bool = False
    is_required: bool = False
    null_value: tp.Union[str, float, int, bool] = False

    def __init__(
            self,
            dtypes: tp.List[str] = None,
            default: tp.Union[str, float, int, bool] = None,
            nargs: int = None,
            nargs_min: int = None,
            nargs_max: int = None,
            choice: list = None,
            value_min: tp.Union[int, float] = None,
            value_max: tp.Union[int, float] = None,
            is_path: bool = False,
            is_file: bool = False,
            is_time_stamp: bool = False,
            is_required: bool = False,
            null_value: tp.Union[str, float, int, bool] = False,
    ):

        object.__setattr__(self, "dtypes", dtypes)
        object.__setattr__(self, "default", default)
        object.__setattr__(self, "nargs", nargs)
        object.__setattr__(self, "nargs_min", nargs_min)
        object.__setattr__(self, "nargs_max", nargs_max)
        object.__setattr__(self, "choice", choice)
        object.__setattr__(self, "value_min", value_min)
        object.__setattr__(self, "value_max", value_max)
        object.__setattr__(self, "is_path", is_path)
        object.__setattr__(self, "is_file", is_file)
        object.__setattr__(self, "is_time_stamp", is_time_stamp)
        object.__setattr__(self, "is_required", is_required)
        object.__setattr__(self, "null_value", null_value)

        self._list_check()
        self._dtypes_check()
        self._value_min_max_check()
        self._nargs_check()

    def __setattr__(self, name, value):
        raise AttributeError("ParserInfos attributes cannot be modify.")

    def __delattr__(self, name):
        raise AttributeError("ParserInfos attributes cannot be deleted.")

    def __repr__(self):
        return str(self.__dict__).replace(",", ",\n")

    def _list_check(self):
        for option in ("dtypes", "choice"):
            if self.__dict__[option] is not None:
                if not isinstance(self.__dict__[option], list):
                    raise ValueError(f"{option} argument expected a list.")

    def _dtypes_check(self):
        if self.dtypes is not None:
            for e in self.dtypes:
                if e not in VALID_DTYPES:
                    raise ValueError(
                        f"{e} is not a valid dtype. dtypes must be one of {VALID_DTYPES}."
                    )

    def _value_min_max_check(self):
        if self.value_min is not None and self.value_max is not None:
            if self.value_min > self.value_max:
                raise ValueError("value_max must be greater than value_min.")

    def _nargs_check(self):
        if self.nargs is not None and any(
                (self.nargs_min is not None, self.nargs_max is not None)
        ):
            raise ValueError(
                "nargs parameter cannot be used with nargs_min or nargs_max."
            )


class TaskParser:
    def __init__(self):
        self._parser_info: tp.Dict[str, tp.Dict[str, OptionInfos]] = {}

    def add_option(
            self,
            section: str = None,
            option: str = None,
            dtypes: tp.List[str] = None,
            default: tp.Union[str, float, int, bool] = None,
            nargs: int = None,
            nargs_min: int = None,
            nargs_max: int = None,
            choice: list = None,
            value_min: tp.Union[int, float] = None,
            value_max: tp.Union[int, float] = None,
            is_path: bool = False,
            is_file: bool = False,
            is_time_stamp: bool = False,
            is_required: bool = False,
            null_value: tp.Union[str, float, int, bool] = False,
    ):
        if section not in self._parser_info:
            self._parser_info[section] = {}
        self._parser_info[section][option] = OptionInfos(
            dtypes,
            default,
            nargs,
            nargs_min,
            nargs_max,
            choice,
            value_min,
            value_max,
            is_path,
            is_file,
            is_time_stamp,
            is_required,
            null_value,
        )

    @property
    def parser(self, empty: bool = False):
        parser = _rawconfigparser()
        for section, options in self._parser_info.items():
            parser.add_section(section)
            for option, value in options.items():
                if empty is True or value.default is None:
                    parser[section][option] = ""
                else:
                    parser[section][option] = str(value.default)
        return parser

    @property
    def as_dict(self):
        parser_dict = self.parser._sections
        return parser_dict

    def format_parser_dict(self, parser_dict: dict, new_values_dict: dict = None, filename: str = None):
        _add_missing_options(parser_dict, self._parser_info)

        if new_values_dict is not None:
            _update_parser_values(parser_dict, new_values_dict)

        _format_config_options(config=parser_dict, config_info=self._parser_info,
                               config_path=filename)  # NEW NAME NEEDED

    def load(self, filename: str, new_values_dict: dict = None):
        parser = _rawconfigparser()
        parser.read(filename)
        parser_dict = parser._sections

        self.format_parser_dict(parser_dict, new_values_dict, filename)

        return parser_dict

    def write(self, filename: str):
        with open(filename, "w") as f:
            self.parser.write(f)

    def write_from_dict(self, filename, parser_dict):
        parser = _rawconfigparser()
        for section, options in parser_dict.items():
            parser.add_section(section)
            for option, value in options.items():
                if value is None:
                    parser[section][option] = ""
                else:
                    parser[section][option] = str(value)
        self.format_parser_dict(parser._sections)

        with open(filename, "w") as f:
            parser.write(f)


def _rawconfigparser():
    parser: RawConfigParser = RawConfigParser()
    parser.optionxform = str
    return parser


def _update_parser_values(parser: dict, values_dict: dict = None):
    for section, options in values_dict.items():
        if section in parser:
            for option, value in options.items():
                parser[section][option] = "" if value is None else str(value)
        return parser


def _add_missing_options(
        parser_dict: dict, parser_info: tp.Dict[str, tp.Dict[str, OptionInfos]],
):
    for section, options in parser_info.items():
        if not section in parser_dict:
            parser_dict[section] = {}
        for option in options.keys():
            if option not in parser_dict[section]:
                parser_dict[section][option] = None
                if parser_info[section][option].null_value is not None:
                    parser_dict[section][option] = parser_info[section][
                        option
                    ].null_value


def _format_config_options(config: tp.Dict, config_info, config_path: Path = None):
    """Format config options for processing.

    - Convert the sensor specific configuration parameters values to the right
    data type, skipping `None` value set previously.
    - Boolean `True` entry have to be in ['True','true','1'] else, it considered `False`.

    Raises
    ------
    TaskFileError :
        Error are risen if the options value cannot be converted to the right dtypes,
        length, value, choice,  etc.

    """
    for section, options in config_info.items():
        for option in options:
            option_info = config_info[section][option]
            value = config[section][option]
            if "bool" not in option_info.dtypes:
                if not value and value != 0:
                    value = None
                    if option_info.is_required is True:
                        raise TaskParserError(
                            "required", section, option, option_info, value
                        )
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
        raise TaskParserError("dtype", section, option, option_info, value)

    if option_info.value_min or option_info.value_max:
        _check_option_min_max(value, option_info, section, option)

    if option_info.choice is not None:
        if value not in option_info.choice:
            raise TaskParserError("choice", section, option, option_info, value)

    if option_info.is_path is True and isinstance(value, str):
        value = Path(config_path).joinpath(Path(value)).resolve()
        if not any((value.is_dir(), value.parent.is_dir())):
            raise TaskParserError("path", section, option, option_info, value)
        value = str(value)

    if option_info.is_file is True:
        value = Path(config_path).joinpath(Path(value)).resolve()
        if not value.is_file():
            raise TaskParserError("file", section, option, option_info, value)
        value = str(value)

    if option_info.is_time_stamp is True:
        try:
            dateutil.parser.parse(value)
        except dateutil.parser._parser.ParserError:
            raise TaskParserError("string_format", section, option, option_info, value)

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
            raise TaskParserError("nargs", section, option, option_info, value)
    if option_info.nargs_max:
        if len(value) > option_info.nargs_max:
            raise TaskParserError("nargs", section, option, option_info, value)
    if option_info.nargs_min:
        if len(value) < option_info.nargs_min:
            raise TaskParserError("nargs", section, option, option_info, value)


def _check_option_min_max(value, option_info, section, option):
    if option_info.value_max is not None:
        if value > option_info.value_max:
            raise TaskParserError("range", section, option, option_info, value)
    if option_info.value_min is not None:
        if value < option_info.value_min:
            raise TaskParserError("range", section, option, option_info, value)

if __name__ == "__main__":
    from datetime import datetime
    REFERENCE = "TODO"

    parser = TaskParser()
    parser.add_option('HEADER', "made_by",dtypes=["str"], default=getpass.getuser())
    parser.add_option('HEADER', "last_updated", dtypes=["str"], default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_option('HEADER', "sensor_type", dtypes=["str"], default="", is_required=True)
    parser.add_option('HEADER', "platform_type", dtypes=["str"], default="", choice=["buoy", "mooring", "ship"])

    parser.add_option('INPUT',  "input_files", dtypes=["str"], default="", nargs_min=1, is_file=True, is_required=True)
    parser.add_option('INPUT',"platform_file", dtypes=["str"], default="", is_file=True)
    parser.add_option('INPUT',"platform_id", dtypes=["str"], default="")
    parser.add_option('INPUT',"sensor_id", dtypes=["str"], default="")

    parser.add_option('OUTPUT',"netcdf_output", dtypes=["str", "bool"], default="", is_path=True)
    parser.add_option('OUTPUT',"odf_output", dtypes=["str", "bool"], default="", is_path=True)

    parser.add_option('NETCDF_CF',"Conventions", dtypes=["str"], default="CF 1.8")
    parser.add_option('NETCDF_CF',"title", dtypes=["str"], default="")
    parser.add_option('NETCDF_CF',"institution", dtypes=["str"], default="")
    parser.add_option('NETCDF_CF',"summary", dtypes=["str"], default="")
    parser.add_option('NETCDF_CF',"references", dtypes=["str"], default=REFERENCE)
    parser.add_option('NETCDF_CF',"comments", dtypes=["str"], default="")
    parser.add_option('NETCDF_CF',"naming_authority", dtypes=["str"], default="BODC, SDC, CF, MEDS")
    parser.add_option('NETCDF_CF',"source", dtypes=["str"], default="")

    parser.add_option('PROJECT', "project", dtypes=["str"], default=""),
    parser.add_option('PROJECT',"sea_name", dtypes=["str"], default="")
    parser.add_option('PROJECT',"sea_code", dtypes=["str"], default="")


    parser.add_option('CRUISE',"country_institute_code", dtypes=["str"], default="")
    parser.add_option('CRUISE',"cruise_number", dtypes=["str"], default="", null_value="")
    parser.add_option('CRUISE',"cruise_name", dtypes=["str"], default="")
    parser.add_option('CRUISE',"cruise_description", dtypes=["str"], default="")
    parser.add_option('CRUISE',"organization", dtypes=["str"], default="")
    parser.add_option('CRUISE',"chief_scientist", dtypes=["str"], default="")
    parser.add_option('CRUISE',"start_date", dtypes=["str"], default="")
    parser.add_option('CRUISE',"end_date", dtypes=["str"], default="")
    parser.add_option('CRUISE',"event_number", dtypes=["str"], default="", null_value="")
    parser.add_option('CRUISE',"event_qualifier1", dtypes=["str"], default="", null_value="")
    parser.add_option('CRUISE',"event_comments", dtypes=["str"], default="")

    parser.add_option("GLOBAL_ATTRIBUTES","date_created", dtypes=["str"], default="")
    parser.add_option("GLOBAL_ATTRIBUTES","cdm_data_type", dtypes=["str"], default="")
    parser.add_option("GLOBAL_ATTRIBUTES","country_code", dtypes=["str"], default="")
    parser.add_option("GLOBAL_ATTRIBUTES","publisher_email", dtypes=["str"], default="")
    parser.add_option("GLOBAL_ATTRIBUTES","creator_type", dtypes=["str"], default="")
    parser.add_option("GLOBAL_ATTRIBUTES","publisher_name", dtypes=["str"], default="")
    parser.add_option("GLOBAL_ATTRIBUTES","keywords", dtypes=["str"], default="")
    parser.add_option("GLOBAL_ATTRIBUTES","keywords_vocabulary", dtypes=["str"], default="")
    parser.add_option("GLOBAL_ATTRIBUTES","standard_name_vocabulary", dtypes=["str"], default="CF v.52")
    parser.add_option("GLOBAL_ATTRIBUTES","acknowledgment", dtypes=["str"], default="")

    section = "ADCP_PROCESSING"
    parser.add_option(section, "yearbase", dtypes=["int"], default="", is_required=True)
    parser.add_option(section, "adcp_orientation", dtypes=["str"], choice=["up", "down"])
    parser.add_option(section, "sonar", dtypes=["str"], choice=["wh", "sv", "os", "sw", "sw_pd0"], is_required=True)
    parser.add_option(section, "navigation_file", dtypes=["str"], default="", is_file=True)
    parser.add_option(section, "leading_trim", dtypes=["str"], default="")
    parser.add_option(section, "trailing_trim", dtypes=["str"], default="")
    parser.add_option(section, "sensor_depth", dtypes=["float"], default="")
    parser.add_option(section, "depth_range", dtypes=["float"], default="()", nargs_min=0, nargs_max=2)
    parser.add_option(section, "bad_pressure", dtypes=["bool"], default=False)
    parser.add_option(section, "magnetic_declination", dtypes=["float"], default="")
    parser.add_option(section, "keep_bt", dtypes=["bool"], default=True)
    parser.add_option(section, "start_time", dtypes=["str"], default="")
    parser.add_option(section, "time_step", dtypes=["float"], default="")

    section = "ADCP_QUALITY_CONTROL"
    parser.add_option(section, "quality_control", dtypes=["bool"], default=True)
    parser.add_option(section, "amplitude_threshold", dtypes=["int"], default=0, value_min=0, value_max=255)
    parser.add_option(section, "percentgood_threshold", dtypes=["int"], default=64, value_min=0, value_max=100)
    parser.add_option(section,"correlation_threshold", dtypes=["int"], default=90, value_min=0, value_max=255)
    parser.add_option(section,"horizontal_velocity_threshold", dtypes=["float"], default=5)
    parser.add_option(section,"vertical_velocity_threshold", dtypes=["float"], default=5)
    parser.add_option(section,"error_velocity_threshold", dtypes=["float"], default=5)
    parser.add_option(section,"sidelobes_correction", dtypes=["bool"], default=True)
    parser.add_option(section,"bottom_depth", dtypes=["float"])
    parser.add_option(section,"pitch_threshold", dtypes=["int"], default=20, value_min=0, value_max=180)
    parser.add_option(section,"roll_threshold", dtypes=["int"], default=20, value_min=0, value_max=180)
    parser.add_option(section,"motion_correction_mode", dtypes=["str"], default="bt", choice=["bt", "nav", "off"])

    section = "ADCP_OUTPUT"
    parser.add_option(section, "merge_output_files", dtypes=["bool"], default=True)
    parser.add_option(section, "bodc_name", dtypes=["bool"], default=True)
    parser.add_option(section,"force_platform_metadata", dtypes=["bool"], default=False)
    parser.add_option(section,"drop_percent_good", dtypes=["bool"], default=True)
    parser.add_option(section,"drop_correlation", dtypes=["bool"], default=True)
    parser.add_option(section,"drop_amplitude", dtypes=["bool"], default=True)
    parser.add_option(section,"odf_data" dtypes=["str"], default="both", choice=["vel", "anc", "both"])
    parser.add_option(section,"make_figures", dtypes=["bool"], default=True)
    parser.add_option(section,"make_log", dtypes=["bool"], default=True)

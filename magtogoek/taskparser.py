"""
December 18, 2021
Made by JeromeJGuay
"""

import getpass
import sys
from typing import List, Union, Dict, Optional, Tuple
from configparser import RawConfigParser
from pathlib import Path
from datetime import timezone
import click
import dateutil.parser
from magtogoek.utils import get_files_from_expression, ensure_list_format

TRUE_VALUES = ["True", "true", "T", "t", "On", "on"]
FALSE_VALUES = ["False", "False", "F", "f", "Off", "off", ""]
VALID_DTYPES = ["str", "int", "float", "bool"]

StrIntFloatBool = Union[str, int, float, bool]
ListStrIntFloatBool = Union[StrIntFloatBool, List[StrIntFloatBool]]
ParserDict = Dict[str, Dict[str, ListStrIntFloatBool]]


class OptionInfos:
    """
    Class used/called by TaskParser.
    Immutable object that hold the TaskParser options information.
    When created, an OptionInfos object run check-up to validate the validate
    the given values.
    """
    section: str = None
    option: str = None
    dtypes: List[str] = None
    default: Optional[ListStrIntFloatBool] = None
    nargs: Optional[int] = None
    nargs_min: Optional[int] = None
    nargs_max: Optional[int] = None
    choice: Optional[List[StrIntFloatBool]] = None
    value_min: Optional[Union[int, float]] = None
    value_max: Optional[Union[int, float]] = None
    is_path: bool = False
    is_file: bool = False
    is_time_stamp: bool = False
    is_required: bool = False
    null_value: Optional[ListStrIntFloatBool] = None
    comments: str = None

    def __init__(
            self,
            section: str,
            option: str,
            dtypes: Union[str, List[str]] = 'str',
            default: Optional[ListStrIntFloatBool] = None,
            nargs: int = None,
            nargs_min: int = None,
            nargs_max: int = None,
            choice: list = None,
            value_min: Union[int, float] = None,
            value_max: Union[int, float] = None,
            is_path: bool = False,
            is_file: bool = False,
            is_time_stamp: bool = False,
            is_required: bool = False,
            null_value: Optional[ListStrIntFloatBool] = None,
            comments: str = None,
    ):
        dtypes = ensure_list_format(dtypes)

        object.__setattr__(self, "section", section)
        object.__setattr__(self, "option", option)
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
        object.__setattr__(self, "comments", comments)

        self._list_check()
        self._dtypes_check()
        self._value_min_max_check()
        self._nargs_check()
        self._check_default_choice()

    def __setattr__(self, name, value):
        raise AttributeError("ParserInfos attributes cannot be modify.")

    def __delattr__(self, name):
        raise AttributeError("ParserInfos attributes cannot be deleted.")

    def __repr__(self):
        return 'OptionInfos(\n' + str(self.__dict__).replace(",", ",\n").replace('{', '').replace('}', '') + '\n)'

    def _list_check(self):
        for option in ["choice"]:
            if self.__dict__[option] is not None:
                if not isinstance(self.__dict__[option], list):
                    raise ValueError(f"{option} argument expected a list.")

    def _dtypes_check(self):
        for e in self.dtypes:
            if e not in VALID_DTYPES:
                raise ValueError(f"{e} is not a valid dtype. dtypes must be one of {VALID_DTYPES}.")

    def _value_min_max_check(self):
        if self.value_min is not None and self.value_max is not None:
            if self.value_min > self.value_max:
                raise ValueError("value_max must be greater than value_min.")
        if self.value_min is not None or self.value_max is not None:
            if 'int' not in self.dtypes and 'float' not in self.dtypes:
                raise ValueError('value_min and value_max can only be used for int or float.')
        if isinstance(self.default, (int, float)):
            if self.value_min is not None:
                if self.default > self.value_max:
                    raise ValueError('default value must be <= value_max.')
            if self.value_max is not None:
                if self.default < self.value_min:
                    raise ValueError('default value must be >= value_min.')

    def _nargs_min_max_check(self):
        if self.nargs_min is not None and self.nargs_max is not None:
            if self.nargs_min > self.nargs_max:
                raise ValueError("value_max must be greater than value_min.")

    def _nargs_check(self):
        if self.nargs is not None and any((self.nargs_min is not None, self.nargs_max is not None)):
            raise ValueError(
                "nargs parameter cannot be used with nargs_min or nargs_max."
            )

    def _check_default_choice(self):
        if self.choice is not None and self.default is not None:
            if self.default not in self.choice:
                raise ValueError("Default value must be in given choices.")


class TaskParserError(SystemExit):
    """Handle TaskParser parsing error message."""

    def __init__(self, error: str, option_info: OptionInfos,
                 value: ListStrIntFloatBool = 'None'):
        self.error = error
        self.section = option_info.section
        self.option = option_info.option
        self.option_info = option_info
        self.value: ListStrIntFloatBool = value
        self.msg: str = ""
        self._get_error_message()
        super().__init__(click.style("TaskParserError", fg="red", bold=True) + "\n" + self.msg)

    def _get_error_message(self):
        if self.error == "dtypes":
            self.msg = f"`{self.section}/{self.option}` expected a `{' or '.join(self.option_info.dtypes)}` but " \
                       f"received `{self.value}`."
        if self.error == "nargs":
            self.msg = f"`{self.section}/{self.option}` expected "
            if self.option_info.nargs is not None:
                self.msg += f"`{self.option_info.nargs}` "
            else:
                if self.option_info.nargs_min is not None:
                    self.msg += f"a minimum of `{self.option_info.nargs_min}` "
                    if self.option_info.nargs_max:
                        self.msg += "and "
                if self.option_info.nargs_max is not None:
                    self.msg += f"a maximum of `{self.option_info.nargs_max}` "
            self.msg += f"values, but received `{len(self.value)}`."
        if self.error == "range":
            self.msg = f"`{self.section}/{self.option}` expected a value "
            if self.option_info.value_min is not None:
                self.msg += f">= than `{self.option_info.value_min}` "
                if self.option_info.value_max is not None:
                    self.msg += "and "
            if self.option_info.value_max is not None:
                self.msg += f"<= than `{self.option_info.value_max}` "
            self.msg += f", but received a value of `{self.value}`."
        if self.error == "choice":
            self.msg = f"`{self.section}/{self.option}` expected a value in `{self.option_info.choice}` but received `{self.value}`."
        if self.error == "string_format":
            self.msg = f"`{self.section}/{self.option}` is an invalid datetime format or timezone (TMZ). Use `YYYY-MM-DDThh:mm:ss.ssss` with `+HH` or ` TMZ`."
        if self.error == "path":
            self.msg = f"`{self.section}/{self.option}` path or path/to/file does not exist."
        if self.error == "file":
            self.msg = f"`{self.section}/{self.option}` file {self.value} does not exist."
        if "bool" in self.option_info.dtypes:
            self.msg += f"\nBoolean have to be express with {TRUE_VALUES} or {FALSE_VALUES}."
        if self.error == "required":
            self.msg = f"`{self.section}/{self.option}` requires a value. None were given."


ParserInfos = Dict[str, Dict[str, OptionInfos]]


class TaskParser:
    """
    Parameters
    ----------
    comment_prefixes : See ConfigParser
    inline_comment_prefixes : See ConfigParser

    Examples
    --------
    Create a Parser
    ```
        parser = TaskParser()
        parser.add_option(section="section0", option="option0", dtypes=["str"], default="")
        parser.add_option(section="section0", options="option1", dtypes=["str"], default="", is_required=True)
        parser.add_option(section="section1", options="option0", dtypes=["float"], default="", choice=[1,2,3])
    ```

    Methods
    -------
    add_option :
            section: str                              -> Section's name
            option: str                               -> Name for the option
            dtypes: Union[str, List[str]]             -> data types. Different types can be expected ex. [int, str]
                                                         Try to parse/decode into one of the dtypes returning the first
                                                         successful decoding in this order (float, int, bool, int).
            default: Optional[ListStrIntFloatBool]    -> Default value
            nargs: int                                -> Number of arguments.
            nargs_min: int                            -> Minimum number of arguments. Can't be used with nargs.
            nargs_max: int                            -> Maximum number of arguments. Can't be used with nargs.
            choice: list                              -> List of choices.
            value_min: Union[int, float]              -> Minimum numerical value.
            value_max: Union[int, float]              -> Maximum numerical value.
            is_path: bool                             -> If an existing path is expected.
            is_file: bool                             -> If an existing file is expected.
            is_time_stamp: bool                       -> If a timestamp is expected
            is_required: bool                         -> If a value is required.
            null_value: Optional[ListStrIntFloatBool] -> Returns `null_value` for empty filled. Default None.
            comments: str                             -> Comments to add to the ini. Comments are preceded by `;;`.

    load(input_filename)                         -> load '.ini' and into a dictionary with formatted(parse) values.
    write(output_filename)                       -> writes a .ini file.
    write_from_dict(output_filename, dictionary) -> format and write from a dictionary.
    as_dict(with_default=False)                  -> dictionary empty fields (null_value).
    parser(with_default=False)                   -> rawconfigparser with empty fields (null_value).
    sections                                     -> list of the section.
    options(section)                             -> list option of a section.
    format_parser_dict(dictionary)               -> formatted dictionary parser.
    format_option(value, section, option)        -> formatted(parse) single value.

    Notes
    -----
    For add_option, a series of check-up is done to ensure coherence e.g. `value_min < default < value_max`.
    Check-up are yet not done to check if a given `default` value is valid for is_path/is_file/is_time_stamp = True and
    that the correct dtypes is 'str'.
    .
    """

    def __init__(self, inline_comment_prefixes: Tuple[str] = (';;',), comment_prefixes: Tuple[str] = (';;',)):
        self._parser_infos: ParserInfos = {}
        self.inline_comment_prefixes: Tuple[str] = inline_comment_prefixes
        self.comment_prefixes: Tuple[str] = comment_prefixes

    @property
    def parser_infos(self):
        """Return a 2 layers deep copy of self._parser_infos.
        Point to the same immutable objects."""
        return dict((zip(self._parser_infos.keys(), map(lambda x: {**x}, self._parser_infos.values()))))

    @property
    def sections(self):
        return list(self._parser_infos)

    def options(self, section: str):
        if section in self.sections:
            return list(self._parser_infos[section])
        raise ValueError(f'{section} section does not exist.')

    def add_option(
            self,
            section: str,
            option: str,
            dtypes: Union[str, List[str]] = 'str',
            default: Optional[ListStrIntFloatBool] = None,
            nargs: int = None,
            nargs_min: int = None,
            nargs_max: int = None,
            choice: list = None,
            value_min: Union[int, float] = None,
            value_max: Union[int, float] = None,
            is_path: bool = False,
            is_file: bool = False,
            is_time_stamp: bool = False,
            is_required: bool = False,
            null_value: Optional[ListStrIntFloatBool] = None,
            comments: str = None
    ):
        if section not in self._parser_infos:
            self._parser_infos[section] = {}
        self._parser_infos[section][option] = OptionInfos(
            section, option, dtypes, default, nargs, nargs_min, nargs_max, choice,
            value_min, value_max, is_path, is_file, is_time_stamp, is_required, null_value, comments
        )

    def configparser(self, with_default: bool = True, with_comments: bool = False) -> RawConfigParser:
        """Return a RawConfigParser of the TaskParser.

        Parameters
        ----------
        with_default:
            If True, uses the default value.
        with_comments
            If True, the comments are added.

        Returns
        -------

        """
        configparser = _rawconfigparser(inline_comment_prefixes=self.inline_comment_prefixes,
                                        comment_prefixes=self.comment_prefixes)
        for section, options in self._parser_infos.items():
            configparser.add_section(section)
            for option, option_infos in options.items():
                if with_default is False or option_infos.default is None:
                    value = ""
                else:
                    value = str(option_infos.default)
                if with_comments is True and self._parser_infos[section][option].comments is not None:
                    value += f"    ;;{self._parser_infos[section][option].comments}"
                configparser[section][option] = value

        return configparser

    def as_dict(self, with_default: bool = True) -> ParserDict:
        config = {k: {} for k in self._parser_infos.keys()}
        for section, options in self._parser_infos.items():
            for option, option_infos in options.items():
                if with_default is True:
                    config[section][option] = option_infos.default
                else:
                    config[section][option] = option_infos.null_value

        return config

    def format_parser_dict(
            self, parser_dict: ParserDict,
            add_missing: bool = True,
            new_values_dict: Optional[ParserDict] = None,
            format_options: bool = True,
            file_path: Optional[str] = None
    ):
        """

        New values are updated as string before being formatted.

        Parameters
        ----------
        parser_dict :
        add_missing :
            If True, missing will be added to the output with null value.
        new_values_dict :
            Dictionary of the same structure of the parser with new values.
        format_options :
           If True, the loaded config options will be formatted.
        file_path :
            Absolute path to the configfile to replace relative path by absolute path.

        Returns
        -------

        """

        if new_values_dict is not None:
            _update_parser_values(parser_dict=parser_dict, values_dict=new_values_dict)

        if format_options is True:
            _format_parser_options(parser_dict=parser_dict, parser_infos=self._parser_infos, file_path=file_path)

        if add_missing is True:
            _add_missing_options(parser_dict, self._parser_infos)

    def format_option(self, value, section: str, option: str) -> ListStrIntFloatBool:
        value = str(value)
        if section not in self._parser_infos:
            raise ValueError(f"{section} section has no option {option}")
        if option not in self._parser_infos[section]:
            raise ValueError(f"{section} section has no option {option}")
        return _format_option(value, self._parser_infos[section][option])

    def load(self, filename: str,
             add_missing: bool = True,
             new_values_dict: Optional[dict] = None,
             format_options: bool = True) -> ParserDict:
        """...

        Parameters
        ----------
        filename :
            path/to/file to load.
        add_missing :
            If True, missing will be added to the output with null value.
        new_values_dict :
            Dictionary of the same structure of the parser with new values.
        format_options :
           If True, the loaded config options will be formatted.

        Returns
        -------
        Dictionary of the loaded config file.

        """
        file_path = str(Path(filename).absolute().parent)

        parser = _rawconfigparser(inline_comment_prefixes=self.inline_comment_prefixes,
                                  comment_prefixes=self.comment_prefixes)
        parser.read(filename)
        parser_dict = parser._sections

        self.format_parser_dict(parser_dict, add_missing, new_values_dict, format_options, file_path)

        return parser_dict

    def write(self, filename: str,
              new_values_dict: Optional[ParserDict] = None,
              with_default: bool = True,
              with_comments: bool = True):
        """

        Parameters
        ----------
        filename :
            path/to/filename
        new_values_dict :
            dictionary of the same structure as the parser with new option values to use. (update)
        with_default :
            If True, add default values.
        with_comments :
            If True, the comments are added.
        """
        if new_values_dict is None:
            with open(Path(filename).with_suffix('.ini'), "w") as f:
                self.configparser(with_default=with_default,
                                  with_comments=with_comments).write(f)
        else:
            self.write_from_dict(filename,
                                 parser_dict=self.as_dict(with_default=with_default),
                                 add_missing=True,
                                 new_values_dict=new_values_dict,
                                 format_options=False,
                                 with_comments=with_comments)

    def write_from_dict(self, filename: str,
                        parser_dict: ParserDict,
                        add_missing: bool = True,
                        new_values_dict: Optional[ParserDict] = None,
                        format_options: bool = True,
                        with_comments: bool = True
                        ):
        """

        Parameters
        ----------
        filename :
            path/to/filename
        parser_dict :
            from the method Parser.
        add_missing :
            If True, adds the missing option with empty fields.
        new_values_dict:
            dictionary of the same structure as the configparser with new option values to use.
        format_options :
           If True, the loaded config options will be formatted.
        with_comments :
            If True, the comments are added

        """
        self.format_parser_dict(parser_dict, add_missing=add_missing, new_values_dict=new_values_dict,
                                format_options=format_options)

        configparser = self._configparser_from_parser_dict(parser_dict, with_comments=with_comments)

        with open(Path(filename).with_suffix('.ini'), "w") as f:
            configparser.write(f)

    def _configparser_from_parser_dict(self, parser_dict: ParserDict, with_comments: bool = True) -> RawConfigParser:
        """Return a RawConfigParser of a parser config

        Parameters
        ----------
        parser_dict :
            from the method Parser.
        with_comments :
            If True, the comments are added

        Returns
        -------

        """
        configparser = _rawconfigparser(inline_comment_prefixes=self.inline_comment_prefixes,
                                        comment_prefixes=self.comment_prefixes)
        for section, options in self.parser_infos.items():
            if section in parser_dict:
                configparser.add_section(section)
                for option in options:
                    if option in parser_dict[section]:
                        value = parser_dict[section][option]
                        comments = ""
                        if option in self._parser_infos[section]:
                            if value == self._parser_infos[section][option].null_value:
                                value = None
                            if with_comments is True and self._parser_infos[section][option].comments is not None:
                                comments += f"    ;;{self._parser_infos[section][option].comments}"
                        if value is None:
                            value = ""
                        else:
                            value = str(value)
                        configparser[section][option] = value + comments

        return configparser


def _rawconfigparser(inline_comment_prefixes: Tuple[str] = (';;',), comment_prefixes: Tuple[str] = (';;',)):
    parser: RawConfigParser = RawConfigParser(inline_comment_prefixes=inline_comment_prefixes,
                                              comment_prefixes=comment_prefixes)
    parser.optionxform = str
    return parser


def _update_parser_values(parser_dict: dict, values_dict: Optional[dict] = None):
    """Value are updated before any option value decoding."""
    for section, options in values_dict.items():
        if section in parser_dict:
            for option, value in options.items():
                if value is None:
                    parser_dict[section][option] = ""
                else:
                    parser_dict[section][option] = str(value)


def _format_parser_options(parser_dict: dict, parser_infos: ParserInfos, file_path: Optional[str] = None):
    """Format config options for processing.

    - Convert the sensor specific configuration parameters values to the right
    data type, skipping `None` value set previously.
    - Boolean `True` entry have to be in ['True','true','1', 'On,'on'] else, it considered `False`.

    Raises
    ------
    TaskFileError :
        Error are risen if the options value cannot be converted to the right dtypes,
        length, value, choice,  etc.

    Notes
    -----
    Value are turned into string before being pass to _format_option since _format_option expect a string and the
    algorithm were design to accept string.

    """
    for section, options in parser_infos.items():
        if section in parser_dict:
            for option in options:
                if option in parser_dict[section]:
                    option_info = parser_infos[section][option]
                    value = parser_dict[section][option]
                    if value == "":
                        _value = option_info.null_value
                        if option_info.is_required is True:
                            raise TaskParserError("required", option_info, value)
                    else:
                        _value = _format_option(str(parser_dict[section][option]), option_info, file_path)

                    parser_dict[section][option] = _value


def _add_missing_options(parser_dict: dict, parser_infos: ParserInfos):
    """Check for missing sections or options compared to the expected parser
       - Adds the options or section if needed with value == ParserInfo.null_value
       Notes
       -----
       This prevents missing key error later in the processing without needing
       to add tons of conditional statements.
       """
    for section, options in parser_infos.items():
        if section not in parser_dict:
            parser_dict[section] = {}
        for option in options.keys():
            if option not in parser_dict[section]:
                parser_dict[section][option] = parser_infos[section][option].null_value


def _format_option(value: str, option_info: OptionInfos, file_path: Optional[str] = None):
    """
    Notes
    -----
    The quick fixes below are needed for OptionInfos.is_file = True due to get_file_from_expression
    that always return a list.
    """
    if option_info.nargs or option_info.nargs_min or option_info.nargs_max:
        value = _get_sequence_from_string(value)
        _check_options_length(value, option_info)
        values = []
        for i, _value in enumerate(value):
            _value = _format_option_type(_value, option_info, file_path)
            if isinstance(_value, list):  # quick fix
                values += _value
            else:
                values.append(_value)
        value = values
    else:
        value = _format_option_type(value, option_info, file_path)
        if isinstance(value, list):  # quick fix
            value = value[0]

    return value


def _format_option_type(value: str, option_info: OptionInfos, file_path: Optional[str] = None):
    """Format option to the right dtypes.
    - Checks if value is outside option_info.min_value and option_info.max_value.
    - Check if values is within the option_info.choice."""

    try:
        value = _format_value_dtypes(value, option_info.dtypes)
    except ValueError:
        raise TaskParserError("dtypes", option_info, value)

    if option_info.choice is not None:
        if value not in option_info.choice:
            raise TaskParserError("choice", option_info, value)

    if isinstance(value, str):
        if option_info.is_path is True:
            value = Path(file_path).joinpath(Path(value)).resolve()
            if not any((value.is_dir(), value.parent.is_dir())):
                raise TaskParserError("path", option_info, str(value))
            value = str(value)

        elif option_info.is_file is True:
            if file_path is not None:
                value = str(Path(file_path).joinpath(Path(value)).resolve())
            else:
                value = str(Path(value))
            try:
                value = get_files_from_expression(value)
            except FileNotFoundError:
                raise TaskParserError('file', option_info, value)

        elif option_info.is_time_stamp is True:
            value = _format_timestring(value, option_info)

    if isinstance(value, (int, float)) and (option_info.value_min or option_info.value_max):
        _check_option_min_max(value, option_info)

    return value


def _format_timestring(value: str, option_info: OptionInfos) -> str:
    try:
        date_time = dateutil.parser.parse(value)
        if date_time.tzinfo is not None:
            date_time = date_time.astimezone(timezone.utc)
        return date_time.strftime('%Y-%m-%dT%H:%M:%S.f')[:-2]
    except dateutil.parser.ParserError:
        raise TaskParserError("string_format", option_info, value)


def _format_value_dtypes(value: str, dtypes: List[str]) -> StrIntFloatBool:
    value = _remove_quotes(value)

    if "int" in dtypes or 'float' in dtypes:
        try:
            float_value = float(value)
            int_or_float = int(float_value)
            if 'float' in dtypes and float_value != int_or_float:
                int_or_float = float_value
            return int_or_float
        except ValueError:
            pass
    if "bool" in dtypes:
        if value in [*TRUE_VALUES, *FALSE_VALUES]:
            return value in TRUE_VALUES
    if 'str' in dtypes:
        return value
    raise ValueError


def _get_sequence_from_string(sequence: str) -> List:
    """Decode string containing a sequence of value.

    The sequence can be between brackets, parenthesis or nothing
    and have comma, colon, semicolon, newlines or spaces as separators.

    Example
    -------
    _format_string_list'(arg1, arg2, arg3)' -> [arg1, arg2, arg3]
    """
    for sep in (" ", "\n", "(", ")", "[", "]", "'", '"'):
        sequence = sequence.replace(sep, ",")

    return list(filter(None, sequence.split(",")))


def _remove_quotes(value: str) -> str:
    """Remove any redundant quotes around the string."""
    for quotes in ["'", '"']:
        value = value.strip(quotes)
    return value


def _check_options_length(value: ListStrIntFloatBool, option_info: OptionInfos):
    if option_info.nargs:
        if len(value) != option_info.nargs:
            raise TaskParserError("nargs", option_info, value)
    if option_info.nargs_max:
        if len(value) > option_info.nargs_max:
            raise TaskParserError("nargs", option_info, value)
    if option_info.nargs_min:
        if len(value) < option_info.nargs_min:
            raise TaskParserError("nargs", option_info, value)


def _check_option_min_max(value: StrIntFloatBool, option_info: OptionInfos):
    if option_info.value_max is not None:
        if value > option_info.value_max:
            raise TaskParserError("range", option_info, value)
    if option_info.value_min is not None:
        if value < option_info.value_min:
            raise TaskParserError("range", option_info, value)

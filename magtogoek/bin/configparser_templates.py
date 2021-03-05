"""
author: Jérôme Guay
date: March 4, 2021

This script is called by magtogoek_command.py

This modules has functions to make the different sections of
the configparser files and to produce it.

NOTE: More comments should be added in the configparser files.
NOTE: Missing,fonctions to open the config files.
"""
import configparser
import typing as tp
from pandas import Timestamp
import getpass

# Defaults attrs and value of the parser sections
default_input_attrs = {"input_files": "", "platform_file": ""}
default_output_attrs = {"netcdf_output": "", "odf_output": ""}
default_netcdf_cf_attrs = {
    "Conventions": "CF 1.8",
    "title": "",
    "institution": "",
    "summary": "",
    "references": "https://github.com/JeromeJGuay/magtogoek",
    "comments": "",
    "naming_authority": "BODC, SDC, CF, MEDS",
}
default_project_attrs = {
    "project": "",
    "sea_name": "",
    "sea_code": "",
}
default_cruise_attrs = {
    "country_institue_code": "",
    "cruise_number": "",
    "organization": "",
    "chief_scientist": "",
    "start_date": "",
    "end_date": "",
}
default_global_attrs = {
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
    "standard_name_vocabulary": "CF v.52",  # NOTE update ?
    "aknowledgment": "",
}
default_adcp_attrs = dict(
    ADCP_PROCESSING=dict(
        yearbase=("", str),
        adcp_orientation=("down", str),
        sonar=("", str),
        GPS_file=("", str),
    ),
    ADCP_QUALITY_CONTROL=dict(
        quality_control=(True, bool),
        amplitude_threshold=(0, float),
        percentgood_threshold=(64, float),
        correlation_threshold=(90, float),
        horizontal_velocity_threshold=(5, float),
        vertical_velocity_threshold=(5, float),
        error_velocity_threshold=(5, float),
        side_lobe_correction=(True, bool),
        pitch_threshold=(20, float),
        roll_threshold=(20, float),
        trim_leading_data=("", str),
        trim_trailling_data=("", str),
        platform_motion_correction=(True, bool),
    ),
    ADCP_OUTPUT=dict(
        merge_output_file=(True, bool),
        bodc_name=(True, bool),
        drop_percent_good=(True, bool),
        drop_correlation=(True, bool),
        drop_amplitude=(True, bool),
        make_figures=(True, bool),
        make_log=(True, bool),
    ),
)


def make_configparser(filename: str, sensor_type: str, options: tp.Dict = None) -> None:
    """make a configparser `.ini` file.

    parameters:
    -----------
    filename:
        name of the config(.ini) file

    sensor_type:
        used to return sensor_type config.
    options:
        options to be set in the configparser file.
    """
    linewidth = 70  # width of the .ini comments sections

    # updates input and ouput sections from the options.
    if options:
        for key in default_input_attrs.keys():
            if options[key] is not None:
                default_input_attrs[key] = options[key]
        for key in default_output_attrs.keys():
            if options[key] is not None:
                default_input_attrs[key] = options[key]

    # making config and adding sections
    config = _header(sensor_type, linewidth)
    _input_files(config, default_input_attrs, linewidth)
    _output_files(config, default_output_attrs, linewidth)

    # adding the sensor_type sections
    if sensor_type == "adcp":
        if options:
            _update_adcp_values(default_adcp_attrs, options)
        adcp_configparser(config, default_adcp_attrs, linewidth)
    else:
        print("Invalid sensor_type. Must be one of: `adcp`")
        exit()

    # adding some more global attrs sections to the configparser.
    _project(config, default_project_attrs, linewidth)
    _cruise(config, default_cruise_attrs, linewidth)
    _netcdf_cf(config, default_netcdf_cf_attrs, linewidth)
    _gloabal_attributes(config, default_global_attrs, linewidth)
    _additional_global_attributes(config, linewidth)

    # make the configfile
    _configparser2ini(config, filename)


def _update_adcp_values(config: tp.Type[configparser.ConfigParser], options: tp.Dict):
    """updates adcp config sections with command line options.

    structure: [section][attrs] = (value, type)
    """
    for section in ["ADCP_PROCESSING", "ADCP_QUALITY_CONTROL", "ADCP_OUTPUT"]:
        for key in default_adcp_attrs[section].keys():
            if options[key] is not None:
                default_adcp_attrs[section][key] = (
                    options[key],
                    default_adcp_attrs[section][key][1],
                )


def _configparser2ini(config: tp.Type[configparser.ConfigParser], filename: str):
    """make .ini file"""
    with open(filename, "w") as configfile:
        config.write(configfile)


def _header(sensor_type: str, linewidth: int) -> tp.Type[configparser.ConfigParser]:
    """initialize the configparser"""
    date = Timestamp.now().strftime("%Y-%m-%d")
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


def _input_files(
    config: tp.Type[configparser.ConfigParser], attrs: tp.Dict, linewidth: int
):
    """adds input sections with attrs"""
    section_name = "INPUT"
    config[section_name] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| input file: Expression identifying the file or files to be process.".ljust(
            linewidth, " "
        )
        + "|": None,
        ";| platform file: (file name) Can be omitted.".ljust(linewidth, " ")
        + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
    }
    for key, item in attrs.items():
        config[section_name][f"\t {key}"] = str(item)


def _output_files(
    config: tp.Type[configparser.ConfigParser], attrs: tp.Dict, linewidth: int
):
    """add output secionts with attrs"""
    section_name = "OUTPUT"
    config[section_name] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Expression for odf and netcdf output files names.".ljust(linewidth, " ")
        + "|": None,
        ";| Leave blank for `False`.".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
    }
    for key, item in attrs.items():
        config[section_name][f"\t {key}"] = str(item)


def _netcdf_cf(
    config: tp.Type[configparser.ConfigParser], attrs: tp.Dict, linewidth: int
):
    """add netcdf CF conventions sections with attrs"""
    section_name = "NETCDF_CF"
    config[section_name] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Global attibutes for CF conventions".ljust(linewidth, " ") + "|": None,
        ";| Blanks are omitted.".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
    }
    for key, item in attrs.items():
        config[section_name][f"\t {key}"] = item


def _project(
    config: tp.Type[configparser.ConfigParser], attrs: tp.Dict, linewidth: int
):
    """add project sections with attrs"""
    section_name = "PROJECT"
    config[section_name] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Global attributes for project".ljust(linewidth, " ") + "|": None,
        ";| Blanks are omitted.".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
    }
    for key, item in attrs.items():
        config[section_name][f"\t {key}"] = str(item)


def _cruise(config: tp.Type[configparser.ConfigParser], attrs: tp.Dict, linewidth: int):
    """add cruise sections with attrs"""
    section_name = "CRUISE"
    config[section_name] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Global attributes for cruise".ljust(linewidth, " ") + "|": None,
        ";| Blanks are omitted".ljust(linewidth, " ") + "|": None,
        ";| chief_scientist: overwrites the value in the platform file.".ljust(
            linewidth, " "
        )
        + "|": None,
        ";| Date format: YYYY-MM-DDTHH:MM:SS FIXME ".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
    }
    for key, item in attrs.items():
        config[section_name][f"\t {key}"] = str(item)


def _gloabal_attributes(
    config: tp.Type[configparser.ConfigParser], attrs: tp.Dict, linewidth: int
):
    """add global attributes sections with attrs"""
    section_name = "GLOBAL_ATTRIBUTES"
    config[section_name] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Global attributes ".ljust(linewidth, " ") + "|": None,
        ";| Blanks are omitted".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
    }
    for key, item in attrs.items():
        config[section_name][f"\t {key}"] = str(item)


def _additional_global_attributes(
    config: tp.Type[configparser.ConfigParser], linewidth: int
):
    """add addtionnal global attributes sections"""
    config["ADDITIONAL_GLOBAL_ATTRIBUTES"] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Insert addittional attributes below.".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
    }


def adcp_configparser(
    config: tp.Type[configparser.ConfigParser], attrs: tp.Dict, linewidth: int
) -> None:
    """add adcp sections with attributes"""
    section_name = "ADCP_PROCESSING"
    config[section_name] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| yearbase: year that the sampling started. ex: `1970`".ljust(linewidth, " ")
        + "|": None,
        ";| adcp_orientation: `down` or `up`. (horizontal no supported)".ljust(
            linewidth, " "
        )
        + "|": None,
        ";| sonar:  Must be one of `wh`, `os`, `bb`, `nb` or `sw`".ljust(linewidth, " ")
        + "|": None,
        ";| GPS_file: path/to/netcdf4 containing the gps track,".ljust(linewidth, " ")
        + "|": None,
        ";|   `longitude` and `latitude`, of the platform. If provided,".ljust(
            linewidth, " "
        )
        + "|": None,
        ";|    will be used instead of GPS data in the adcp file.(optional) ".ljust(
            linewidth, " "
        )
        + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
    }
    for key, item in attrs[section_name].items():
        config[section_name][f"\t {key}"] = str(item[0])

    section_name = "ADCP_QUALITY_CONTROL"
    config[section_name] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| If quality_control is `False`, no quality control is carried out .".ljust(
            linewidth, " "
        )
        + "|": None,
        ";| Blanks are omitted or set False.".ljust(linewidth, " ") + "|": None,
        ";| Trims format `YYYYMMDDHHMMSS`".ljust(linewidth, " ") + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
    }
    for key, item in attrs[section_name].items():
        config[section_name][f"\t {key}"] = str(item[0])

    section_name = "ADCP_OUTPUT"
    config[section_name] = {
        ";#".ljust(linewidth, "-") + "#": None,
        ";| Set True or False. (FIXME)".ljust(linewidth, " ") + "|": None,
        ";| If bodc_name False, generic variable names are used.".ljust(linewidth, " ")
        + "|": None,
        ";#".ljust(linewidth, "-") + "# ": None,
    }
    for key, item in attrs[section_name].items():
        config[section_name][f"\t {key}"] = str(item[0])

    return config

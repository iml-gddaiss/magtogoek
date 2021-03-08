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
"""
from configparser import ConfigParser
import typing as tp
from pandas import Timestamp
import getpass


class ConfigFile(ConfigParser):
    """FIXME"""

    def __init__(self, filename):
        """
        parameters:
        -----------
        filename:
            name of the config(.ini) file
        """

        self.filename = filename
        self.valid_sensor_type = ["adcp"]

    def __repr__(self):
        try:
            output = ""
            for key, item in self._sections.items():
                output += f"[{key}]\n"
                for subkey, subitem in item.items():
                    if subitem is not None:
                        output += f"{subkey}: {subitem}\n"
                    else:
                        output += f"{subkey}\n"

            return output
        except AttributeError:
            return "<%s instance at %s>" % (self.__class__.__name__, id(self))

    def make(
        self,
        sensor_type: str,
        options: tp.Dict = None,
        comments_section_width: int = 70,
    ):
        """make a ConfigParser

        sections:
        ---------
        [header]
        [input_files]
        [output_files]
        [`sensor_type`_processing]
        [project]
        [cruise]
        [netcdf_cf]
        [gloabal_attributes]
        [additional_global_attributes]

        parameters:
        -----------
        sensor_type:
            Used to add the `sensor_type` config parameters.

        options:
            options passed update the default value of the parameters.
            Only for. input, ouput, sensor_type sections.
        """
        super(ConfigFile, self).__init__(comment_prefixes=";", allow_no_value=True)
        self.optionxform = str

        self.sensor_type = sensor_type
        self.update_options = options
        self.comments_section_width = comments_section_width

        if self.sensor_type not in self.valid_sensor_type:
            raise ValueError("Invalid sensor_type. Must be one of: `adcp`")

        self._init_sections_params()

        self._header()
        self._input_files()
        self._output_files()

        if sensor_type == "adcp":
            self._adcp_processing()

        self._project()
        self._cruise()
        self._netcdf_cf()
        self._gloabal_attributes()
        self._additional_global_attributes()

        return self

    def save(self):
        """save to a .ini file"""
        with open(self.filename, "w") as cf:
            self.write(cf)

    def load(self):
        """ read `ini` and set sensor_type"""
        self._inline_comment_prefixes = "#"
        self._comment_prefixes = ";"
        super(ConfigFile, self).read(self.filename)

    def _init_sections_params(self):
        """FIXME"""

        self._input_params = {"input_files": ("", str), "platform_file": ("", str)}
        self._output_params = {"netcdf_output": ("", str), "odf_output": ("", str)}
        self._netcdf_cf_params = {
            "Conventions": ("CF 1.8", str),
            "title": ("", str),
            "institution": ("", str),
            "summary": ("", str),
            "references": ("https://github.com/JeromeJGuay/magtogoek", str),
            "comments": ("", str),
            "naming_authority": ("BODC, SDC, CF, MEDS", str),
        }
        self._project_params = {
            "project": ("", str),
            "sea_name": ("", str),
            "sea_code": ("", str),
        }
        self._cruise_params = {
            "country_institue_code": ("", str),
            "cruise_number": ("", str),
            "organization": ("", str),
            "chief_scientist": ("", str),
            "start_date": ("", str),
            "end_date": ("", str),
        }
        self._global_attrs_params = {
            "date_created": ("", str),
            "date_created": ("", str),
            "data_type": ("", str),
            "data_subtype": ("", str),
            "country_code": ("", str),
            "keywords": ("", str),
            "publisher_email": ("", str),
            "creator_type": ("", str),
            "publisher_name": ("", str),
            "keywords_vocabulary": ("", str),
            "standard_name_vocabulary": ("CF v.52", str),
            "aknowledgment": ("", str),
        }

        self._adcp_params = dict(
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

        if self.update_options is not None:
            for key in self._input_params.keys():
                if self.update_options[key] is not None:
                    self._input_params[key] = (
                        self.update_options[key],
                        self._input_params[key][1],
                    )
            for key in self._output_params.keys():
                if self.update_options[key] is not None:
                    self._output_params[key] = (
                        self.update_options[key],
                        self._output_params[key][1],
                    )

        sensor_params = {"adcp": self._adcp_params}[self.sensor_type]

        for section_key, section in sensor_params.items():
            print(section_key)
            for param_key, param in section.items():
                if self.update_options[param_key] is not None:
                    sensor_params[section_key][param_key] = (
                        self.update_options[param_key],
                        param[1],
                    )

    def _header(self):
        """add a header to the configparser"""

        date = Timestamp.now().strftime("%Y-%m-%d")
        user = getpass.getuser()

        self["HEADER"] = {
            ";#".ljust(self.comments_section_width, "-") + "#": None,
            f";| Configurations file for {self.sensor_type} data processing".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            f";| Created on {date}".ljust(self.comments_section_width, " ") + "|": None,
            f";| By {user}".ljust(self.comments_section_width, " ") + "|": None,
            ";#".ljust(self.comments_section_width, "-") + "# ": None,
        }

    def _input_files(self):
        """adds input sections with attrs"""
        section_name = "INPUT"
        self[section_name] = {
            ";#".ljust(self.comments_section_width, "-") + "#": None,
            ";| input file: Expression identifying the file or files to be process.".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";| platform file: (file name) Can be omitted.".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";#".ljust(self.comments_section_width, "-") + "# ": None,
        }
        for key, item in self._input_params.items():
            self[section_name][f"\t {key}"] = str(item[0])

    def _output_files(self):
        """add output secionts with attrs"""
        section_name = "OUTPUT"
        self[section_name] = {
            ";#".ljust(self.comments_section_width, "-") + "#": None,
            ";| Expression for odf and netcdf output files names.".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";| Leave blank for `False`.".ljust(self.comments_section_width, " ")
            + "|": None,
            ";#".ljust(self.comments_section_width, "-") + "# ": None,
        }
        for key, item in self._output_params.items():
            self[section_name][f"\t {key}"] = str(item[0])

    def _netcdf_cf(self):
        """add netcdf CF conventions sections with attrs"""
        section_name = "NETCDF_CF"
        self[section_name] = {
            ";#".ljust(self.comments_section_width, "-") + "#": None,
            ";| Global attibutes for CF conventions".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";| Blanks are omitted.".ljust(self.comments_section_width, " ")
            + "|": None,
            ";#".ljust(self.comments_section_width, "-") + "# ": None,
        }
        for key, item in self._output_params.items():
            self[section_name][f"\t {key}"] = str(item[0])

    def _project(self):
        """add project sections with attrs"""
        section_name = "PROJECT"
        self[section_name] = {
            ";#".ljust(self.comments_section_width, "-") + "#": None,
            ";| Global attributes for project".ljust(self.comments_section_width, " ")
            + "|": None,
            ";| Blanks are omitted.".ljust(self.comments_section_width, " ")
            + "|": None,
            ";#".ljust(self.comments_section_width, "-") + "# ": None,
        }
        for key, item in self._project_params.items():
            self[section_name][f"\t {key}"] = str(item[0])

    def _cruise(self):
        """add cruise sections with attrs"""
        section_name = "CRUISE"
        self[section_name] = {
            ";#".ljust(self.comments_section_width, "-") + "#": None,
            ";| Global attributes for cruise".ljust(self.comments_section_width, " ")
            + "|": None,
            ";| Blanks are omitted".ljust(self.comments_section_width, " ") + "|": None,
            ";| chief_scientist: overwrites the value in the platform file.".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";| Date format: YYYY-MM-DDTHH:MM:SS FIXME ".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";#".ljust(self.comments_section_width, "-") + "# ": None,
        }
        for key, item in self._cruise_params.items():
            self[section_name][f"\t {key}"] = str(item[0])

    def _gloabal_attributes(self):
        """add global attributes sections with attrs"""
        section_name = "GLOBAL_ATTRIBUTES"
        self[section_name] = {
            ";#".ljust(self.comments_section_width, "-") + "#": None,
            ";| Global attributes ".ljust(self.comments_section_width, " ") + "|": None,
            ";| Blanks are omitted".ljust(self.comments_section_width, " ") + "|": None,
            ";#".ljust(self.comments_section_width, "-") + "# ": None,
        }
        for key, item in self._global_attrs_params.items():
            self[section_name][f"\t {key}"] = str(item[0])

    def _additional_global_attributes(self):
        """add addtionnal global attributes sections"""
        self["ADDITIONAL_GLOBAL_ATTRIBUTES"] = {
            ";#".ljust(self.comments_section_width, "-") + "#": None,
            ";| Insert addittional attributes below.".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";#".ljust(self.comments_section_width, "-") + "# ": None,
        }

    def _adcp_processing(self) -> None:
        """add adcp sections with attributes"""
        section_name = "ADCP_PROCESSING"
        self[section_name] = {
            ";#".ljust(self.comments_section_width, "-") + "#": None,
            ";| yearbase: year that the sampling started. ex: `1970`".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";| adcp_orientation: `down` or `up`. (horizontal no supported)".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";| sonar:  Must be one of `wh`, `os`, `bb`, `nb` or `sw`".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";| GPS_file: path/to/netcdf4 containing the gps track,".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";|   `longitude` and `latitude`, of the platform. If provided,".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";|    will be used instead of GPS data in the adcp file.(optional) ".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";#".ljust(self.comments_section_width, "-") + "# ": None,
        }
        for key, item in self._adcp_params[section_name].items():
            self[section_name][f"\t {key}"] = str(item[0])

        section_name = "ADCP_QUALITY_CONTROL"
        self[section_name] = {
            ";#".ljust(self.comments_section_width, "-") + "#": None,
            ";| If quality_control is `False`, no quality control is carried out .".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";| Blanks are omitted or set False.".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";| Trims format `YYYYMMDDHHMMSS`".ljust(self.comments_section_width, " ")
            + "|": None,
            ";#".ljust(self.comments_section_width, "-") + "# ": None,
        }
        for key, item in self._adcp_params[section_name].items():
            self[section_name][f"\t {key}"] = str(item[0])

        section_name = "ADCP_OUTPUT"
        self[section_name] = {
            ";#".ljust(self.comments_section_width, "-") + "#": None,
            ";| Set True or False. (FIXME)".ljust(self.comments_section_width, " ")
            + "|": None,
            ";| If bodc_name False, generic variable names are used.".ljust(
                self.comments_section_width, " "
            )
            + "|": None,
            ";#".ljust(self.comments_section_width, "-") + "# ": None,
        }
        for key, item in self._adcp_params[section_name].items():
            self[section_name][f"\t {key}"] = str(item[0])


if __name__ == "__main__":
    a = ConfigFile("test.ini")
    a.make("adcp")
    a.save()

    A = ConfigParser()
    A.optionxform = str
    A.read_file(open("test.ini"))
    with open("test2.ini", "w") as f:
        A.write(f)

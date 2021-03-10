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
from configparser import ConfigParser
import typing as tp
from pandas import Timestamp
import getpass


class ConfigFile(ConfigParser):
    """FIXME"""

    def make(self, filename, sensor_type: str, updated_params: tp.Dict = None):
        """Make the ConfigFile
        -----------
        sensor_type:
            Used to add the `sensor_type` config parameters.

        updated_params:
            options passed to update the default value of the configfile
            parameters. Only input, ouput and the `sensor_type` sections
            can be updated.

        comments_section_width:
            Width of the comment section.

        """
        super(ConfigFile, self).__init__(comment_prefixes=";", allow_no_value=True)
        self.optionxform = str
        self.comments_section_width = 79

        self.filename = filename
        self.valid_sensor_type = ["adcp"]

        self.sensor_type = sensor_type
        if self.sensor_type not in self.valid_sensor_type:
            raise ValueError("Invalid sensor_type. Must be one of: `adcp`")

        self.updated_params = updated_params

        self._init_default_sections_params()
        self._init_sections_comments()

        if self.updated_params is not None:
            self._update_default_sections_params()

        self._make_section("HEADER", self._header_params, self._header_comments)
        self._make_section("INPUT", self._input_params, self._input_comments)
        self._make_section("OUTPUT", self._output_params, self._output_comments)
        if self.sensor_type == "adcp":
            self._make_section(
                "ADCP_PROCESSING",
                self._adcp_processing_params,
                self._adcp_processing_comments,
            )
            self._make_section(
                "ADCP_QUALITY_CONTROL",
                self._adcp_quality_control_params,
                self._adcp_quality_control_comments,
            )
            self._make_section(
                "ADCP_OUTPUT",
                self._adcp_output_params,
                self._adcp_output_comments,
            )
        self._make_section("PROJECT", self._project_params, self._project_comments)
        self._make_section("CRUISE", self._cruise_params, self._cruise_comments)
        self._make_section(
            "NETCDF_CF", self._netcdf_cf_params, self._netcdf_cf_comments
        )
        self._make_section(
            "GLOBAL_ATTRIBUTES",
            self._global_attributes_params,
            self._global_attributes_comments,
        )

    def save(self):
        """save to a .ini file"""
        with open(self.filename, "w") as f:
            self.write(f)

    def load(self):
        super(ConfigFile, self).read(self.filename)

    def _make_section(
        self, section_name: str, section_params: tp.Dict, section_comments: str
    ):
        """FIXME"""
        self.add_section(section_name)
        self._add_comments_to_section(
            section=self[section_name],
            comments=section_comments,
            comment_section_width=self.comments_section_width,
        )
        # add parameters to sections
        for key, item in section_params.items():
            self[section_name][key] = str(item)

    def _update_default_sections_params(self):
        """init the default params section and update them"""
        # options are only pass for input, ouput and sensor_type.
        self._update_params(self._input_params, self.updated_params)
        self._update_params(self._output_params, self.updated_params)

        if self.sensor_type == "adcp":
            self._update_params(self._adcp_processing_params, self.updated_params)
            self._update_params(self._adcp_quality_control_params, self.updated_params)
            self._update_params(self._adcp_quality_control_params, self.updated_params)

    @staticmethod
    def _update_params(section, updated_params: tp.Dict):
        """Update default param with updated params"""
        for param_key in section.keys():
            if param_key in updated_params:
                section[param_key] = updated_params[param_key]

    def _init_default_sections_params(self):
        """FIXME"""

        self._header_params = (
            {
                "sensor_type": self.sensor_type,
                "made_by": getpass.getuser(),
                "last_updated": Timestamp.now().strftime("%Y-%m-%d"),
            },
        )
        self._input_params = {"input_files": "", "platform_file": ""}
        self._output_params = {"netcdf_output": "", "odf_output": ""}
        self._netcdf_cf_params = {
            "Conventions": "CF 1.8",
            "title": "",
            "institution": "",
            "summary": "",
            "references": "https://github.com/JeromeJGuay/magtogoek",
            "comments": "",
            "naming_authority": "BODC, SDC, CF, MEDS ; comment",
        }
        self._project_params = {
            "project": "",
            "sea_name": "",
            "sea_code": "",
        }
        self._cruise_params = {
            "country_institue_code": "",
            "cruise_number": "",
            "organization": "",
            "chief_scientist": "",
            "start_date": "",
            "end_date": "",
        }
        self._global_attributes_params = {
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
        }
        self._additional_global_attributes_params = {}

        self._adcp_processing_params = dict(
            yearbase="",
            adcp_orientation="down",
            sonar="",
            GPS_file="",
        )
        self._adcp_quality_control_params = dict(
            quality_control=True,
            amplitude_threshold=0,
            percentgood_threshold=64,
            correlation_threshold=90,
            horizontal_velocity_threshold=5,
            vertical_velocity_threshold=5,
            error_velocity_threshold=5,
            side_lobe_correction=True,
            pitch_threshold=20,
            roll_threshold=20,
            trim_leading_data="",
            trim_trailling_data="",
            platform_motion_correction=True,
        )
        self._adcp_output_params = dict(
            merge_output_file=True,
            bodc_name=True,
            drop_percent_good=True,
            drop_correlation=True,
            drop_amplitude=True,
            make_figures=True,
            make_log=True,
        )

    @staticmethod
    def _add_comments_to_section(section, comments: str, comment_section_width: int):
        """Add comments to configparser section"""
        comments = comments.split("\n")
        section[";#".ljust(comment_section_width, "-") + "#"] = None
        for line in comments:
            section[(";|" + line).ljust(comment_section_width, " ") + "|"] = None

        section[";#".ljust(comment_section_width, "-") + "# "] = None

    def _init_sections_comments(self):
        date = Timestamp.now().strftime("%Y-%m-%d")
        user = getpass.getuser()

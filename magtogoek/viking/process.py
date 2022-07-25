"""
This script has to functions to process and quick process viking buoy data.
These functions are called by the app command `process` and `quick viking`.

Date: July 25 2022
Made by: jeromejguay

METEOCE BODC:
        Time                                                 : SYTM_01 : SDN:P01::
        Longitude (East +ve)                                 : LOND_01 : SDN:P01::
        Latitude (North +ve)                                 : LATD_01 : SDN:P01::
        Horizontal Wind Speed                                : WSPD_01 : SDN:P01::EWSBZZ01
        Gust Wind Speed                                      : GSPD_01 : SDN:P01::EGTSZZ01
        Wind Direction relative to North (T)                 : WDIR_01 : SDN:P01::EWDAZZ01
        Dry Bulb Temperature                                 : DRYT_01 : SDN:P01::CTMPZZ01
        Relative Humidity                                    : RELH_01 : SDN:P01::CRELZZ01
        Atmospheric pressure                                 : ATMP_01 : SDN:P01::CAPHZZ01
        Temperature (1990 scale)                             : TE90_01 : SDN:P01::TEMPPR01
        Electrical Conductivity                              : CNDC_01 : SDN:P01::CNDCZZ01
        Practical Salinity                                   : PSAL_01 : SDN:P01::PSLTZZ01
        Sea Density                                          : DENS_01 : SDN:P01::SIGTEQ01
        Hydrogen Ion Concentration (pH)                      : PHPH_01 : SDN:P01::PHXXZZXX
        Fluorescence                                         : FLOR_01 : SDN:P01::FLUOZZZZ
        Partial pressure of carbon dioxide in the atmosphere : ACO2_01 : SDN:P01::ACO2XXXX
        Partial pressure of carbon dioxide in the water body : PCO2_01 : SDN:P01::PCO2XXXX
        Wave mean height                                     : VRMS_01 : SDN:P01::GAVHZZ01
        Wave maximum height                                  : VMXL_01 : SDN:P01::GCMXZZ01
        Wave period                                          : VTCA_01 : SDN:P01::GTAMZZ01
"""

import pandas as pd
from sys import getpass

TERMINAL_WIDTH = 80

STANDARD_ADCP_GLOBAL_ATTRIBUTES = {
    "sensor_type": "", #FIXME
    "featureType": "timeSeriesProfile",
}
DEFAULT_CONFIG_ATTRIBUTES = {
    "date_created": pd.Timestamp.now().strftime("%Y-%m-%d"),
    "publisher_name": getpass.getuser(),
    "source": "adcp",
}
VARIABLES_TO_DROP = []
GLOBAL_ATTRS_TO_DROP = []

CONFIG_GLOBAL_ATTRS_SECTIONS = ["NETCDF_CF", "PROJECT", "CRUISE", "GLOBAL_ATTRIBUTES"]

PLATFORM_TYPES = ['buoy']
DEFAULT_PLATFORM_TYPE = "buoy"
DATA_TYPE = {'buoy': 'buoy'} # MCTD ?
DATA_SUBTYPE = {'buoy':'BUOY'}

P01_CODES = dict(
     wind_mean = "EWSBZZ01",
     wind_direction_mean ="EGTSZZ01",
     wind_max="EWDAZZ01",
     atm_temperature ="CTMPZZ01",
     atm_humidity="CRELZZ01",
     atm_pressure="CAPHZZ01",
     temperature="TEMPPR01",
     conductivity="CNDCZZ01",
     salinity="PSLTZZ01",
     density="SIGTEQ01",
     ph="PHXXZZXX",
     fluorescence="FLUOZZZZ",
     co2_a="ACO2XXXX",
     co2_w="PCO2XXXX",
     wave_mean_height="GAVHZZ01",
     wave_maximal_height="GCMXZZ01",
     wave_period="GTAMZZ01"
)

VAR_TO_ADD_SENSOR_TYPE = []

TIME_ATTRS = {"cf_role": "profile_id"}

TIME_ENCODING = {
    "units": "seconds since 1970-1-1 00:00:00Z",
    "calendar": "gregorian",
    "_FillValue": None,
}
TIME_STRING_ENCODING = {"dtype": "S1"}
DEPTH_ENCODING = {
    "_FillValue": -9999.0,
    "dtype": "float32",
}

DATE_STRING_FILL_VALUE = "17-NOV-1858 00:00:00.00"  # filled value used by ODF format
QC_FILL_VALUE = 127
QC_ENCODING = {"dtype": "int8", "_FillValue": QC_FILL_VALUE}

DATA_FILL_VALUE = -9999.0
DATA_ENCODING = {"dtype": "float32", "_FillValue": DATA_FILL_VALUE}


class ProcessConfig:
    sensor_type: str = None
    platform_type: str = None
    input_files: str = None
    platform_file: str = None

    motion_correction_mode: str = None
    merge_output_files: bool = None
    bodc_name: bool = None
    force_platform_metadata: bool = None

    make_figures: bool = None
    make_log: bool = None
    odf_data: str = None
    metadata: dict = {}
    platform_metadata: dict = {}

    def __init__(self):
        self.metadata.update(DEFAULT_CONFIG_ATTRIBUTES)
        pass

    def load_from_quick(self, params):
        pass

    def load_from_process(self, config: dict) -> dict:
        """Split and flattens"""

        for section, options in config.items():
            if section in CONFIG_GLOBAL_ATTRS_SECTIONS:
                for option in options:
                    self.metadata[option] = config[section][option]
            else:
                for option in options:
                    self.__dict__[option] = config[section][option]

        return self.metadata


def process_viking(config):
    pass
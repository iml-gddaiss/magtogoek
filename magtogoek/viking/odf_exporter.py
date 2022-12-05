"""
Module to map xarray dataset to Odf

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
        u
        v
        w
        e
        bt_u
        bt_v
        bt_w
        bt_e

"""
import re
from pathlib import Path
from datetime import datetime

import pandas as pd
import xarray as xr
from typing import List, Union, Tuple, Dict, Optional
from magtogoek.odf_format import Odf, odf_time_format
from magtogoek.utils import json2dict, resolve_relative_path

REPOSITORY_ADDRESS = "https://github.com/JeromeJGuay/magtogoek"

ADCP_COMMENTS_SENSOR = {
    # 'pres': {'sensor': 'PRESSURE_SENSOR_01', 'comments': {'CODE': 'DEPH_01', 'Name': 'pressure'}},
    # 'heading': {'sensor': 'COMPAS_SENSOR_01', 'comments': {'CODE': 'HEAD_01', 'Name': 'compas'}},
    # 'roll_': {'sensor': 'INClINOMETER_SENSOR_01', 'comments': {'CODE': 'ROLL_01', 'Name': 'tilt'}},
    # 'temperature': {'sensor': 'TEMPERATURE_SENSOR_01', 'comments': {'CODE': 'TE90_01', 'Name': 'temperature'}}
}


PARAMETERS_TYPES = { #FIXME put in odf_format ?
    "int8": "INT",  # "BYTE",  # -128, 127
    "int16": "INT",  # SHORT  # -32768, 32767
    "int32": "INT",
    "int64": "LONG",
    "float16": "HALF",
    "float32": "SING",
    "float64": "DOUB",
    "|S1": "SYTM",
    "datetime64[ns]": "SYTM",
}
PARAMETERS = {
    # 'VEL': ("time", "depth", "u", "v", "w", "e"),
    # "ANC": ('time', 'pitch', 'roll_', 'heading', 'pres', 'temperature', 'lon', 'lat')
}
QC_PARAMETERS = (
    # 'u', 'v', 'w', 'pres', 'temperature'
    )
PARAMETERS_METADATA_PATH = resolve_relative_path("../files/odf_parameters_metadata.json", __file__)

PARAMETERS_METADATA = json2dict(PARAMETERS_METADATA_PATH)


def make_odf(
        dataset: xr.Dataset,
        platform_metadata: dict,
        config_attrs: dict,
        bodc_name: bool = True,
        event_qualifier2: str = 'METEOC',
        output_path: Optional[str] = None, ):
    """
    Parameters
    ----------
    dataset :
        Dataset to which add the navigation data.
    platform_metadata :
        Metadata from the platform file.
    config_attrs :
        Global attributes parameter from the configFile.
    bodc_name:
        If True, map from the generic to the BODC p01 variables names.
    event_qualifier2:
        Either `'VEL'` or `'ANC'`.
    output_path:
        If a path(str) is provided, there is two possibilities: is the path is only a directory, the file name
        will be made from the odf['file_specification']. If a file name is also provided, the 'event_qualifier2'
        will be appended if its not present in the `ouput_path`.

    """
    odf = Odf()
    #
    # _make_cruise_header(odf, platform_metadata, config_attrs)
    # _make_event_header(odf, dataset, config_attrs, event_qualifier2)
    # _make_odf_header(odf)
    # if platform_metadata['platform']["platform_type"] == "buoy":
    #     _make_buoy_header(odf, platform_metadata)
    #     _make_adcp_buoy_instrument_header(odf, dataset, platform_metadata)
    #     _make_other_buoy_instrument_header(odf, platform_metadata)
    # else:
    #     _make_instrument_header(odf, dataset)
    # _make_quality_header(odf, dataset)
    # _make_history_header(odf, dataset)
    # _make_parameter_headers(odf, dataset, PARAMETERS[event_qualifier2], bodc_name)

    if output_path is not None:
        output_path = Path(output_path)
        if output_path.is_dir():
            output_path = output_path.joinpath(odf.odf["file_specification"])
        else:
            if event_qualifier2 not in output_path.name:
                output_path = Path(str(output_path.with_suffix('')) + f'_{event_qualifier2}')
            odf.odf["file_specification"] = output_path.name

        output_path = Path(output_path).with_suffix(".ODF")
        odf.save(output_path)
        print(f"odf {event_qualifier2.upper()} file made -> {output_path}")

    return odf
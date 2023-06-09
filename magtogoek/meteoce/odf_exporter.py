"""
Module to map xarray dataset to Odf

Date: July 25 2022
Made by: jeromejguay


METEOCE BODC:
        Time                                                 : SYTM_01 : SDN:P01::ELTMEP01
        Longitude (East +ve)                                 : LOND_01 : SDN:P01::ALONZZ01
        Latitude (North +ve)                                 : LATD_01 : SDN:P01::ALATZZ01
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
        Fluorescence                                         : FLOR_01 : SDN:P01::FLUOZZZZ (new)
        par                                                  : PSAR_01 : SDN:P01::PFDPAR01 (new)
        chlorophyll                                          : CPHL_01 : SDN:P01::CPHLPR01
        Partial pressure of carbon dioxide in the atmosphere : ACO2_01 : SDN:P01::ACO2XXXX
        Partial pressure of carbon dioxide in the water body : PCO2_01 : SDN:P01::PCO2XXXX
        Wave mean height                                     : VRMS_01 : SDN:P01::GAVHZZ01
        Wave maximum height                                  : VMXL_01 : SDN:P01::GCMXZZ01
        Wave period                                          : VTCA_01 : SDN:P01::GTAMZZ01

        u
        v
        w
        e

Notes
-----

"""
from pathlib import Path
from datetime import datetime

import xarray as xr
from typing import List, Union, Tuple, Dict, Optional
from magtogoek import CONFIGURATION_PATH
from magtogoek.odf_format import Odf, odf_time_format, ODF_PARAMETERS_TYPES
from magtogoek.utils import json2dict
from magtogoek.platforms import PlatformMetadata

REPOSITORY_ADDRESS = "https://github.com/JeromeJGuay/magtogoek"

BUOY_INSTRUMENT_SENSOR = {
    'CTD_01',
    'ANEMOMETRE_01',
    'TEMPERATURE_01',
    'BAROMETRE_01',
    'POMPE_01',
    'PH_01',
    'FLUORIMETRE_01',
    'PCO2_01',
    'CAPTEUR_VAGUES_01'
    # 'pres': {'sensor': 'PRESSURE_SENSOR_01', 'comments': {'CODE': 'DEPH_01', 'Name': 'pressure'}},
    # 'heading': {'sensor': 'COMPAS_SENSOR_01', 'comments': {'CODE': 'HEAD_01', 'Name': 'compas'}},
    # 'roll_': {'sensor': 'INClINOMETER_SENSOR_01', 'comments': {'CODE': 'ROLL_01', 'Name': 'tilt'}},
    # 'temperature': {'sensor': 'TEMPERATURE_SENSOR_01', 'comments': {'CODE': 'TE90_01', 'Name': 'temperature'}}
}

INSTRUMENT_COMMENTS_SENSOR = {
    "ctd": {'sensor': 'TEMPERATURE_SENSOR_01', 'comments': {'CODE': 'TE90_01', 'Name': 'temperature'}},
    # ....
}

PARAMETERS = (
    'time',
    'lon',
    'lat',
    'mean_wind_speed',
    'max_wind_speed',
    'mean_wind_direction'
    'atm_temperature',
    'atm_humidity',
    'atm_pressure',
    'temperature',
    'conductivity',
    'salinity',
    'density',
    'dissolved_oxygen',
    'ph',
    'fluorescence',
    'chlorophyll',
    'par',
    'co2_a',
    'co2_w',
    'wave_mean_height',
    'wave_maximal_height',
    'wave_mean_period',

    #Not in ODF meteoce file but could be added
    # 'pitch',
    # 'roll_',
    # 'heading',
    # "u",
    # "v",
    # "w",
    # "e"
)

QC_PARAMETERS = () # all except time, lon, lat ? All Qc available maybe.

PARAMETERS_METADATA_PATH = CONFIGURATION_PATH.joinpath("odf_parameters_metadata.json")
PARAMETERS_METADATA = json2dict(PARAMETERS_METADATA_PATH)

EVENT_QUALIFIER2 = 'METEOCE'

def make_odf(
        dataset: xr.Dataset,
        platform_metadata: PlatformMetadata,
        sensor_id: str,
        config_attrs: dict,
        generic_variables_name: List[str],
        bodc_name: bool = True,
        output_path: Optional[str] = None,
):
    """
    Parameters
    ----------
    dataset :
        Dataset to which add the navigation data.
    platform_metadata :
        Metadata from the platform file.
    sensor_id :

    config_attrs :
        Global attributes parameter from the configFile.
    generic_variables_name :
        List of the generic name fo the variables. Python variables used in the code.
    bodc_name:
        If True, map from the generic to the BODC p01 variables names.
    output_path:
        If a path(str) is provided, there is two possibilities: is the path is only a directory, the file name
        will be made from the odf['file_specification']. If a file name is also provided, the 'event_qualifier2'
        will be appended if it's not present in the `output_path`.

    """
    odf = Odf()

    _make_cruise_header(odf, platform_metadata=platform_metadata, config_attrs=config_attrs)
    _make_event_header(odf, dataset=dataset, config_attrs=config_attrs, event_qualifier2=EVENT_QUALIFIER2)
    _make_odf_header(odf)

    _make_buoy_header(odf, platform_metadata=platform_metadata)
    #_make_adcp_buoy_instrument_header(odf, dataset, platform_metadata)
    _make_buoy_instruments_header(odf, dataset=dataset, platform_metadata=platform_metadata)


    #TODO METEO HEADER

    # _make_quality_header(odf, dataset)
    # _make_history_header(odf, dataset)
    # _make_parameter_headers(odf, dataset, PARAMETERS[event_qualifier2], bodc_name)

    if output_path is not None:
        output_path = Path(output_path)
        if output_path.is_dir():
            output_path = output_path.joinpath(odf.odf["file_specification"])
        else:
            if EVENT_QUALIFIER2 not in output_path.name:
                output_path = Path(str(output_path.with_suffix('')) + f'_{EVENT_QUALIFIER2}')
            odf.odf["file_specification"] = output_path.name

        output_path = Path(output_path).with_suffix(".ODF")
        odf.save(output_path)
        print(f"odf {EVENT_QUALIFIER2.upper()} file made -> {output_path}")


    # Change oxygen value back to ml/L
    # if dissolved oxygen units are not ml/L:
    # dissolved_oxygen_ml_per_L_to_umol_per_L(dissolved_oxygen, inverse=True)


    return odf

def _make_cruise_header(odf: Odf, platform_metadata: PlatformMetadata, config_attrs: dict):
    odf.cruise["country_institute_code"] = config_attrs["country_institute_code"]
    odf.cruise["organization"] = config_attrs["organization"]
    odf.cruise["chief_scientist"] = config_attrs["chief_scientist"]
    odf.cruise["start_date"] = odf_time_format(config_attrs["start_date"])
    odf.cruise["end_date"] = odf_time_format(config_attrs["end_date"])
    odf.cruise["cruise_number"] = config_attrs["cruise_number"]
    odf.cruise["cruise_name"] = config_attrs["cruise_name"]
    odf.cruise["cruise_description"] = config_attrs["cruise_description"]

    odf.cruise["platform"] = platform_metadata.platform.platform_name
    if platform_metadata.platform.platform_type == "buoy":
        odf.cruise["platform"] = "Oceanographic Buoy"

def _make_event_header(odf, dataset, config_attrs, event_qualifier2):
    """
    Make the event header.

    Notes
    -----
    `depth_off_bottom` is `0` if "sounding" is missing.
    """
    odf.event['data_type'] = dataset.attrs['data_type'].upper()
    odf.event["creation_date"] = odf_time_format(datetime.now())
    odf.event['orig_creation_date'] = odf_time_format(dataset.attrs['date_created'])
    if 'delta_t_sec' in dataset.attrs:
        odf.event['sampling_interval'] = dataset.attrs['delta_t_sec']
    odf.event["event_number"] = config_attrs["event_number"]
    odf.event["event_qualifier1"] = config_attrs["event_qualifier1"]
    odf.event["event_qualifier2"] = event_qualifier2
    if 'sounding' in dataset.attrs:
        odf.event['sounding'] = dataset.attrs['sounding']
    odf.event["event_comments"] = config_attrs["event_comments"]
    _set_event_header_geospatials(odf, dataset)


def _set_event_header_geospatials(odf: Odf, dataset: xr.Dataset) -> None:
    """ Set geospatial metadata from dataset.

    Sets :
     - initial_latitude, end_latitude
     - initial_latitude, end_longitude
     - depth_off_bottom

    Parameters
    ----------
    odf :
    dataset :

    Notes
    -----
    `depth_off_bottom` is `0` if "sounding" is missing.
    """
    odf.event['start_date_time'] = odf_time_format(dataset.time.values.min())
    odf.event['end_date_time'] = odf_time_format(dataset.time.values.max())

    odf.event['min_depth'] = dataset.attrs['sensor_depth'] # sensor depth comes from the config file.
    odf.event['max_depth'] = dataset.attrs['sensor_depth']

    if "lat" in dataset and "lon" in dataset:
        odf.event["initial_latitude"] = dataset.lat.values[0]
        odf.event["end_latitude"] = dataset.lat.values[-1]
        odf.event["initial_longitude"] = dataset.lon.values[0]
        odf.event["end_longitude"] = dataset.lon.values[-1]
    elif "latitude" in dataset.attrs and "longitude" in dataset.attrs:
        odf.event["initial_latitude"] = dataset.attrs["latitude"]
        odf.event["end_latitude"] = dataset.attrs["latitude"]
        odf.event["initial_longitude"] = dataset.attrs["longitude"]
        odf.event["end_longitude"] = dataset.attrs["longitude"]

    odf.event["depth_off_bottom"] = 0
    if odf.event["sounding"] is not None:
        odf.event["depth_off_bottom"] = odf.event['sounding'] - odf.event['max_depth']


def _make_odf_header(odf):
    """
    Make field specification with:
    data_type, cruise_number, event_number, event_qualifier1, event_qualifier2
    Joins with `_` and add the extension `.ODF`.
    """
    name_part = [
        odf.event["data_type"],
        odf.cruise["cruise_number"],
        odf.event["event_number"],
        odf.event["event_qualifier1"],
        odf.event["event_qualifier2"],
    ]

    odf.odf["file_specification"] = "_".join(name_part).strip("_").upper() + ".ODF"


def _make_buoy_header(odf: Odf, platform_metadata: PlatformMetadata):
    """
    Uses values in the Buoy_Specs section of the platform_file.
    """
    odf.buoy["name"] = platform_metadata.platform.platform_name
    for key in ['type', 'model', 'diameter', 'weight', 'height', 'description']:
        if key in platform_metadata.buoy_specs.__dict__:
            odf.buoy[key] = str(platform_metadata.buoy_specs.__dict__[key])


def _make_buoy_instruments_header(odf: Odf, dataset: xr.Dataset, platform_metadata: PlatformMetadata):
    """
    Parameters
    ----------
    odf
    platform_metadata

    Returns
    -------
    """
    configuration = "CONFIGURATION_01" #

    for sensor_id, sensor in platform_metadata.instruments.items():
        if sensor_id in ['platform', 'buoy_specs']:
            continue
        odf.add_buoy_instrument(sensor_id)
        odf.buoy_instrument[sensor_id]['type'] = sensor.sensor_type
        odf.buoy_instrument[sensor_id]['model'] = sensor.model
        odf.buoy_instrument[sensor_id]['serial_number'] = sensor.serial_number
        odf.buoy_instrument[sensor_id]['description'] = sensor.description

        odf.buoy_instrument[sensor_id]['inst_start_date_time'] = odf_time_format(dataset.time.values.min())
        odf.buoy_instrument[sensor_id]['inst_end_date_time'] = odf_time_format(dataset.time.values.min())

        odf.buoy_instrument[sensor_id]["buoy_instrument_comments"] = sensor.comments

        # comments = {
        #     "Firmware_Version": sensor.firmware_version,
        #     "depth_m": sensor.sensor_depth,
        #     "Comments": sensor.comments
        # }




def _make_buoy_instruments_sensor_comments(odf: Odf, sensor_id: str, dataset: xr.Dataset, generic_variables_name: List[str]):
    """

    Parameters
    ----------
    odf

    sensor_id

    dataset

    generic_variables_name :
      List of the generic name fo the variables. Python variables used in the code.

    Returns
    -------
    """
    # SENSOR_TEMPERATURE_01.CODE: XXXXX
    sensor_metadata = {
        'CODE': '',
        'name': '',
        'manufacturer': '',
        'model': '',
        'serial_number': '',
        'description': '',
        'start_time': '',
        'end_time': '',
        'depth_m': '', # or 'heights_m
        'comments': '',
    }
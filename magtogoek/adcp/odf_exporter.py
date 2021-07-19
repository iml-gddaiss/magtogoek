"""
module to map xarray dataset to Odf
"""
import re

import pandas as pd
import xarray as xr
from magtogoek.odf_format import Odf

# Add a int suffix (_01) to parameter codes increasing with each new parameter of the same type.
# - dtype : sing or doub
# Missing Metadata are in the magtogoek/files/odf_parameter.json.

TIME_TYPE = "SYTM"
TIME_FILL_VALUE = "17-NOV-1858 00:00:00.00"
REPOSITORY_ADDRESS = "https://github.com/JeromeJGuay/magtogoek"


def _make_odf_cruise_header(odf, platform: dict, global_attrs: dict):
    """
    All in the .INI cruise section
    Except:
        platform : Platform file
        cruise_description: Missing Add to ini files. #FIXME
    """
    for key in odf.cruise:
        if key in global_attrs:
            odf.cruise[key] = global_attrs[key]

    odf.cruise["platform"] = platform["platform_name"]


def _make_odf_event_header(odf, global_attrs: dict):
    """
    geospatial_lat_min
    geospatial_lat_max
    geospatial_lat_units
    geospatial_lon_min
    geospatial_lon_max
    geospatial_lon_units
    geospatial_vertical_min
    geospatial_vertical_max
    geospatial_vertical_positive
    geospatial_vertical_units
     TIME HAVE TO BE FORMATED TO ODF_STRING_FORMAT MAKE FUNCTION

     compute
      creation_date    :
      depth_off_bottom   : #FIXME
     config_file
      event_number     : Is in .INI cruise section
      data_type        : Is in .INI global_attributes section
      event_qualifier1 : #FIXME
      event_qualifier2 : #FIXME
      event_comments   : #FIXME
     dataset.attrs
      orig_creation_date : date_created
      start_date_time    : time_coverage_start
      end_date_time      : time_coverage_end
      initial_latitude   : #FIXME SUPPOSED TO BE THERE
      initial_longitude  : #FIXME SUPPOSED TO BE THERE
      end_latitude       : #FIXME SUPPOSED TO BE THERE
      end_longitude      : #FIXME SUPPOSED TO BE THERE
      min_depth          : geospatial_vertical_min
      max_depth          : geospatial_vertical_max
      sampling_interval  : sampling_interval
    plaform_file
      sounding           : sounding #FIXME look for any computation


    """
    for key in odf.event:
        if key in global_attrs:
            odf.event[key] = global_attrs[key]


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
    odf.odf["file_specification"] = "_".join(name_part).strip("_") + ".ODF"


def _make_to_odf_buoy_header(odf, platform: dict):
    """
    All in platform_specs of a platform in the platform_file
    """
    odf.buoy["name"] = platform["platform_name"]
    for key in odf.buoy:
        if key in platform["platform_specs"]:
            odf.buoy[key] = platform["platform_specs"][key]


def _nc_to_buoy_instrument_header(odf, dataset):
    """
    dataset.attrs
     type                      : manufacturer
     model                     : model
     serial_number             : serial_number
     description               : description
     inst_start_date_time      : time_coverage_start
     inst_end_date_time        : time_coverage_end
    config_file
     buoy_instrument_comments  : #FIXME
     sensors                   : #FIXME
    """
    odf.add_buoy_instrument("ADCP_01")
    for key in odf.instrument:
        if key in dataset.attrs:
            odf.instrument[key] = dataset.attrs[key]


def _nc_to_buoy_instrument_comment(odf, dataset):
    """ dataset.atttrs  'CONFIGURATION_01. FIXME"""


def _nc_to_buoy_instrument_sensors(odf, dataset):
    """FIXME
    temperature_01
    compas_01
    inclinometer_01
    pressions_01
    """


def _nc_to_odf_history_header(odf, dataset):
    """
    One history header is made by log datetime entry.
    """
    process = [
        "Data processed by Magtogoek Proccesing Software. More at " + REPOSITORY_ADDRESS
    ]
    creation_date = pd.Timestamp.now().strftime("%d-%b-%Y %H:%M:%S.%f").upper()[:-4]

    regex = "(\[.*\])\s+([0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})"
    histories = dataset.attrs["history"].strip("\n").split("\n")

    for history in histories:
        m = re.findall(regex, history)
        if m:
            odf.add_history({"creation_date": creation_date, "process": process})
            process = [m[0][0]]
            creation_date = m[0][1]
        else:
            process.append(history)
    odf.add_history({"creation_date": creation_date, "process": process})


def _nc_to_parameter_headers():
    """
    name : GF3 code plus _XX increament.
    units : from odf_
    print_field_value =
    print_decimal_value =
    """


if __name__ == "__main__":
    from magtogoek.adcp.process import _get_config
    from magtogoek.configfile import load_configfile
    from magtogoek.utils import json2dict

    nc_file = "../../test/files/iml6_2017_wh.nc"
    platform_file = "../../test/files/iml_platforms.json"
    config_file = "../../test/files/adcp_iml6_2017.ini"
    ds = xr.open_dataset(nc_file)
    platform = json2dict(platform_file)["IML6_2017"]
    _, global_attrs = _get_config(load_configfile(config_file))
    odf = Odf()

    _make_odf_cruise_header(odf, platform, global_attrs)
    _make_odf_event_header(odf, global_attrs)
    _make_odf_header(odf)
    _make_to_odf_buoy_header(odf, platform)

    _nc_to_odf_history_header(odf, ds)

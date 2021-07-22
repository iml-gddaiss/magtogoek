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

cruise_attrs = {
    "country_institute_code": ("dataset", "country_institute_code"),
    "cruise_number": ("dataset", "cruise_number"),
    "organization": ("dataset", "organization"),
    "chief_scientist": ("dataset", "chief_scientist"),
    "start_date": ("dataset", "start_date"),
    "end_date": ("dataset", "end_date"),
    "platform": ("dataset", "platform"),
    "cruise_name": ("dataset", "cruise_name"),
    "cruise_description": ("dataset", "cruise_description"),  # FIXME MISSING
    "platform": ("platform", "platform_name"),
}
event_attrs = {
    "data_type": ("dataset", "data_type"),
    "event_number": ("dataset", "event_number"),
    "orig_creation_date": ("dataset", "date_created"),
    "start_date_time": ("dataset", "start_date_time"),
    "end_date_time": ("dataset", "end_date_time"),
    "min_depth": ("dataset", "geospatial_vertical_min"),
    "max_depth": ("dataset", "geospatial_vertical_max"),
    "sampling_interval": ("dataset", "sampling_interval"),
    "sounding": ("dataset", "sounding"),
    "event_qualifier1": ("config_file", "event_qualifier1"),  # FIXME MISSING
    "event_qualifier2": ("config_file", "event_qualifier2"),  # FIXME MISSING
    "event_comments": ("config_file", "event_comments"),  # FIXME MISSING
}
event_attrs = {
    "name": ("platform_specs", "name"),
    "type": ("platform_specs", "type"),
    "model": ("platform_specs", "model"),
    "height": ("platform_specs", "height"),
    "diameter": ("platform_specs", "diameter"),
    "weight": ("platform_specs", "weight"),
    "description": ("platform_specs", "description"),
}
instrument_attrs = {
    "type": ("dataset", "manufacturer"),
    "model": ("dataset", "model"),
    "serial_number": ("dataset", "serial_number"),
    "description": ("dataset", "description"),
    "inst_start_date_time": ("dataset", "time_coverage_start"),
    "inst_end_date_time": ("dataset", "time_coverage_end"),
}


def _make_cruise_header(odf, platform: dict, global_attrs: dict):
    """"""


def _make_event_header(odf, global_attrs: dict, dataset):
    """
    "initial_latitude": ("compute"),
    "initial_longitude": ("compute"),
    "end_latitude": ("compute"),
    "end_longitude": ("compute"),
    "depth_off_bottom": ("compute"),
    "creation_date": ("compute"),
    """


def _make_header(odf):
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


def _make_buoy_header(odf, platform: dict):
    """"""
    odf.buoy["name"] = platform["platform_name"]


def _make_instrument_header(odf, dataset):
    """"""


def _make_buoy_instrument_comment(odf, dataset):
    """ dataset.atttrs  'CONFIGURATION_01. FIXME"""


def _make_buoy_instrument_sensors(odf, dataset):
    """FIXME
    temperature_01
    compas_01
    inclinometer_01
    pressions_01
    """


def _make_history_header(odf, dataset):
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


def _make_parameter_headers():
    """
    TODO MAKE A DICTIONNARY GF3_CODE:{ITEMS}
    name : GF3 code plus _XX increament.
    units : from odf
    print_field_value = from odf
    print_decimal_value = from odf
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

    _make_cruise_header(odf, platform, global_attrs)
    _make_event_header(odf, global_attrs, ds)
    _make_header(odf)
    _make_buoy_header(odf, platform)

    _make_history_header(odf, ds)

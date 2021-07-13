"""
module to map xarray dataset to Odf
"""
import xarray as xr
from magtogoek.odf_format import Odf

# Add a int suffix (_01) to parameter codes increasing with each new parameter of the same type.
# - dtype : sing or doub
# Missing Metadata are in the magtogoek/files/odf_parameter.json.

TIME_TYPE = "SYTM"
TIME_FILL_VALUE = "17-NOV-1858 00:00:00.00"

odf = Odf()


def _nc_to_odf_cruise_header(odf, dataset):
    """
    All in the .INI cruise section
    Except:
        platform : Platforom file
        cruise_description: Missing Add to ini files.
    """
    for key in odf.cruise:
        if key in dataset.attrs:
            odf.cruise[key] = dataset.attrs[key]
    # FIXME


def _nc_to_odf_event_header(odf, dataset):
    """
    event_number : is in .INI cruise section
    data_type : is in .INI global_attributes section
    event_qualifier1(2) : Missing. Add to ini files.
    """
    odf.cruise["event_number"] = dataset.attrs["event_number"]
    # FIXME


def _make_odf_header(odf):
    """
    file_specification =
    """
    name_part = [
        "data_type",
        "cruise_number",
        "event_number",
        "event_qualifier1",
        "event_qualifier2",
    ]
    odf.odf["file_specification"] = "_".join(name_part)


def _platform_file_to_odf_buoy_header(odf, platform_dict):
    """
    All in platform_specs of a platform in the platform_file
    """
    odf.buoy["name"] = platform_dict["platform_name"]
    for key in odf.buoy:
        if key in platform_dict["platform_specs"]:
            odf.buoy[key] = platform_dict["platform_specs"][key]


def _config_file_to_instrument_header(config_dict):
    """
    All missing in the config files.
    """
    # FIXME


def _nc_to_odf_history_header(dataset):
    """
    Add a line for magtogoek data processesing.
    One header by datetime entry ?
    """
    # FIXME


def _nc_to_parameter_headers():
    """
    name : GF3 code plus _XX increament.
    units : from odf_
    print_field_value =
    print_decimal_value =
    """

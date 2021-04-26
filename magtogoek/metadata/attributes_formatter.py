#!/usr/bin/python3
"""
author: Jérôme Guay
date: Feb. 16, 2021

:NOTE var_attrs:
_:add sea data net attrisbtes
-:add ancillary_variables:
-:add attributes to accilary variables:
:FIXME

--:time variable need to have a "time_zone" attributes.
"""
import json
import os
import typing as tp

import numpy as np
import xarray as xr
from magtogoek.utils import json2dict

SDN_FILE_PATH = os.path.join(os.path.dirname(__file__), "../files/sdn.json")


def format_variables_names_and_attributes(
    dataset: tp.Type[xr.Dataset], use_bodc_codes: bool
) -> tp.Type[xr.Dataset]:
    """Format variables names and attributes

    Returns dataset with variables attributes set.

    Convert variables names to BODC and then adds CF and SeaDataNet attributes
    to variables.

    Dataset attributes needed :
        `sensor_type`, `sensor_depth`, `sensor_serial`, `VAR_TO_ADD_SENSOR_TYPE`, `P01_CODE_TRANSLATOR`.

    Parameters
    ----------
    dataset :

    bodc_name :

    Notes
    -----

    """
    dataset.time.attrs["cf_role"] = "profil_id"

    for var in dataset.variables:
        dataset[var].attrs["generic_name"] = var

    dataset = _convert_variables_names(dataset)

    for var in dataset.attrs["VAR_TO_ADD_SENSOR_TYPE"]:
        if var in dataset:
            dataset[var].attrs["sensor_type"] = dataset.attrs["sensor_type"]

    _add_sdn_and_cf_var_attrs(dataset, json2dict(SDN_FILE_PATH))

    if not use_bodc_codes:
        dataset = _convert_variables_names(dataset, convert_back_to_generic=True)

    _add_data_min_max_to_var_attrs(dataset)

    if dataset.attrs["sensor_depth"]:
        _add_sensor_depth_to_var_attrs(dataset)
    if dataset.attrs["serial_number"]:
        _add_sensor_serial_to_var_attrs(dataset)

    _add_ancillary_variables_to_var_attrs(dataset)
    _add_names_to_QC_var_attrs(dataset)

    return dataset


def _convert_variables_names(
    dataset: tp.Type[xr.Dataset], convert_back_to_generic: bool = False
):
    """Convert variable and coords names.

    From generic to BODC P01 names or from BODC P01 to generic names if
    `convert_back_to_generic` is True.

    Parameters
    ----------
    dataset :
        FIXME
    convert_to_generic:
       converts from bodc to generitc.
    Notes
    -----
    Conveting names is used to add the conventionned attributes to variables.
    """
    varname_translator = dataset.attrs["P01_CODES"]

    if convert_back_to_generic:
        # mapping key and value and value to key
        varname_translator = dict(
            (value, key) for key, value in varname_translator.items()
        )

    for key in tuple(varname_translator.keys()):
        if key not in dataset:
            del varname_translator[key]

    dataset = dataset.rename(varname_translator)

    return dataset


def _add_sdn_and_cf_var_attrs(dataset: tp.Type[xr.Dataset], sdn: tp.Dict) -> None:
    """add sdn (sea data net) attributes.

    Parameters
    ----------
    sdn :
        sdn is a dictionnary with the P01 variable Code as `key` and dictionnary
    of attributes as `value`. The dictionnary is saved as a json file in
    magtogoek/files/sdn.json

    Notes
    -----
    SeaDataNet attributes include:
     -'standard_name'
     -'units'
     -'long_name'
     -'ancillary_variables'
     -'sdn_parameter_urn'
     -'sdn_parameter_name'
     -'sdn_uom_urn'
     -'sdn_uom_name'
     -'legacy_GF3_code'

    """
    variables = set(dataset.variables).intersection(set(sdn.keys()))
    for var in variables:
        dataset[var].assign_attrs(sdn[var])


def _add_data_min_max_to_var_attrs(dataset):
    """adds data max and min to variables except ancillary and coords variables)"""
    for var in set(dataset.variables).difference(set(dataset.coords)):
        if "_QC" not in var:
            if dataset[var].dtype == float:
                dataset[var].attrs["data_max"] = dataset[var].max().values
                dataset[var].attrs["data_min"] = dataset[var].min().values


def _add_sensor_depth_to_var_attrs(dataset: tp.Type[xr.Dataset]):
    """Add sensor depth to variables with sensor_type"""
    for var in dataset.variables:
        if "sensor_type" in dataset[var].attrs:
            if dataset[var].attrs["sensor_type"] == dataset.attrs["sensor_type"]:
                dataset[var].attrs["sensor_depth"] = dataset.attrs["sensor_depth"]


def _add_sensor_serial_to_var_attrs(dataset: tp.Type[xr.Dataset]):
    """Add sensor serial number `dataset['serial_number'] to variables using XducerDepth."""
    for var in dataset.variables:
        if "sensor_type" in dataset[var].attrs:
            if dataset[var].attrs["sensor_type"] == dataset.attrs["sensor_type"]:
                dataset[var].attrs["serial_number"] = dataset.attrs["serial_number"]


def _add_ancillary_variables_to_var_attrs(dataset: tp.Type[xr.Dataset]):
    """add accillary_variables to variables attributes

    Looks for `_QC` variable names and adds 'ancillary_variables` attributes
    to the corresponding variables.
    """
    for var in list(dataset.variables):
        if "_QC" in var:
            dataset[var.split("_")[0]].attrs["ancillary_variables"] = var


def _add_names_to_QC_var_attrs(dataset: tp.Type[xr.Dataset]) -> None:
    """add long_name and standard_name to QualityControl `_QC` variables."""
    for var in list(dataset.variables):
        if "_QC" in var:
            value = f"Quality flag for {var.split('_')[0]}"
            dataset[var].attrs["long_name"] = value
            dataset[var].attrs["standard_name"] = value


def format_global_attrs(dataset: tp.Type[xr.Dataset]):
    """
    Sets :
    -sounding: (Sounding not added if platform_type is ship.)
     -geospatial_lat_min
     -geospatial_lat_max
     -geospatial_lat_units
     -geospatial_lon_min
     -geospatial_lon_max
     -geospatial_lon_units
     -geospatial_vertical_min
     -geospatial_vertical_max
     -geospatial_vertical_positive
     -geospatial_vertical_units

     -time_coverage_start
     -time_coverage_end
     -time_coverage_duration
     -time_coverage_duration_units (days)
    """
    _geospatial_global_attrs(dataset)
    _time_global_attrs(dataset)


def _time_global_attrs(dataset: tp.Type[xr.Dataset]):
    """
    Notes
    -----
    Attributes added :
     -time_coverage_start
     -time_coverage_end
     -time_coverage_duration
     -time_coverage_duration_units (days)
    """
    dataset.attrs["time_coverage_start"] = str(
        dataset.time.data[0].astype("datetime64[s]")
    )
    dataset.attrs["time_coverage_end"] = str(
        dataset.time.data[-1].astype("datetime64[s]")
    )
    number_day = np.round(
        (dataset.time[-1].data - dataset.time.data[0]).astype(float)
        / (1e9 * 60 * 60 * 24),
        3,
    )

    dataset.attrs["time_coverage_duration"] = number_day
    dataset.attrs["time_coverage_duration_units"] = "days"


def _geospatial_global_attrs(dataset: tp.Type[xr.Dataset]):
    """Compute and add geospatial global attributes to dataset.

    If `lon` and `lon` are variables in the dataset, lat/lon
    min and max are compute from them. If `lon` and `lat`
    are not present, the values are taken form the `longitude` and
    `latitude` dataset attributes.

    The 'longitude' and 'latitude' attributes shoud previously be
    taken from the platform file attributes

    Notes
    -----
    Attributes added :
     -sounding: (Sounding not added if platform_type is ship.)
     -geospatial_lat_min
     -geospatial_lat_max
     -geospatial_lat_units
     -geospatial_lon_min
     -geospatial_lon_max
     -geospatial_lon_units
     -geospatial_vertical_min
     -geospatial_vertical_max
     -geospatial_vertical_positive
     -geospatial_vertical_units
    """

    if dataset.attrs["platform_type"] != "ship":
        if dataset["sensor_type"] == "adcp":
            if "bt_depth" in dataset:
                dataset.attrs["sounding"] = round(dataset.bt_depth.data.median(), 2)

    if "lat" in dataset:
        dataset.attrs["geospatial_lat_min"] = round(dataset.lat.data.min(), 4)
        dataset.attrs["geospatial_lat_max"] = round(dataset.lat.data.max(), 4)
        dataset.attrs["geospatial_lat_units"] = "degrees north"
    elif dataset.attrs["longitude"]:
        dataset.attrs["geospatial_lat_min"] = round(dataset.attrs["longitude"], 4)
        dataset.attrs["geospatial_lat_max"] = round(dataset.attrs["longitude"], 4)
        dataset.attrs["geospatial_lat_units"] = "degrees north"

    if "lon" in dataset:
        dataset.attrs["geospatial_lon_min"] = round(dataset.lon.data.min(), 4)
        dataset.attrs["geospatial_lon_max"] = round(dataset.lon.data.max(), 4)
        dataset.attrs["geospatial_lon_units"] = "degrees east"
    elif dataset.attrs["latitude"]:
        dataset.attrs["geospatial_lon_min"] = round(dataset.attrs["latitude"], 4)
        dataset.attrs["geospatial_lon_max"] = round(dataset.attrs["latitude"], 4)
        dataset.attrs["geospatial_lon_units"] = "degrees east"

    dataset.attrs["geospatial_vertical_min"] = round(dataset.depth.data.min(), 2)
    dataset.attrs["geospatial_vertical_max"] = round(dataset.depth.data.max(), 2)
    dataset.attrs["geospatial_vertical_positive"] = "down"
    dataset.attrs["geospatial_vertical_units"] = "meters"

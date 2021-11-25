#!/usr/bin/python3
"""
author : jerome.guay@protonamil.com
date : Feb. 16, 2021

This script contains `format_variables_namnes_and_attributes()` function that, as the name may
suggest, formats a xarray dataset variables attributes have SeaDataNet, CF Conventions and other
attributes. This script requires json files containing the `static` metadata to add to variables.
The json files can be made by executing static_attributes.py script which can be edited to change
where the json is saved.

   $ python static_attributes.py

static variables attributes :
 -'standard_name'
 -'units'
 -'long_name'
 -'ancillary_variables'
 -'sdn_parameter_urn'
 -'sdn_parameter_name'
 -'sdn_uom_urn'
 -'sdn_uom_name'
 -'legacy_GF3_code'

dynamic variables attributes :
 -'data_min'
 -'data_max'


Sea Also
--------
Read the functions and the docs below. They are pretty explicit.
"""
import typing as tp
from pathlib import Path

import numpy as np
import xarray as xr

from magtogoek.utils import json2dict

STATIC_ATTRIBUTES_RELATIVE_FILE_PATH = "files/CF_P01_GF3_formats.json"
STATIC_ATTRIBUTES_ABSOLUTE_FILE_PATH = (
    Path(__file__).resolve().parent.joinpath(STATIC_ATTRIBUTES_RELATIVE_FILE_PATH).resolve()
)


def format_variables_names_and_attributes(
    dataset: xr.Dataset, use_bodc_codes: bool
) -> xr.Dataset:
    """Format variables names and attributes

    Returns dataset with variables attributes set.

    Convert variables names to BODC and then adds CF and SeaDataNet metadata
    to variables attributes. Coordinates names are always changed back to their
    original names (generic_name). Variables names can also be changed back to
    their original names (generic_name) setting `use_bodc_codes` as `False`/

    Require dataset global attributes  :
        `P01_CODE_TRANSLATOR` : a dictionary containing `generic_name`:`p01_codes`
             as keys and items.

    None essential global attributes :
        `sensor_type` :
        `sensor_depth` :
        `sensor_serial` :
        `VAR_TO_ADD_SENSOR_TYPE` : List of P01 parameters codes of variables to which
            add the sensor_type attributes.

    Parameters
    ----------
    dataset :
        dataset to format. The dataset must contain a global_attributes named `P01_CODE_TRANSLATOR`
    which has to be a dictionary containing `generic_name`:`p01_code` as keys and items.

    use_bodc_codes :
       If `True`, the variable names are changed to th BODC P01 parameters codes.

    Notes
    -----
    """
    for var in dataset.variables:
        dataset[var].attrs["generic_name"] = var

    original_coords_name = dataset.coords

    dataset = _convert_variables_names(dataset)
    if "VAR_TO_ADD_SENSOR_TYPE" in dataset.attrs:
        for var in dataset.attrs["VAR_TO_ADD_SENSOR_TYPE"]:
            if var in dataset:
                dataset[var].attrs["sensor_type"] = dataset.attrs["sensor_type"]

    _add_sdn_and_cf_var_attrs(dataset, json2dict(STATIC_ATTRIBUTES_ABSOLUTE_FILE_PATH))

    if not use_bodc_codes:
        dataset = _convert_variables_names(dataset, convert_back_to_generic=True)
    else:
        dataset = dataset.rename(
            {dataset.attrs["P01_CODES"][name]: name for name in original_coords_name}
        )

    _add_data_min_max_to_var_attrs(dataset)

    if dataset.attrs["sensor_depth"]:
        _add_sensor_depth_to_var_attrs(dataset)
    if dataset.attrs["serial_number"]:
        _add_sensor_serial_to_var_attrs(dataset)

    _add_ancillary_variables_to_var_attrs(dataset)
    _add_names_to_qc_var_attrs(dataset)

    return dataset


def _convert_variables_names(
    dataset: xr.Dataset, convert_back_to_generic: bool = False
) -> xr.Dataset:
    """Convert variable and coords names.

    From generic to BODC P01 names or from BODC P01 to generic names if
    `convert_back_to_generic` is True.

    Parameters
    ----------
    dataset :
        FIXME
    convert_back_to_generic:
       converts from bodc to generic.
    Notes
    -----
    Converting names is used to add the convention attributes to variables.
    """
    varname_translator = {**dataset.attrs["P01_CODES"]}

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


def _add_sdn_and_cf_var_attrs(dataset: xr.Dataset, sdn: tp.Dict):
    """add sdn (sea data net) attributes.

    Parameters
    ----------
    sdn :
        sdn is a dictionary with the P01 variable Code as `key` and dictionary
    of attributes as `value`. The dictionary is saved as a json file in
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
        dataset[var] = dataset[var].assign_attrs(sdn[var])


def _add_data_min_max_to_var_attrs(dataset):
    """adds data max and min to variables except ancillary and coords variables)"""
    for var in set(dataset.variables).difference(set(dataset.coords)):
        if "_QC" not in var:
            if dataset[var].dtype == float:
                dataset[var].attrs["data_max"] = dataset[var].max().values
                dataset[var].attrs["data_min"] = dataset[var].min().values


def _add_sensor_depth_to_var_attrs(dataset: xr.Dataset):
    """Add sensor depth to variables with sensor_type"""
    for var in dataset.variables:
        if "sensor_type" in dataset[var].attrs:
            if dataset[var].attrs["sensor_type"] == dataset.attrs["sensor_type"]:
                dataset[var].attrs["sensor_depth"] = dataset.attrs["sensor_depth"]


def _add_sensor_serial_to_var_attrs(dataset: xr.Dataset):
    """Add sensor serial number `dataset['serial_number'] to variables using XducerDepth."""
    for var in dataset.variables:
        if "sensor_type" in dataset[var].attrs:
            if dataset[var].attrs["sensor_type"] == dataset.attrs["sensor_type"]:
                dataset[var].attrs["serial_number"] = dataset.attrs["serial_number"]


def _add_ancillary_variables_to_var_attrs(dataset: xr.Dataset):
    """add ancillary_variables to variables attributes

    Looks for `_QC` variable names and adds 'ancillary_variables` attributes
    to the corresponding variables.
    """
    for var in list(dataset.variables):
        if "_QC" == var[-3:]:
            dataset[var[:-3]].attrs["ancillary_variables"] = var


def _add_names_to_qc_var_attrs(dataset: xr.Dataset) -> None:
    """add long_name and standard_name to QualityControl `_QC` variables."""
    for var in list(map(str, dataset.variables)):
        if "_QC" in var:
            value = f"Quality flag for {var.split('_')[0]}"
            dataset[var].attrs["long_name"] = value
            dataset[var].attrs["standard_name"] = value


def compute_global_attrs(dataset: xr.Dataset):
    """
    Sets :
     -time_coverage_start
     -time_coverage_end
     -time_coverage_duration
     -time_coverage_duration_units (days)

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
    _geospatial_global_attrs(dataset)
    _time_global_attrs(dataset)


def _time_global_attrs(dataset: xr.Dataset):
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


def _geospatial_global_attrs(dataset: xr.Dataset):
    """Compute and add geospatial global attributes to dataset.

    If `lon` and `lon` are variables in the dataset, lat/lon
    min and max are compute from them. If `lon` and `lat`
    are not present, the values are taken form the `longitude` and
    `latitude` dataset attributes.

    The 'longitude' and 'latitude' attributes should previously be
    taken from the platform file attributes

    Notes
    -----
    Attributes added :
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

    if "lat" in dataset:
        dataset.attrs["latitude"] = round(dataset.lat.data.mean(), 4)
        dataset.attrs["geospatial_lat_min"] = round(dataset.lat.data.min(), 4)
        dataset.attrs["geospatial_lat_max"] = round(dataset.lat.data.max(), 4)
        dataset.attrs["geospatial_lat_units"] = "degrees north"
    elif "latitude" in dataset.attrs:
        if dataset.attrs["latitude"]:
            dataset.attrs["geospatial_lat_min"] = round(dataset.attrs["latitude"], 4)
            dataset.attrs["geospatial_lat_max"] = round(dataset.attrs["latitude"], 4)
            dataset.attrs["geospatial_lat_units"] = "degrees north"

    if "lon" in dataset:
        dataset.attrs["longitude"] = round(dataset.lon.data.mean(), 4)
        dataset.attrs["geospatial_lon_min"] = round(dataset.lon.data.min(), 4)
        dataset.attrs["geospatial_lon_max"] = round(dataset.lon.data.max(), 4)
        dataset.attrs["geospatial_lon_units"] = "degrees east"
    elif "longitude" in dataset.attrs:
        if dataset.attrs["longitude"]:
            dataset.attrs["geospatial_lon_min"] = round(dataset.attrs["longitude"], 4)
            dataset.attrs["geospatial_lon_max"] = round(dataset.attrs["longitude"], 4)
            dataset.attrs["geospatial_lon_units"] = "degrees east"

    dataset.attrs["geospatial_vertical_min"] = round(dataset.depth.data.min(), 2)
    dataset.attrs["geospatial_vertical_max"] = round(dataset.depth.data.max(), 2)
    dataset.attrs["geospatial_vertical_positive"] = "down"
    dataset.attrs["geospatial_vertical_units"] = "meters"

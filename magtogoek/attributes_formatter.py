#!/usr/bin/python3
"""
author : jerome.guay@protonamil.com
date : Feb. 16, 2021

This script contains `format_variables_names_and_attributes()` function that, as the name may
suggest, formats a xarray dataset variables attributes have SeaDataNet, CF Conventions and other
attributes. This script requires json files containing the `static` metadata to add to variables.
The json files can be made by executing static_attributes.py script which can be edited to change
where the json is saved.


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

import numpy as np
import xarray as xr

from magtogoek import logger as l, CONFIGURATION_PATH
from magtogoek.utils import json2dict


STATIC_ATTRIBUTES_PATH = CONFIGURATION_PATH.joinpath("CF_P01_GF3_formats.json")

CF_P01_GF3_ATTRS_KEY_TO_ADD = [
    "standard_name",
    "positive",
    "units",
    "long_name",
    "sdn_parameter_urn",
    "sdn_parameter_name",
    "sdn_uom_urn",
    "sdn_uom_name",
    "legacy_GF3_code"
]


def format_variables_names_and_attributes(
        dataset: xr.Dataset,
        use_bodc_name: bool,
        p01_codes_map: dict,
        cf_profile_id: str = 'time',
) -> xr.Dataset:
    """Format variables names and attributes
    Returns dataset with variables attributes set.

    Convert variables names to BODC and then adds CF and SeaDataNet metadata
    to variables attributes. Coordinates names are always changed back to their
    original names (generic_name). Variable names can also be keep their
    original names (generic_name) setting `use_bodc_codes` as `False`.


    Parameters
    ----------
    dataset :
        dataset to format.
    use_bodc_name :
        True if the bodc_name are to be used.
    p01_codes_map :
        generic name to bodc p01_code mapping.
    cf_profile_id :
        Name of the coordinate to add the attributes {'cf_role': 'profile_id'}

    Notes
    -----

    Raises
    ------
    `ValueError` if units in dataarray attributes don't match those in the CF_P01_GF3_formats.json file.
    """

    _add_generic_name_to_variables(dataset)

    original_coords_name = dataset.coords

    dataset = _convert_variables_names(dataset, p01_codes_map)

    _add_sdn_and_cf_var_attrs(dataset, json2dict(STATIC_ATTRIBUTES_PATH))

    if use_bodc_name is not True:
        dataset = _convert_variables_names(dataset, p01_codes_map, convert_back_to_generic=True)
    else:
        dataset = dataset.rename(
            {p01_codes_map[name]: name for name in original_coords_name}
        )

    _add_data_min_max_to_var_attrs(dataset)

    _add_ancillary_variables_to_var_attrs(dataset)
    _add_names_to_qc_var_attrs(dataset)

    if cf_profile_id in dataset.variables:
        dataset[cf_profile_id].attrs['cf_role'] = 'profile_id'

    l.log("Variables attributes added.")

    return dataset


def _add_generic_name_to_variables(dataset: xr.Dataset):
    for var in dataset.variables:
        dataset[var].attrs["generic_name"] = var


def _convert_variables_names(
    dataset: xr.Dataset, p01_codes: dict, convert_back_to_generic: bool = False
) -> xr.Dataset:
    """Convert variable and coords names.

    From generic to BODC P01 names or from BODC P01 to generic names if
    `convert_back_to_generic` is True.

    Parameters
    ----------
    dataset :
        dataset to format
    p01_codes :
        generic name to bodc p01_code mapping.
    convert_back_to_generic :
       converts from bodc to generic.

    Notes
    -----
    Converting names is used to add the convention attributes to variables.
    """
    varname_translator = {**p01_codes}

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


def _add_sdn_and_cf_var_attrs(dataset: xr.Dataset, sdn_meta: tp.Dict):
    """add sdn (sea data net) attributes.

    Parameters
    ----------
    sdn_meta :
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
    common_variables = set(dataset.variables).intersection(set(sdn_meta.keys()))
    for var in common_variables:
        _check_units(dataset[var], sdn_meta[var])
        var_attrs = {key: value for key, value in sdn_meta[var].items() if key in CF_P01_GF3_ATTRS_KEY_TO_ADD}
        dataset[var].attrs.update(var_attrs)


def _check_units(dataarray: xr.DataArray, sdn_meta: dict):
    """Raise error if units don't match. Use for development."""
    if "units" in dataarray.attrs:
        if dataarray.attrs['units']:  # not none or empty string
            if sdn_meta['units'] != dataarray.attrs['units']:
                raise ValueError(f"DataArray ({dataarray.name}) units ({dataarray.attrs['units']}) and SND_META ({sdn_meta['units']}) units don't match")


def _add_data_min_max_to_var_attrs(dataset):
    """adds data max and min to variables except ancillary and coords variables)"""
    for var in set(dataset.variables).difference(set(dataset.coords)):
        if "_QC" not in var:
            if dataset[var].dtype in (float, int):  # Use to be only float but that I did know why (June 30th 2023)
                dataset[var].attrs["data_max"] = dataset[var].max().values.item() # item() get the value out of the
                dataset[var].attrs["data_min"] = dataset[var].min().values.item() #  numpy array. Maybe not necessary


def _add_ancillary_variables_to_var_attrs(dataset: xr.Dataset):
    """add ancillary_variables to variables attributes

    Looks for `_QC` variable names and adds `ancillary_variables` attributes
    to the corresponding variables.
    """
    for var in list(dataset.variables):
        if "_QC" in var:
            param = var.split("_QC")[0]
            if "ancillary_variables" in dataset[param].attrs:
                dataset[param].attrs["ancillary_variables"] += " " + var
            else:
                dataset[param].attrs["ancillary_variables"] = var


def _add_names_to_qc_var_attrs(dataset: xr.Dataset) -> None:
    """add long_name and standard_name to QualityControl `_QC` variables."""
    for var in list(map(str, dataset.variables)):
        if "_QC" in var:
            value = f"Quality flag for {var.split('_QC')[0]}"
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

    if "time" in dataset.coords:
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

    if "lat" in dataset.variables:
        dataset.attrs["latitude"] = round(dataset.lat.mean().values.item(), 4)
        dataset.attrs["geospatial_lat_min"] = round(dataset.lat.min().values.item(), 4)
        dataset.attrs["geospatial_lat_max"] = round(dataset.lat.max().values.item(), 4)
        dataset.attrs["geospatial_lat_units"] = "degrees north"
    elif "latitude" in dataset.attrs:
        if dataset.attrs["latitude"]:
            dataset.attrs["geospatial_lat_min"] = round(dataset.attrs["latitude"], 4)
            dataset.attrs["geospatial_lat_max"] = round(dataset.attrs["latitude"], 4)
            dataset.attrs["geospatial_lat_units"] = "degrees north"

    if "lon" in dataset.variables:
        dataset.attrs["longitude"] = round(dataset.lon.mean().values.item(), 4)
        dataset.attrs["geospatial_lon_min"] = round(dataset.lon.min().values.item(), 4)
        dataset.attrs["geospatial_lon_max"] = round(dataset.lon.max().values.item(), 4)
        dataset.attrs["geospatial_lon_units"] = "degrees east"
    elif "longitude" in dataset.attrs:
        if dataset.attrs["longitude"]:
            dataset.attrs["geospatial_lon_min"] = round(dataset.attrs["longitude"], 4)
            dataset.attrs["geospatial_lon_max"] = round(dataset.attrs["longitude"], 4)
            dataset.attrs["geospatial_lon_units"] = "degrees east"

    if 'depth' in dataset.variables:
        dataset.attrs["geospatial_vertical_min"] = round(dataset.depth.min().values.item(), 2)
        dataset.attrs["geospatial_vertical_max"] = round(dataset.depth.max().values.item(), 2)
        dataset.attrs["geospatial_vertical_positive"] = "down"
        dataset.attrs["geospatial_vertical_units"] = "meters"

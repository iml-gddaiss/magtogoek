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
import typing as tp

import xarray as xr
from magtogoek.utils import json2dict

FLAG_REFERENCE = "BODC SeaDataNet"
FLAG_VALUES = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
FLAG_MEANINGS = (
    "no_quality_control",
    "good_value",
    "probably_good_value",
    "probably_bad_value",
    "bad_value",
    "changed_value",
    "value_below_detection",
    "value_in_excess",
    "interpolated_value",
    "missing_value",
)


def add_dataset_variables_attributes(
    dataset: tp.Type[xr.Dataset],
    sdn: tp.Dict,
):
    """Add dataset variable attributes

    Parameters:
    -----------
    dataset :
        dataset to which add attributes its variables.

    sdn :
        SDN variables attributes with P01 keys for varnames.

    sensor_dictionnary :
        variables attributes.

    """
    _add_sdn(dataset, sdn)
    _add_data_min_max(dataset)
    _add_ancillary_variables(dataset)
    _add_attributes_to_ancillary_variables(dataset)

    return print("variables attributes set")


def _add_sdn(dataset: tp.Type[xr.Dataset], sdn: tp.Dict) -> None:
    """add sdn (sea data net) attributes."""
    variables = set(dataset.variables).intersection(set(sdn.keys()))
    for var in variables:
        dataset[var].attrs = sdn[var]


def _add_data_min_max(dataset):
    """adds data max and min to variables except ancillary and coords variables)"""
    for var in set(dataset.variables).difference(set(dataset.coords)):
        if "_QC" not in var:
            if dataset[var].dtype is float:
                dataset[var].attrs["data_max"] = dataset[var].max().values
                dataset[var].attrs["data_min"] = dataset[var].min().values


def _add_ancillary_variables(dataset: tp.Type[xr.Dataset]):
    """add accillary_variables to variables attributes"""
    for var in list(dataset.variables):
        if "_QC" in var:
            dataset[var.split("_")[0]].attrs["ancillary_variables"] = var


def _add_attributes_to_ancillary_variables(dataset: tp.Type[xr.Dataset]) -> None:
    """add attributes to  ancillary variables."""
    for var in list(dataset.variables):
        if "_QC" in var:
            dataset[var].attrs["long_name"] = f"Quality flag for {var.split('_')[0]}"
            dataset[var].attrs[
                "standard_name"
            ] = f"Quality flag for {var.split('_')[0]}"
            dataset[var].attrs["flag_meanings"] = FLAG_MEANINGS
            dataset[var].attrs["flag_values"] = FLAG_VALUES
            dataset[var].attrs["flag_reference"] = FLAG_REFERENCE


def _add_long_name(dataset: tp.Type[xr.Dataset], long_names: tp.Dict) -> None:
    """add long_name from long_names dictionnary
    NOTE NOT USED TO REMOVE"""
    for sensor_type, long_names in long_names.items():
        variables = set(dataset.variables).intersection(set(long_names.keys()))
        for var in variables:
            dataset[var].attrs["long_name"] = long_names[var]


def _add_sensor_attributes(dataset: tp.Type[xr.Dataset], sensors_type: tp.Dict) -> None:
    """add sensors related attributes to variables.
    NOTE NOT USED TO REMOVE
    Runs:
    -----
    _add_sensor_type()
    _add_sensor_depth_and_serial_number()
    """
    _add_sensor_type(dataset, sensors_type)
    _add_sensor_depth_and_serial_number()


def _add_sensor_type(dataset: tp.Type[xr.Dataset], sensors_type: tp.Dict) -> None:
    """add sensor_type from sensors_type dictionnary if in dataset variables
    NOTE NOT USED TO REMOVE
    """
    for sensor, variables in sensors_type.items():
        variables = set(dataset.variables).intersection(set(sensors_type[sensor]))
        for var in variables:
            dataset[var].attrs["sensor_type"] = sensor


def _add_sensor_depth_and_serial_number(dataset: tp.Type[xr.Dataset]) -> None:
    """add sensor_depth and sensor_serial_number from global attributes
    NOTE NOT USED TO REMOVE
    """
    for var in list(dataset.variables):
        if "sensor_type" in var.attrs:
            var.attrs["sensor_depth"] = dataset[
                f"_vartmp_{dataset.attrs['sensor_id']}_depth"
            ]
            var.attrs["sensor_serial_number"] = dataset[
                f"_vartmp_{dataset.attrs['sensor_id']}_serial_number"
            ]

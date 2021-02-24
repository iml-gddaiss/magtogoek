"""
author: Jérôme Guay
date: Feb. 16, 2021

:NOTE var_attrs:
-:add sensor_type to specific variables:
-:add sensor_depth and sensor_serial_number with _vartmp_
-:add ancillary_variables:
-:add attributes to accilary variables:
:FIXME
-:time coords, move to adcp encoding.
--:units = seconds since 1992-10-8 15:15:42.5 -6:00:
--:time variable need to have a "time_zone" attributes.
"""

import json
import typing as tp
import xarray as xr
from toolbox import json2dict


def add_dataset_variables_attributes(
    dataset: tp.Type[xr.Dataset],
    sdn: tp.Tuple[str, tp.Dict],
    sensors_type: tp.Tuple[str, tp.Dict],
    long_names: tp.Tuple[str, tp.Dict],
    drop_tmp: bool = True,
) -> None:
    """Set dataset variable attributes

    Parameters:
    -----------
        dataset:
            dataset to which add attributes its variables.
        sdn:
            json file containing the sdn variables attributes.
        sensor_type:
            [optional] json file containing the sensor_type variables  attributes.
        long_name:
            [optional] json file containing the long_name variables  attributes.
        drop_tmp:
            if 'True', drops global attributes with the prefix: '_vartmp_'
    """
    _add_sdn(dataset, sdn)
    _add_sensor_attributes(dataset, sensors_type)
    _add_long_name(dataset, long_names)
    _add_data_min_max(dataset)
    _add_ancillary_variables(dataset)
    _add_attributes_to_ancillary_variables(dataset)

    if drop_tmp is True:
        for attrs in dataset.attrs.keys():
            if "_vartmp_" in attrs:
                del dataset.attrs[attrs]

    return print("variables attributes set")


def _add_sdn(dataset: tp.Type[xr.Dataset], sdn: tp.Dict) -> None:
    """add sdn (sea data net) attributes.

    FIXME"""
    variables = set(dataset.variables).intersection(set(sdn.keys()))
    for var in variables:
        dataset[var].attrs = sdn[var]


def _add_sensor_attributes(dataset: tp.Type[xr.Dataset], sensors_type: tp.Dict) -> None:
    """add sensors related attributes to variables.
    FIXME
    Runs:
    -----
        _set_sensor_type()
        _set_sensor_depth_and_serial_number()
        _set_sensor_serial_number()
    """
    _add_sensor_type(dataset, sensors_type)
    _add_sensor_depth_and_serial_number()


def _add_sensor_type(dataset: tp.Type[xr.Dataset], sensors_type: tp.Dict) -> None:
    """add sensor_type from sensors_type dictionnary if in dataset variables"""
    for sensor, variables in sensors_type.items():
        variables = set(dataset.variables).intersection(set(sensors_type.keys()))
        for var in variables:
            dataset[var].attrs["sensor_type"] = sensor


def _add_sensor_depth_and_serial_number(dataset: tp.Type[xr.dataset]) -> None:
    """add sensor_depth and sensor_serial_number from global attributes"""
    for var in list(dataset.variables):
        if "sensor_type" in var.attrs:
            var.attrs["sensor_depth"] = dataset[
                f"_vartmp_{dataset.attrs['sensor_id']}_depth"
            ]
            var.attrs["sensor_serial_number"] = dataset[
                f"_vartmp_{dataset.attrs['sensor_id']}_serial_number"
            ]


def _add_long_name(dataset: tp.Type[xr.Dataset], long_names: tp.Dict) -> None:
    """add long_name from long_names dictionnary"""
    for sensor_type, long_names in long_names.items():
        variables = set(dataset.variables).intersection(set(long_names.keys()))
        for var in variables:
            dataset[var].attrs["long_name"] = long_names[var]


def _add_data_min_max(dataset):
    """TODO check if it works"""
    for var in dataset.variables:
        if "_QC" not in var:
            dataset[var].attrs["data_max"] = dataset[var].max()
            dataset[var].attrs["data_min"] = dataset[var].min()


def _add_ancillary_variables(dataset: tp.Type[xr.Dataset]):
    """add accillary_variables"""
    for var in list(dataset.varibales()):
        if "_QC" in var:
            dataset[var.split("_")[0]].attrs["ancillary_variables"] = var


def _add_attributes_to_ancillary_variables(dataset: tp.Type[xr.Dataset]) -> None:
    """add attributes to  ancillary variables."""
    for var in list(dataset.variables()):
        if "_QC" in var:
            dataset[var].attrs["long_name"] = (f"Quality flag for {var.split('_')[0]}",)
            dataset[var].attrs["coomments"] = ("Quality flag resulting from ...",)
            dataset[var].attrs["flag_meanings"] = [
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
            ]
            dataset[var].attrs["flag_values"] = ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9],)
            dataset[var].attrs["References"] = ("BODC SeaDataNet",)

"""
author: Jérôme Guay
date: Feb. 16, 2021

:NOTE var_attrs:
-:add sensor_type to specific variables:
--:Make a default list by instruments:
---:Ex:
-:serial_number: if sensor_type == 'instrument':
-:data_min, data_max:
-:sensor_depth:
-:ancillary_variables (in _QC function):
-:time, time attributes are more encoding dependent, maybe move it in instrument/encoder.py:
--:units = seconds since 1992-10-8 15:15:42.5 -6:00:
"""

import json
import typing as tp
import xarray as xr
from toolbox import dict2json


def set_dataset_variables_attributes(
    dataset: tp.Type[xr.Dataset],
    attrs: tp.Tuple[str, tp.Dict],
    drop_tmp: bool = True,
) -> None:
    """Set dataset variable attributes

    Parameters:
    -----------
        dataset:
            dataset to which add attributes to variables.
        attrs:
            dict or json file containing the sdn variables attributes.
        remove_tmp:
            remove temporary attributes from dataset.
    """
    var_list = list(dataset.variables)

    # open attrs: check if type is dict or .json json2dict() or raise value error
    # compare intersect var_list with dict(key)

    return print("variables attributes set")


def set_data_min_max_attrs():
    """TODO"""
    return None


def set_sensor_attrs():
    """TODO
    NOTE: Look for sensor_type, make list[]
    -add the following temporary attrs to dataset
    -tmp_adcp_serial = 'adcp_serial' make list[]
    -tmp_adcp_depth = adcp_depth make list[]
    -Then add them to var with sensor_type corresponding.
    """
    return None


def set_sensor_depth():
    """TODO
    NOTE May not be usefull
    """
    return None


def set_sensor_serial_number():
    """TODO
    NOTE May not be usefull
    """
    return None


def set_ancillary_attrs():
    """TODO"""
    return None


def get_QCvar_attributes(P01_name: str, comments: str) -> tp.Dict[str, str]:
    """Set attributes for _QC variables.

    Parameters:
    -----------

        P01_var_name:
            long_name = 'Quality flag for ' + P01_var_name

        comments:
            Something like: 'Quality flag resulting from ...'
    """
    return dict(
        long_name=f"Quality flag for {P01_name}",
        comments=comments,
        flag_meanings=(
            "no_quality_control, "
            "good_value, "
            "probably_good_value, "
            "probably_bad_value, "
            "bad_value, "
            "changed_value,"
            "value_below_detection, "
            "value_in_excess, "
            "interpolated_value, "
            "missing_value"
        ),
        flag_values="0, 1, 2, 3, 4, 5, 6, 7, 8, 9",
        References="BODC SeaDataNet",
    )

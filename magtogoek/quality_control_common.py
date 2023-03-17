import numpy as np
import xarray as xr
from typing import List
from nptyping import NDArray
from pandas import Timestamp

from magtogoek import logger as l, CONFIGURATION_PATH
from magtogoek.process_common import FLAG_ATTRIBUTES
from magtogoek.utils import json2dict

IMPOSSIBLE_PARAMETERS_VALUES_FILE_PATH = CONFIGURATION_PATH.joinpath("impossible_parameter_values.json")
IMPOSSIBLE_PARAMETERS_VALUES = json2dict(IMPOSSIBLE_PARAMETERS_VALUES_FILE_PATH)

SPIKE_DETECTION_PARAMETERS_FILE_PATH = CONFIGURATION_PATH.joinpath("spike_thresholds.json")
SPIKE_DETECTION_PARAMETERS = json2dict(SPIKE_DETECTION_PARAMETERS_FILE_PATH)

CLIMATOLOGY_TIME_FORMATS = {
        'dayofyear': 'time.dayofyear',
        'weekofyear': 'time.week',
        'monthofyear': 'time.month',
        'season': 'time.season'
    }
SEASONS_ID = ('DJF', 'JJA', 'MAM', 'SON')


def values_outliers_detection(data: NDArray, lower_limit: float, upper_limit: float) -> NDArray:
    """Check for data outlier

    Parameters
    ----------
    data :
        Data to check
    lower_limit :
        Outlier need to be smaller than the `lower_limit`.
    upper_limit :
        Outlier need to be greater than the `upper_limit`.

    Returns
    -------
    Boolean array of the same shape as `data`
    """
    return np.bitwise_or(data < lower_limit, data > upper_limit)


def find_climatology_outlier(
        dataset: xr.Dataset,
        climatology_dataset: xr.Dataset,
        variable: str,
        threshold: float,
        depth_interpolation_method='linear'
) -> xr.DataArray:
    """Flag data that are outside the climatology.

    Fixme Test needs to be carried out for:  different resolutions, missing values

    Parameters
    ----------
    dataset :
        Dataset containing the data to compare.
    climatology_dataset :
        Dataset containing the climatology.
        For any give `variable_name` to compare with the climatology,
        the climatology dataset should be structured as follow:
            Variables:
                variable_name + '_mean'
                variable_name + '_std'
            Time coords:
                'dayofyear': 1 .. 366
                'weekofyear': 1 .. 52
                'monthofyear': 1 .. 12
                'season': 'DJF', 'JJA', 'MAM', 'SON'
    variable :
        Variable to carry climatology test on.
    threshold :
        factor that is multiplier to the standard deviation.
    depth_interpolation_method :
        Only use when the data has a depth component.
        "linear", "nearest", "zero", "slinear", "quadratic", "cubic" (See xarray documentation)

    Returns
    -------
    Return boolean dataarray with values of:

        [True] < (mean - threshold * std) <= [False] <= (mean + threshold * std) < [True]
    """
    # Check for the variable in the dataset
    if variable not in dataset:
        raise KeyError(f'Variable not found in dataset {variable}')

    # Check for climatology variables `mean` and `std
    for var in [variable + s for s in ('_mean', '_std')]:
        if var not in climatology_dataset:
            raise KeyError(f'variable not in climatology dataset {var}')

    clim_time = _get_climatology_time_coord(climatology_dataset, variable)

    # Group Data into clim_time
    grouped_data = dataset[variable].groupby(clim_time)

    # Interpolation of the climatology to over the dataset depths.
    if 'depth' in dataset.variables and 'depth' in climatology_dataset:
        climatology_dataset = climatology_dataset.interp(depth=dataset.depth, method=depth_interpolation_method)

    # Defining upper and lower limits
    lower_limits = climatology_dataset[variable + '_mean'] - threshold * climatology_dataset[variable + '_std']
    upper_limits = climatology_dataset[variable + '_mean'] + threshold * climatology_dataset[variable + '_std']

    # Returns boolean array where outlier return True.
    return (grouped_data > upper_limits) | (grouped_data < lower_limits)


def _get_climatology_time_coord(dataset: xr.Dataset, variable: str) -> str:
    """TODO"""
    mean_clim_time = _find_climatology_variable_time_coord(dataset[variable + '_mean'])
    std_clim_time = _find_climatology_variable_time_coord(dataset[variable + '_std'])
    if mean_clim_time != std_clim_time:
        raise ValueError(f'The mean and std climatology for {variable} have different climatological time coords.')

    clim_time = mean_clim_time

    if clim_time == 'time.season':
        if set(dataset.season.values) != set(SEASONS_ID):
            raise ValueError("Invalid season ID for climatology. Season IDs: ['DJF', 'JJA', 'MAM', 'SON'].")

    return clim_time


def _find_climatology_variable_time_coord(dataarray: xr.DataArray) -> str:
    """TODO"""
    intersection = list(set(dataarray.coords).intersection(set(CLIMATOLOGY_TIME_FORMATS.keys())))
    if len(intersection) == 1:
        return CLIMATOLOGY_TIME_FORMATS[intersection[0]]
    else:
        raise ValueError(f'Climatology time not found in climatology dataset for variable: {dataarray.name}.')


def climatology_outlier_test(
        dataset: xr.Dataset,
        climatology_dataset: xr.Dataset,
        variable: str,
        threshold: float,
        depth_interpolation_method: str,
):
    """Find climatology outlier and add an ancillary variable to the dataset
    named : <variable>_QC_climatology_outlier

    Parameters
    ----------
    dataset :
        Dataset containing the data to compare.
    climatology_dataset :
        Dataset containing the climatology.
        For any give `variable_name` to compare with the climatology,
        the climatology dataset should be structured as follow:
            Variables:
                variable_name + '_mean'
                variable_name + '_std'
            Time coords:
                'dayofyear': 1 .. 366
                'weekofyear': 1 .. 52
                'monthofyear': 1 .. 12
                'season': 'DJF', 'JJA', 'MAM', 'SON'
    variable :
        Variable to carry climatology test on.
    threshold :
        factor that is multiplier to the standard deviation.
    depth_interpolation_method :
        Only use when the data has a depth component.
        "linear", "nearest", "zero", "slinear", "quadratic", "cubic" (See xarray documentation)
    """
    outliers_flag = find_climatology_outlier(
        dataset=dataset,
        climatology_dataset=climatology_dataset,
        variable=variable,
        threshold=threshold,
        depth_interpolation_method=depth_interpolation_method
    )

    _add_climatology_qc_variable(dataset, variable)

    dataset[variable + "_QC_climatology_outlier"] = dataset[variable + "_QC_climatology_outlier"].where(~outliers_flag, other=3)

    test_comment = f"Climatology outlier test. Range: {threshold} times the standard deviation around the mean. (flag=3)"
    l.log(f"{variable}: " + test_comment)
    dataset[variable + "_QC_climatology_outlier"].attrs['quality_test'] += test_comment + "\n"


def _add_climatology_qc_variable(dataset: xr.Dataset, variable: str):
    """"""
    dataset[variable + "_QC_climatology_outlier"] = (
        dataset[variable].dims, np.ones(dataset[variable].shape).astype(int),
        {'quality_test': "", "quality_date": Timestamp.now().strftime("%Y-%m-%d")}
    )
    dataset[variable + "_QC_climatology_outlier"].attrs.update(FLAG_ATTRIBUTES)


def data_spike_detection(data: NDArray, inner_thres: float, outer_thres: float):
    """ Spike detection.

    ```Algorithm without first and last values:

        |V2 - (V3+V1)/2| - |(V1-V3)/2|  >= Threshold_1
    ```

    ```Algorithm for first and last values:

        |V2 - v1|  >= Threshold_2
    ```

    Parameters
    ----------
    data :
        Time series to check for spikes.
    inner_thres :
        Threshold for data without first and last values.
    outer_thres :
        Threshold for the first and last values.

    Returns
    -------
    Boolean array of the same shape as data where True values are data spikes.

    """
    spikes = np.zeros(data.shape).astype(bool)
    v1 = data[0:-2]
    v2 = data[1:-1]
    v3 = data[2:]

    spikes[0] = np.abs(data[1] - data[0]) >= outer_thres
    spikes[1:-1] = np.abs(v2 - (v3 + v1)/2) - np.abs(v1 - v3) / 2 >= inner_thres
    spikes[-1] = np.abs(data[-1] - data[-2]) >= outer_thres

    return spikes


def data_spike_detection_tests(dataset: xr.Dataset, variable: str):
    """
    Carry spike detection for inner and other threshold.

    Variable spikes thresholds are define in files/spike_thresholds.json.

    Adds add an ancillary variable named <variable>_QC to dataset if one does not exist.
        Set ancillary Set new_flag of 3 for spikes.

    Parameters
    ----------
    dataset :

    variable :

    See Also
    --------
    magtogoek/quality_control_common/data_spike_detection()
    """
    spikes_flag = data_spike_detection(
        dataset[variable].data,
        inner=SPIKE_DETECTION_PARAMETERS[variable]['inner'],
        outer=SPIKE_DETECTION_PARAMETERS[variable]['outer']
    )
    if variable + "_QC" not in dataset.variables:
        add_ancillary_QC_variable_to_dataset(dataset=dataset, variable=variable, default_flag=1)

    add_flags_values(variable + "_QC", spikes_flag * 3)

    test_comment = \
        f"Spike detection inner threshold {SPIKE_DETECTION_PARAMETERS[variable]['inner']} {SPIKE_DETECTION_PARAMETERS[variable]['units']} " \
        f"and outer threshold {SPIKE_DETECTION_PARAMETERS[variable]['outer']} {SPIKE_DETECTION_PARAMETERS[variable]['units']} (new_flag=3)"

    l.log(f"{variable} :" + test_comment)
    dataset[variable+"_QC"].attrs['quality_test'].append(test_comment + "\n")


def add_ancillary_QC_variable_to_dataset(dataset: xr.Dataset, variable: str, default_flag=1):
    """Add an ancillary variable named <variable>_QC to dataset."""
    dataset[variable + "_QC"] = (
        dataset[variable].dims, np.ones(dataset[variable].shape).astype(int) * default_flag,
        {'quality_test': "", "quality_date": Timestamp.now().strftime("%Y-%m-%d")}
    )
    dataset[variable + "_QC"].attrs.update(FLAG_ATTRIBUTES)


def add_flags_values(ancillary_variable: NDArray, new_flags: NDArray):
    """Add `new_flags` values if it's greater than the current `ancillary_variable` values.

    Parameters
    ----------
    ancillary_variable :
        Variable to add `flag` value to.
    new_flags :
        Flag value to add.

    Returns
    -------

    """
    np.maximum(ancillary_variable, new_flags, out=ancillary_variable)


def merge_flags(flags_arrays: List[NDArray]) -> NDArray:
    """Merge flags_arrays keeping the greatest values"""
    return np.stack([flags_arrays], axis=-1).max(axis=-1)


if __name__ == "__main__":
    import xarray as xr

    # CLIMATOLOGY COMPARISON TEST #
    path = '/home/jeromejguay/WorkSpace/Data/Sillex2018/Raw/FreshWater/'
    # data_path = path + 'discharge1944_2019.nc'
    # clim_path = path + 'discharge1994_2019_clim.nc'

    data_2d_path = path + 'test_2d_data.nc'
    clim_2d_path = path + 'test_2d_clim.nc'

    ds = xr.open_dataset(data_2d_path)
    clim_ds = xr.open_dataset(clim_2d_path)

    _variable = 'discharge'
    _threshold = 1

    climatology_outlier_test(
        dataset=ds,
        climatology_dataset=clim_ds,
        variable=_variable,
        threshold=_threshold,
        depth_interpolation_method='linear'
    )

    outlier = find_climatology_outlier(
        dataset=ds,
        climatology_dataset=clim_ds,
        variable=_variable,
        threshold=_threshold,
        depth_interpolation_method='linear'
    )
    outlier.plot()


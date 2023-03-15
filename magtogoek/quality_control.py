import numpy as np
import xarray as xr
from nptyping import NDArray

from magtogoek.utils import resolve_relative_path, json2dict

IMPOSSIBLE_PARAMETERS_VALUES_FILE_PATH = resolve_relative_path("files/impossible_parameter_values.json", __file__)
IMPOSSIBLE_PARAMETERS_VALUES = json2dict(IMPOSSIBLE_PARAMETERS_VALUES_FILE_PATH)

SPIKE_DETECTION_PARAMETERS_FILE_PATH = resolve_relative_path("files/spike_thresholds.json", __file__)
SPIKE_DETECTION_PARAMETERS = json2dict(SPIKE_DETECTION_PARAMETERS_FILE_PATH)

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
CLIMATOLOGY_TIME_FORMATS = {
        'dayofyear': 'time.dayofyear',
        'weekofyear': 'time.week',
        'monthofyear': 'time.month',
        'season': 'time.season'
    }
SEASONS_ID = ('DJF', 'JJA', 'MAM', 'SON')


def outlier_values_test(data: NDArray, lower_limit: float, upper_limit: float) -> NDArray:
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


def climatology_outlier_test(
        dataset: xr.Dataset,
        climatology_dataset: xr.Dataset,
        variable: str,
        threshold: float,
        depth_interpolation_method='linear'
) -> xr.DataArray:
    """Flag data that are outside the climatology.

    Fixme Test needs to be carried out for:  different resolutions, missing values

    Return boolean dataarray with values of:

        [True] < (mean - threshold * std) <= [False] <= (mean + threshold * std) < [True]

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

    outlier = climatology_outlier_test(
        dataset=ds,
        climatology_dataset=clim_ds,
        variable=_variable,
        threshold=_threshold,
        depth_interpolation_method='linear'
    )
    outlier.plot()

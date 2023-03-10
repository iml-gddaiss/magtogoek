"""

TODO
-----



+ GLOBAL IMPOSSIBLE PARAMETER VALUES

"""
from typing import *
import numpy as np
from pandas import Timestamp
import xarray as xr
from magtogoek import logger as l, FLAG_VALUES, FLAG_MEANINGS, FLAG_REFERENCE

CLIMATOLOGY_TIME_FORMATS = {
        'dayofyear': 'time.dayofyear',
        'weekofyear': 'time.week',
        'monthofyear': 'time.month',
        'season': 'time.season'
    }
SEASONS_ID = ('DJF', 'JJA', 'MAM', 'SON')

QC_VARIABLES = [
    'atm_pressure',  # Need since atm_pressure is used for correction Dissolved Oxygen or compute Density
    'temperature',
    'salinity',
    'density',
    'dissolved_oxygen',
    'ph',
    'par',
    'fluorescence',
    'chlorophyll',
    'fdom',
    'co2_w',
]


def no_meteoce_quality_control(dataset: xr.Dataset):
    """
    Notes
    -----
        SeaDataNet Quality Control Flags Value
        * 0: no_quality_control
    """
    l.section("Meteoce Quality Control")

    l.log("No quality control carried out")

    _add_ancillary_variables_to_dataset(dataset, default_flag=0)

    dataset.attrs["flags_reference"] = FLAG_REFERENCE
    dataset.attrs["flags_values"] = FLAG_VALUES
    dataset.attrs["flags_meanings"] = FLAG_MEANINGS
    dataset.attrs["quality_comments"] = "No quality control."


def meteoce_quality_control(
        dataset: xr.Dataset,

        climatology_variables: List[str] = None,
        climatology_dataset: xr.Dataset = None,
        climatology_threshold: float = None,
        climatology_depth_interpolation_method: str = None,

):
    """

    Flag propagation:

    Pressure -> Depth
    Depth, Temperature, Salinity -> Density
    Pressure, Temperature, Salinity -> Dissolved Oxygen
    Temperature, Salinity -> pH


    Parameters
    ----------
    dataset

    climatology_variables
    climatology_dataset
    climatology_threshold
    climatology_depth_interpolation_method


    Notes
    -----
       Tests return `True` where cells fail a test.

       SeaDataNet Quality Control Flags Value
       * 0: no_quality_control
       * 1: good_value
       * 2: probably_good_value
       * 3: probably_bad_value
           - Unusual data value, inconsistent with real phenomena.
       * 4: bad_value
           - Obviously erroneous data value.
       * 5: changed_value
       * 6: value_below_detection
       * 7: value_in_excess
       * 8: interpolated_value
       * 9: missing_value


    Todos
    -----
    + spike detection
    + absolute limit detection
    + Flag propagation
    + Flag Comments attrs.

    """
    l.section("Meteoce Quality Control")

    l.warning('QUALITY CONTROL IN DEVELOPMENT')

    _add_ancillary_variables_to_dataset(dataset)

    if climatology_variables is not None:
        for variables in climatology_variables:
            _flag_climatology_outlier(
                dataset=dataset,
                climatology_dataset=climatology_dataset,
                variables=variables,
                threshold=climatology_threshold,
                depth_interpolation_method=climatology_depth_interpolation_method
            )


    # spike detection


    # absolute limit detection


    # Flag propagation


    # Flag Comments attrs.

    dataset.attrs["quality_comments"] = l.logbook.split("[Meteoce Quality Control]\n")[1]

    dataset.attrs["flags_reference"] = FLAG_REFERENCE
    dataset.attrs["flags_values"] = FLAG_VALUES
    dataset.attrs["flags_meanings"] = FLAG_MEANINGS


def _add_ancillary_variables_to_dataset(dataset: xr.Dataset, default_flag: int = 1):
    for variable in QC_VARIABLES:
        if variable in dataset.variables:
            dataset[variable + "_QC"] = (
                ['time'], np.ones(dataset.time.shape).astype(int) * default_flag,
                {
                    'quality_test': "",
                    "quality_date": Timestamp.now().strftime("%Y-%m-%d"),
                    "flag_meanings": FLAG_MEANINGS,
                    "flag_values": FLAG_VALUES,
                    "flag_reference": FLAG_REFERENCE
                }
            )


def meteoce_absolute_outlier_test(dataset: xr.Dataset):
    #TODO
    pass


def _flag_climatology_outlier(
        dataset: xr.Dataset,
        climatology_dataset: xr.Dataset,
        variables: str,
        threshold: float,
        depth_interpolation_method: str,
):

    for variable in variables:
        try:
            find_climatology_outlier(
                dataset=dataset,
                climatology_dataset=climatology_dataset,
                variable=variable,
                threshold=threshold,
                depth_interpolation_method=depth_interpolation_method
            )
            l.log(f'Climatology outlier QC carried out on {variable}.') # TODO
        except ValueError as msg:
            l.warning(f'Unable to carry out climatology outlier qc on {variable}.\n\t Error: {msg}') #TODO
    pass


def find_climatology_outlier(
        dataset: xr.Dataset,
        climatology_dataset: xr.Dataset,
        variable: str,
        threshold: float,
        depth_interpolation_method ='linear'
):
    """
    Fixme Test needs to be carried out for:
     - different resolutions
     - missing values
    Interpolation Method:
        Default: linear.
        - nearest, cubic, (see xarray documentation)

    ORDINAL DAY CLIMATOLOGY

    IMPORTANT
    ---------
    Flag propagation for Density/Oxygen/pH after correction.

    """
    # Check for the variable in the dataset
    if variable not in dataset:
        raise KeyError(f'Variable not found in dataset {variable}')

    # Check for climatology variables `mean` and `std
    for var in [variable + s for s in ('_mean', '_std')]:
        if var not in climatology_dataset:
            raise KeyError(f'variable not in climatology dataset {var}')

    clim_time = get_climatology_time_coord(climatology_dataset, variable)

    # Group Data into clim_time
    grouped_data = dataset[variable].groupby(clim_time)

    # Nearest interpolation of the climatology to over the dataset depths.
    if 'depth' in dataset.variables and 'depth' in climatology_dataset:
        climatology_dataset = climatology_dataset.interp(depth=dataset.depth, method=depth_interpolation_method)

    # Defining upper and lower limits
    lower_limits = climatology_dataset[variable + '_mean'] - threshold * climatology_dataset[variable + '_std']
    upper_limits = climatology_dataset[variable + '_mean'] + threshold * climatology_dataset[variable + '_std']

    # Returns boolean array where outlier return True.
    return (grouped_data > upper_limits) | (grouped_data < lower_limits)


def get_climatology_time_coord(dataset: xr.Dataset, variable: str) -> str:
    """TODO"""
    mean_clim_time = _get_climatology_dataarray_time_coord(dataset[variable + '_mean'])
    std_clim_time = _get_climatology_dataarray_time_coord(dataset[variable + '_std'])
    if mean_clim_time != std_clim_time:
        raise ValueError(f'The mean and std climatology for {variable} have different climatological time coords.')

    clim_time = mean_clim_time

    if clim_time == 'time.season':
        if set(dataset.season.values) != set(SEASONS_ID):
            raise ValueError("Invalid season ID for climatology. Season IDs: ['DJF', 'JJA', 'MAM', 'SON'].")

    return clim_time


def _get_climatology_dataarray_time_coord(dataarray: xr.DataArray) -> str:
    """TODO"""
    intersection = set(dataarray.coords).intersection(set(CLIMATOLOGY_TIME_FORMATS.keys()))
    if len(intersection) == 1:
        return intersection[0]
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
    threshold = 1

    outlier = find_climatology_outlier(
        dataset=ds,
        climatology_dataset=clim_ds,
        variable=_variable,
        threshold=threshold,
        depth_interpolation_method='linear'
    )
    outlier.plot()



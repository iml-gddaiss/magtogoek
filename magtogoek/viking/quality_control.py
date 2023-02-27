"""

TODO
-----

+ Spike Detection:  From CTD_ODF_qualite_en.docx

    + This should depend on the frequency of the Probe.

    + Without First and Last Records

           V2
           +
          / \  V3
       V1/   +---
    ----+
    Spike when:
        |V2 - (V3+V1)/2| - |(V1-V3)/2| >= Thres
        |V2 - V2'| - dV >= Thres

    Thresholds

    - Pres: 5 db  (docs says in `m`).
    - Temp: 2 C
    - PSAL: 0.3 psu
    - DOXY: 0.3 mL/L
    - PH: 0.03

    + For First and Last Records

           V2      V1
           +     ---+
          /   Or     \
       V1/            \ V2
    ----+              +

    Spike when:
        |V1 - V2| >= Thres

    Thresholds

    - Pres: 25 db  (docs says in `m`).
    - Temp: 10 C
    - PSAL: 5 psu
    - DOXY: 3.5 mL/L
    - PH: 0.5




+ Data Drift over Time:
++ Linear regression on data ?
++ Linear correction with post-mission calibration.
  - Considering constant drift: t_start = 0, t_end = 1

+ Median Filter

+ Calibration with In-Situ Measurements.

+ Oxygen Winkler

+ GLOBAL IMPOSSIBLE PARAMETER VALUES

"""
from nptyping import NDArray
from typing import *
import numpy as np
import xarray as xr
from magtogoek import logger as l


CLIMATOLOGY_TIME_FORMATS = {
        'dayofyear': 'time.dayofyear',
        'weekofyear': 'time.week',
        'monthofyear': 'time.month',
        'season': 'time.season'
    }
SEASONS_ID = ('DJF', 'JJA', 'MAM', 'SON')


def no_meteoce_quality_control(dataset: xr.Dataset):
    l.warning('NO QUALITY CONTROL AVAILABLE')
    return dataset


def meteoce_quality_control(dataset: xr.Dataset):
    l.warning('NO QUALITY CONTROL AVAILABLE')
    return dataset


def climatology_outlier(
        dataset: xr.Dataset,
        climatology_dataset: xr.Dataset,
        variable: str,
        threshold: float,
        depth_interpolation_method='linear',
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

    # Returns boolean array where oulier return True.
    return (grouped_data > upper_limits) | (grouped_data < lower_limits)


def get_climatology_time_coord(dataset: xr.Dataset, variable: str) -> str:
    """
    FIXME TEST
    Parameters
    ----------
    dataset:

    variable:

    Returns
    -------

    """

    mean_clim_time = _get_climatology_time_coord(dataset[variable + '_mean'])
    std_clim_time = _get_climatology_time_coord(dataset[variable + '_std'])
    if mean_clim_time != std_clim_time:
        raise ValueError('The mean and std climatology for {variable} have different climatological time coords.')

    clim_time = mean_clim_time

    if clim_time == 'time.season':
        if set(dataset.season.values) != set(SEASONS_ID):
            raise ValueError("Invalid season ID for climatology. Season IDs: ['DJF', 'JJA', 'MAM', 'SON']")

    return clim_time


def _get_climatology_time_coord(dataarray: xr.DataArray) -> str:
    """

    Parameters
    ----------
    dataarray

    Returns
    -------

    """
    intersection = set(dataarray.coords).intersection(set(CLIMATOLOGY_TIME_FORMATS.keys()))
    if len(intersection) == 1:
        return intersection[0]
    else:
        raise ValueError(f'Climatology time not found in climatology dataset for variable: {dataarray.name}.')




if __name__ == "__main__":
    import matplotlib.pyplot as plt
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

    outlier = climatology_outlier(
        dataset=ds,
        climatology_dataset=clim_ds,
        variable=_variable,
        threshold=threshold,
        depth_interpolation_method='linear'
    )
    outlier.plot()



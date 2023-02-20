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

THRESHOLD_1 = { # TO BE REMOVED MAYBE
    "pres": 5, # db docs says `m`
    "temperature": 2,
    "salinity": 0.3,
    "dissolved_oxygen": 0.3, # mL/L
    "ph": 0.03,
}
THRESHOLD_2 = {
    "pres": 25, # db docs says `m`
    "temperature": 10,
    "salinity": 5,
    "dissolved_oxygen": 3.5, # mL/L
    "ph": 0.05,
}


def no_meteoce_quality_control(dataset: xr.Dataset):
    l.warning('NO QUALITY CONTROL AVAILABLE')
    return dataset


def meteoce_quality_control(dataset: xr.Dataset):
    l.warning('NO QUALITY CONTROL AVAILABLE')
    return dataset


def climatology_outlier(
        data: NDArray,
        clim_time_format: str,
        clim_mean: NDArray,
        clim_std: NDArray,
        threshold: float):
    """

    Parameters
    ----------
    data

    clim_time_format:
        Possible values: `dayofyear, week, month`

    clim_mean:
        Length depends on clim_time_format: [365, 52, 12]

    clim_std:
        Length depends on clim_time_format: [365, 52, 12]

    threshold

    Returns
    -------

    """
    # check lengths
    pass

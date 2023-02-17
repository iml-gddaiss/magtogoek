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

THRESHOLD_1 = {
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


def spike_detection(data: NDArray, threshold_1: float, threshold_2: float):
    """ # FIXME

    # use some fraction of the variance of the diff. ?

        |V2 - (V3+V1)/2| - |(V1-V3)/2|  >= Thres

    Parameters
    ----------
    data
    threshold_1 :
        Threshold for data without first and last values.
    threshold_2 :
        Threshold for the first and last values.

    Returns
    -------

    """
    spikes = np.zeros(data.shape).astype(bool)
    v1 = data[0:-2]
    v2 = data[1:-1]
    v3 = data[2:]

    spikes[0] = np.abs(data[1] - data[0]) >= threshold_2
    spikes[1:-1] = np.abs(v2 - (v3 + v1)/2) - np.abs(v1 - v3)/2 >= threshold_1
    spikes[-1] = np.abs(data[-1] - data[-2]) >= threshold_2

    return spikes



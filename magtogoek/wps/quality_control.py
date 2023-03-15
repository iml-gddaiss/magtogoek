"""

"""
import xarray as xr
from nptyping import NDArray

import numpy as np

from magtogoek import logger as l
from magtogoek.quality_control import SPIKE_DETECTION_PARAMETERS


def spike_detection_test(data: NDArray, inner_thres: float, outer_thres: float):
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

    Notes
    -----
    Spike Detection:  From CTD_ODF_qualite_en.docx

        This should depend on the frequency of the Probe.

        Without First and Last Records Suggested Thresholds.
            - Pres: 5 db  (docs says in `m`).
            - Temp: 2 C
            - PSAL: 0.3 psu
            - DOXY: 0.3 mL/L
            - PH: 0.03

        For First and Last Records Suggested Thresholds.
            - Pres: 25 db  (docs says in `m`).
            - Temp: 10 C
            - PSAL: 5 psu
            - DOXY: 3.5 mL/L
            - PH: 0.5

    """
    spikes = np.zeros(data.shape).astype(bool)
    v1 = data[0:-2]
    v2 = data[1:-1]
    v3 = data[2:]

    spikes[0] = np.abs(data[1] - data[0]) >= outer_thres
    spikes[1:-1] = np.abs(v2 - (v3 + v1)/2) - np.abs(v1 - v3) / 2 >= inner_thres
    spikes[-1] = np.abs(data[-1] - data[-2]) >= outer_thres

    return spikes


def _spike_detection_tests(dataset: xr.Dataset):
    """
    Iterates over SPIKE_DETECTION (in magtogoek/__init__) for inner and outer absolute values.
    """
    for variable in set(dataset.variables).intersection(set(SPIKE_DETECTION_PARAMETERS.keys())):
        spikes_flag = spike_detection_test(
            dataset[variable].data,
            inner=SPIKE_DETECTION_PARAMETERS[variable]['inner'],
            outer=SPIKE_DETECTION_PARAMETERS[variable]['outer']
        )
        dataset[variable + "_QC"][spikes_flag] = 3

        test_comment = \
            f"Spike detection inner threshold {SPIKE_DETECTION_PARAMETERS[variable]['inner']} {SPIKE_DETECTION_PARAMETERS[variable]['units']} " \
            f"and outer threshold {SPIKE_DETECTION_PARAMETERS[variable]['outer']} {SPIKE_DETECTION_PARAMETERS[variable]['units']} (flag=3)"

        l.log(f"{variable} :" + test_comment)
        dataset[variable+"_QC"].attrs['quality_test'].append(test_comment + "\n")

"""

"""
from nptyping import NDArray

import numpy as np

INNER_THRESHOLDS = { # TO BE REMOVED MAYBE
    "pres": 5, # db docs says `m`
    "temperature": 2,
    "salinity": 0.3,
    "dissolved_oxygen": 0.3, # mL/L
    "ph": 0.03,
}
OUTER_THRESHOLDS = {
    "pres": 25, # db docs says `m`
    "temperature": 10,
    "salinity": 5,
    "dissolved_oxygen": 3.5, # mL/L
    "ph": 0.05,
}


def spike_detection(data: NDArray, inner_thres: float, outer_thres: float):
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

from nptyping import NDArray

import numpy as np

def spike_detection(data: NDArray, threshold_1: float, threshold_2: float):
    """ Spike detection.

    ```Algorithm without first and last values:

        |V2 - (V3+V1)/2| - |(V1-V3)/2|  >= Threshold_1
    ```

    ```Algorithm for first and last values:

        |V2 - v1|  >= Threshold_2
    ```


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
"""
Date: February 2023
Made by jeromejguay

This script contains correction algorithm for Water Property Sensor (WPS) data.

"""
import numpy as np
from typing import List

from magtogoek.wps.sci_tools import rinko_raw_measurement_from_dissolved_oxygen, dissolved_oxygen_from_rinko_raw_measurement


def dissolved_oxygen_correction_winkler(
        dissolved_oxygen: np.ndarray,
        temperature: np.ndarray,
        rinko_coeffs: List[float],
        winkler_coeffs: List[float],
):
    """
    Sensor raw values are retro computed using the calibration coefficients [d0, d1, d2, c0, c1, c2],
    and then the dissolved oxygen is re-computed using the Winkler coefficients [d1_w, d2_w] for [d1, d2].

    Parameters
    ----------
    dissolved_oxygen :

    temperature :

    rinko_coeffs :
        [d0, d1, d2, c0, c1, c2]
    winkler_coeffs :
        Winkler coefficients [d1_w, d2_w]

    Returns
    -------
        Winkler corrected dissolved oxygen.

    Notes
    -----
    Needs to be done on uncorrected data (in pressure or salinity).
    """
    raw = rinko_raw_measurement_from_dissolved_oxygen(dissolved_oxygen=dissolved_oxygen, temperature=temperature, coeffs=rinko_coeffs)

    rinko_coeffs[1:3] = winkler_coeffs

    return dissolved_oxygen_from_rinko_raw_measurement(raw=raw, temperature=temperature, coeffs=rinko_coeffs)



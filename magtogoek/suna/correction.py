"""
Made by JeromeJGuay
Date 28th January 2022

NO3- Correction algorithm.
Based on:

      |------------------------------------------------------------------------------------|
      | Improved algorithm for the computation of nitrate concentrations in seawater using |
      |                 an in situ ultraviolet spectrophotometer.                          |
      |                                                             -Sakamoto et al, 2009  |
      |------------------------------------------------------------------------------------|

A    : Absorption
I    : Intensity (count)
b    : Probe Path Lenght
mA    : measured Absorption
ACDOM : Absorption of Colored Dissolved organic Matter : Linear Fit a0 + wave_length*a1
ASW  : Absorption of Sea Water
ESW  : Extinction of Sea Water
AN : Absorption of NO3-
EN : Extinction of NO3-
AB : expected Absorption of Sea Water (bromide)
T    : Temperature
Tis  : In Situ Temperature
Tcal : Calibration Temperature -> linear coefficients fit


See Also
--------
Start at 1:03:39 for Calibration and raw file processing.
https://www.youtube.com/watch?v=_xfns1rLGCU&t=3973s&ab_channel=LUDOVICFOUILLE

"""

import numpy as np

#import scipy as sp
# sp.optimize.curve_fit(
#     lambda, temperature, a,b,c,d: (a+b*temperature)*np.exp((c+d*temperature)*(lambda-210))
# lambda, temperature)


def compute_absorbance_from_intensity(intensity: np.ndarray[int], dwi: np.ndarray[int], dark_intensity: int) -> float:
    """
    Parameters
    ----------
    intensity :
        count
    dwi :
        Deionized water intensity.
    dark_intensity :
        Dark intensity (background noise)
    """

    return -np.log10((intensity - dark_intensity) / (dwi - dark_intensity))


def compute_absorption_sea_water(wave_length: np.ndarray, temperature: np.ndarray, coeff):
    """

    Parameters
    ----------
    wave_length
    temperature
    coeff :
        Fitting coefficient [A, B, C, D] from equation (4) Sakamoto et al, 2009.

    Returns
    -------

    """
    return (coeff[0]+coeff[1]*temperature)*np.exp((coeff[2]+coeff[3]*temperature)*(wave_length-210))



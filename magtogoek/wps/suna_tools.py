"""
Made by JeromeJGuay
Date 28th January 2022

[NO3-] Correction algorithm | IMPORTANT Test of the algorithm were inconclusive.

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
import matplotlib
matplotlib.use('Qt5Agg')

import numpy as np
from datetime import datetime, timedelta
import pandas as pd
import re
import matplotlib.pyplot as plt
import scipy as sp

RAW_HEADERS = ['Header and Serial Number', 'Date year and day-of-year',
               'Time, hours of day', 'Nitrate concentration [uM]',
               'Nitrogen in nitrate [mg/L]', 'Absorbance at 254 nm',
               'Absorbance at 350 nm', 'Bromide trace [mg/L]',
               'Spectrum average', 'Dark value used for fit',
               'Integration time factor', 'Internal temperature [C]',
               'Spectrometer temperature [C]', 'Lamp temperature [C]',
               'Cumulative lamp on-time [s]', 'Relative Humidity [%]',
               'Main Voltage [V]', 'Lamp Voltage [V]',
               'Internal Voltage [V]',
               'Main current [mA]', 'Fit Aux 1', 'Fit Aux 2', 'Fit Base 1',
               'Fit Base 2', 'Fit RMSE', 'CTD Time [seconds since 1970]',
               'CTD Salinity [PSU]', 'CTD Temperature [C]',
               'CTD Pressure [dBar]', 'Check Sum']

for i in range(1, 257):  # write the channel header
    col = "channel " + str(i)
    RAW_HEADERS.insert(10 + i, col)

CAL_HEADERS = ['wavelength', 'no3', 'swa', 'tswa', 'reference']

CAL_NULL_VALUE = 99


def read_raw(filename):
    """
    SATSLF data
    """
    lambda_range = None
    linecount = 0
    with open(filename, 'r') as f:
        for line in f:
            linecount += 1
            if "xml" in line:
                continue
            # elif "SATFHR" in line:
            #     if "Wavelength Fit  Range" in line:
            #         lambda_range = tuple(map(float, re.findall(r"[-+]?(?:\d*\.\d+|\d+)", line)))
            elif 'SATSLF' in line:
                break


    df = pd.read_csv(filename, skiprows=linecount, names=RAW_HEADERS)

    decode_time(df)

    return df#, lambda_range


def decode_time(dataframe):
    time = []
    for date, hours in zip(dataframe['Date year and day-of-year'], dataframe['Time, hours of day']):
        date = str(date)
        time.append(datetime(int(date[:4]), 1, 1) + timedelta(days=int(date[-3:]), hours=float(hours)))
    dataframe['time'] = time


def get_channel(dataframe):
    return dataframe[[f"channel {i}" for i in range(1,257)]]


def read_calibration(filename):
    """
    H,CONC_CAL_SWA 34.99
    H,T_CAL_SWA 20.00

    E, data

    Returns
    -------
    calibration :
        dataframe ?
    metadata :
        dict ?
    """
    t_cal = None
    s_cal = None
    int_period = None
    linecount = 0
    with open(filename, 'r') as f:
        for line in f:
            if "H" in line:
                if "CONC_CAL_SWA" in line:
                    s_cal = float( re.findall(r"[-+]?(?:\d*\.\d+|\d+)", line)[0])
                if "T_CAL_SWA" in line:
                    t_cal = float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)", line)[0])
           #     if "INT_PERIOD":
            #        int_period = float(re.findall(r"[-+]?(?:\d*\.\d+|\d+)", line)[0])
            elif 'E' in line:
                break
            linecount += 1

    df = pd.read_csv(filename, skiprows=linecount, names=CAL_HEADERS)

    df[df==CAL_NULL_VALUE] = np.nan

    return df, s_cal, t_cal, int_period



def compute_measured_absorbance(intensity: np.ndarray, diw: np.ndarray, dark_intensity: int, diw_dark_intensity: int) -> float:
    """Compute absorbance adjusted for dark count and absorbance of de-ionized water.

    ```
    A = -log_10((I - I_Dark) / (I_DIW - I_Dark))

    I: Count
    I_Dark: Dark intensity
    I_DIW: Intensity of De-ionized Water
    ```

    Parameters
    ----------
    intensity :
        count
    diw :
        Deionized water intensity.
    dark_intensity :
        Dark intensity (background noise) df['Dark value used for fit']
    """
    return -np.log10((intensity - dark_intensity) / (diw - diw_dark_intensity))


def temperature_compensation_function(temperature: np.ndarray, coeffs: list, wave_length: np.ndarray, wavelength_offset: float):
    A, B, C, D = coeffs
    return (A + B * temperature) * np.exp((C + D * temperature) * (wave_length - wavelength_offset))

def temperature_extinction_of_seawater(
        seawater_extinction_t_cal: np.ndarray,
        calibration_temperature: float,
        temperature: np.ndarray,
        coeffs: list,
        wave_length: np.ndarray,
        wavelength_offset: float
):
    f_t = temperature_compensation_function(temperature=temperature, coeffs=coeffs,wave_length=wave_length,wavelength_offset=wavelength_offset)
    f_t_cal = temperature_compensation_function(temperature=calibration_temperature, coeffs=coeffs,wave_length=wave_length,wavelength_offset=wavelength_offset)
    return seawater_extinction_t_cal * f_t / f_t_cal


def absorbance_of_seawater(seawater_extinction: np.ndarray, salinity: float)->np.ndarray:
    return seawater_extinction * salinity

def absorbance_of_nitrate(measured_absorbance: np.ndarray, seawater_absorbance: np.ndarray)->np.ndarray:
    return measured_absorbance - seawater_absorbance


def beer_lamber_multilinear_fit(nitrate_absorbance: np.ndarray, wavelengths: np.ndarray, nitrate_extinction: np.ndarray):
    """

    Returns
    -------
    nitrate:

    popt:
        e, f, nitrate

    pcov:
    """


    if not nitrate_absorbance.shape == wavelengths.shape == nitrate_extinction.shape:
        raise ValueError("array length don't match.")
    def _optimize_fit(_data, _e, _f, _nitrate):
        _wavelengths, _nitrate_extinction = _data
        return _e + _f * _wavelengths + _nitrate * _nitrate_extinction

    popt, pcov = sp.optimize.curve_fit(_optimize_fit, [wavelengths, nitrate_extinction], nitrate_absorbance)
    _, _, nitrate = popt
    return nitrate, popt, pcov

if __name__ == "__main__":
    path = '/home/jeromejguay/ImlSpace/Data/iml4_2021/2021-IML4-Suna-1363/'
    raw_filename = 'D2021246.CSV'
    cal_file = path + '1363/SNA1363B.cal'

    #/home/jeromejguay/ImlSpace/Data/iml4_2021/2021-IML4-Suna-1363/1363/ZCoefDat.cal
    coeffs = [A,B,C,D] = 186.324, 0.789173, 0.000151474, -0.000000311447
    wavelength_offset = 0 #?
    cal, t_cal, s_cal , int_period = read_calibration(cal_file)


    ############ RAW DATA ##############
    df = read_raw(path + 'Raw/' + raw_filename)
    sample = df.iloc[0]

    l_range = (216.5, 240)

    in_situ_t = 8.4705
    in_situ_s = 27.7194

    ############ selected channel wavelength #####
    channels = sample['channel 1':'channel 256']
    channel_index = (cal['wavelength'] >= l_range[0]) & (cal['wavelength'] <= l_range[1])

    ############# DATA TO USE ###############

    raw_intensity = np.asarray(channels)[channel_index].astype(float)
    wavelengths = np.asarray(cal['wavelength'])[channel_index].astype(float)
    nitrate_extinction = np.asarray(cal['no3'])[channel_index].astype(float)
    seawater_extinction_t_cal = np.asarray(cal['swa'])[channel_index].astype(float)
    diw_blank = np.asarray(cal['reference'])[channel_index].astype(float)


    measured_absorbance = compute_measured_absorbance(raw_intensity, diw_blank, dark_intensity=0, diw_dark_intensity=0)

    seawater_extinction = temperature_extinction_of_seawater(
        seawater_extinction_t_cal=seawater_extinction_t_cal,
        calibration_temperature=t_cal,
        temperature=in_situ_t,
        coeffs=coeffs,
        wave_length=wavelengths,
        wavelength_offset=0
    )

    seawater_absorbance = absorbance_of_seawater(seawater_extinction=seawater_extinction, salinity=in_situ_s)

    nitrate_absorbance = absorbance_of_nitrate(measured_absorbance=measured_absorbance, seawater_absorbance=seawater_absorbance)

    nitrate, popt, pcov = beer_lamber_multilinear_fit(nitrate_absorbance, wavelengths, nitrate_extinction)

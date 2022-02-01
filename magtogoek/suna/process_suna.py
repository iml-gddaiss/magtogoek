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
import matplotlib
matplotlib.use('Qt5Agg')

import numpy as np
from datetime import datetime, timedelta
import pandas as pd
import re
import matplotlib.pyplot as plt

# import scipy as sp
# sp.optimize.curve_fit(
#     lambda, temperature, a,b,c,d: (a+b*temperature)*np.exp((c+d*temperature)*(lambda-210))
# lambda, temperature)
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
    SATFHR,Wavelength Fit  Range , 217.00 <-> 240.00
    SATSLF data
    """
    lambda_range = None
    linecount = 0
    with open(filename, 'r') as f:
        for line in f:
            linecount += 1
            if "xml" in line:
                continue
            elif "SATFHR" in line:
                if "Wavelength Fit  Range" in line:
                    lambda_range = tuple(map(float, re.findall(r"[-+]?(?:\d*\.\d+|\d+)", line)))
            elif 'SATSLF' in line:
                break


    df = pd.read_csv(filename, skiprows=linecount, names=RAW_HEADERS)

    decode_time(df)

    return df, lambda_range


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


def read_coeff_cal(filename):
    """
    C0 = lambda_0
    C1, C2, C3, C4 = A, B, C, D

    Skip all /, /*


    Returns
    -------
    lambda_0, coeff

    """
    pass


def compute_absorbance_from_intensity(intensity: np.ndarray, dwi: np.ndarray, dark_intensity: int) -> float:
    """
    Parameters
    ----------
    intensity :
        count
    dwi :
        Deionized water intensity.
    dark_intensity :
        Dark intensity (background noise) df['Dark value used for fit']
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
    return (coeff[0] + coeff[1] * temperature) * np.exp((coeff[2] + coeff[3] * temperature) * (wave_length - 210))


if __name__ == "__main__":
    path = '/home/jeromejguay/ImlSpace/Data/iml4_2021/2021-IML4-Suna-1363/'
    raw_filename = 'D2021246.CSV'#'D2021143.CSV'
    cal_files = ['SNA1363A.CAL',  'SNA1363B.CAL',  'SNA1363_.CAL']
    df, l_range = read_raw(path + 'Raw/' + raw_filename)

    cal, _, _ , int_period = read_calibration(path + 'SUNA/' + cal_files[2])
    calA, s_cal, t_cal, int_periodA = read_calibration(path + 'SUNA/' + cal_files[0])
    calB, _, _, int_periodB = read_calibration(path + 'SUNA/' + cal_files[1])

    dfc = get_channel(df)
    wavelength = np.linspace(l_range[0], l_range[1], 256)

    plt.figure('ref')
    plt.plot(cal['wavelength'], cal['reference']/500, label='0, 500') # DIW maybe
    plt.plot(calA['wavelength'], calA['reference']/450, label='A, 450')
    plt.plot(calB['wavelength'], calB['reference']/450,'--', label='B, 450')
    plt.plot(calA['wavelength'], dfc.loc[1]/375, label='data')
   # plt.xlim(l_range)
    plt.legend()
    plt.show()

    plt.figure('NO3')
    plt.plot(cal['wavelength'], cal['no3'], label='0') # DIW maybe
    plt.plot(calA['wavelength'], calA['no3'], label='A')
    plt.plot(calB['wavelength'], calB['no3'], '--', label='B')
   # plt.xlim(l_range)
    plt.legend()
    plt.show()

    plt.figure('swa')
    plt.plot(cal['wavelength'], cal['swa'], label='0') # DIW maybe
    plt.plot(calA['wavelength'], calA['swa'], label='A')
    plt.plot(calB['wavelength'], calB['swa'], '--', label='B')
    #plt.xlim(l_range)
    plt.legend()
    plt.show()

    plt.figure('tswa')
    plt.plot(cal['wavelength'], cal['tswa'], label='0')  # DIW maybe
    plt.plot(calA['wavelength'], calA['tswa'], label='A')
    plt.plot(calB['wavelength'], calB['tswa'], '--', label='B')
    #plt.xlim(l_range)
    plt.legend()
    plt.show()


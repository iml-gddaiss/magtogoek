"""
Correction algorithm for Water Property Sensor (WPS) data.

cal coeff      : c0, c1, c2, d0
pressure coeff : cp
salinity coeff : b0, b1, b2, b3, b4
winkler coeff  : d1, d2


"""
from nptyping import NDArray
import numpy as np
#import pandas as pd
import xarray as xr
from typing import List

from magtogoek.wps.sci_tools import voltEXT_from_pHEXT, pHEXT_from_voltEXT, compute_scaled_temperature, \
    rinko_raw_measurement_from_dissolved_oxygen, dissolved_oxygen_from_rinko_raw_measurement

# RINKO_COEFFS_KEYS = ('c0', 'c1', 'c2', 'd0', 'cp',
#                      'b0', 'b1', 'b2', 'b3', 'b4',
#                      'd1', 'd2')


def pH_correction_for_salinity(temperature: NDArray,
                               salinity: NDArray,
                               ph_temperature: NDArray,
                               cal_psal: float, k0: float, k2: float) -> NDArray:
    """
    Recompute pH using in-situ salinity from a CTD.
    1. Compute the pH probe voltage using:
        -The pH measured by the ph sensor.
        -The temperature measured by the ph sensor (which was used to compute the pH).
        -The constant salinity used.
        -k0 and k1 coefficients.
    2. Compute the pH using:
        -pH probe voltage
        - In-situ temperature and salinity from a CTD
        -k0 and k1 coefficients.


    Parameters
    ----------
    temperature :
        temperature measured by CTD in Celsius
    salinity :
        Practical salinity measured by CTD
    ph_temperature :
        temperature measured by pH sensor.
    cal_psal :
        Constant salinity (From Calibration).
    k0 :
        Exterior cell standard potential Offset (From Calibration).
    k2 :
        Exterior temperature slope coefficient (From Calibration).

    Returns
    -------
        Corrected pH

    """
    volt = voltEXT_from_pHEXT(temp=ph_temperature, psal=cal_psal, k0=k0, k2=k2)
    ph = pHEXT_from_voltEXT(temp=temperature, psal=salinity, volt=volt, k0=k0, k2=k2)

    return ph


def dissolved_oxygen_correction_winkler(
        dissolved_oxygen: NDArray,
        temperature: NDArray,
        coeffs: List[float],
        winkler_coeffs: List[float],
):
    """
    Sensor raw values are retro computed using the calibration coefficients [d0, d1, d2, c0, c1, c2],
    and then the dissolved oxygen is re-computed using the Winkler coefficients [d1_w, d2_w] for [d1, d2].

    Parameters
    ----------
    dissolved_oxygen :

    temperature :

    coeffs :
        [d0, d1, d2, c0, c1, c2]
    winkler_coeffs :
        Winkler coefficients [d1_w. d2_w]

    Returns
    -------
        Winkler corrected dissolved oxygen.

    Notes
    -----
    Needs to be done on uncorrected data (in pressure or salinity).
    """
    raw = rinko_raw_measurement_from_dissolved_oxygen(dissolved_oxygen=dissolved_oxygen, temperature=temperature, coeffs=coeffs)

    coeffs[1:3] = winkler_coeffs

    return dissolved_oxygen_from_rinko_raw_measurement(raw=raw, temperature=temperature, coeffs=coeffs)


def dissolved_oxygen_correction_for_salinity_SCOR_WG_142(dissolved_oxygen: NDArray, salinity: NDArray, temperature: NDArray):
    """Compute salinity compensated dissolved oxygen using SCOR WG 142 recommended coefficients.

    ```(Benson and Krause, 1984; García and Gordon, 1992)
    DO_sc = DO*exp[
            a0 + ac
    T_s = ln[(298.15 - T) / (273.15 + T)]

    DO: dissolved oxygen
    T_s : Scaled temperature
    T : temperature as measured by the in-situ sensor
    S : Salinity [PSU]
    a0, a1, a2, a3, a4, a5 = 2.00907, 3.22014, 4.0501, 4.94457, -0.256847, 3.88767
    b0, b1, b2, b3 = -6.24523e-3, -7.37614e-3, -1.03410e-2, -8.17083e-3
    c0 = -4.8868e-7
    ```

    Parameters
    ----------
    dissolved_oxygen :
        Dissolved oxygen as measured by in-situ sensor.
    salinity : [PSU]
        Practical salinity
    temperature :
        temperature as measured by the in-situ sensor

    Returns
    -------
        Salinity compensated dissolved oxygen

    References
    ----------
    .. [1] Benson and Krause 1984, Limnology and Oceanography, The concentration and isotopic fractionation of oxygen
            dissolved in freshwater and seawater in equilibrium with the atmosphere.
    .. [2] García and Gordon 1992, Limnology and Oceanography, Oxygen solubility in seawater: Better fitting equations.
    .. [3] Bittig et al. 2018, SCOR WG 142: Quality Control Procedures for Oxygen and Other Biogeochemical Sensors on
            Floats and Gliders. Recommendations on the conversion between oxygen quantities for Bio-Argo floats and
            other autonomous sensor platforms. https://doi.org/10.13155/45915

    """
    a0, a1, a2, a3, a4, a5 = 2.00907, 3.22014, 4.0501, 4.94457, -0.256847, 3.88767
    b0, b1, b2, b3 = -6.24523e-3, -7.37614e-3, -1.03410e-2, -8.17083e-3
    c0 = -4.8868e-7

    t_s = compute_scaled_temperature(temperature)

    poly_a = a0 + a1*t_s + a2*t_s**2 + a3*t_s**3 + a4*t_s**4 + a5*t_s**5
    poly_b = b0 + b1*t_s + b2*t_s**2 + b3*t_s**3

    oxy_solubility = np.exp(poly_a + poly_b*salinity + c0*salinity**2)

    return dissolved_oxygen * oxy_solubility


def dissolved_oxygen_correction_for_pressure_JAC(
        dissolved_oxygen: NDArray, pressure: NDArray
) -> NDArray:
    """Dissolved oxygen pressure correction for JAC(ARO-FT) oxygen sensor.

    ```(Thierry et al., 2022; Uchida et al., 2010)

    DO_pc = DO * [1 + cp * Pressure / 1000]

    DO : dissolved oxygen
    Pressure : pressure in dbar

    cp : Pressure coefficient = 0.032

    ```

    Parameters
    ----------
    dissolved_oxygen :
        Dissolved oxygen [umol/kg] (I don't know why the units matters)...
    pressure :
        Pressure in dbar


    Returns
    -------
        Pressure compensated dissolved oxygen.

    References
    ----------
    .. [1] Thierry Virginie, Bittig Henry, Gilbert Denis, Kobayashi Taiyo, Kanako Sato, Schmid Claudia (2022).
            Processing Argo oxygen data at the DAC level. DOI: https://doi.org/10.13155/39795
    .. [2] Uchida et al. 2010, IOCCP Report Number 14; ICPO Publication Series Number 134,
            CTD Oxygen Sensor Calibration Procedures, DOI: https://doi.org/10.25607/OBP-1344

    """
    cp = 0.032

    return dissolved_oxygen * (1 + cp * pressure / 1000)


def time_drift_correction(data: NDArray, data_time: NDArray, drift: NDArray, drift_time: NDArray) -> NDArray:
    """Apply correction for drift over time as a linear drift. fixme Test

    ```
    data_corrected(time) = data(time) - drift(time)
    ```

    Drift slope can vary between drift_time segments.

    Drift and time_drift should include the drift for the first and last times of the data_time.

    Drifts values are relative to the initial drift which should be 0.

    Parameters
    ----------
    data
    data_time

    drift :
        Vector of the amount of drift.
    drift_time
        Drift times for the corresponding drifts.

    Returns
    -------

    """
    if len(drift) < 2:
        raise ValueError('`drift` must contains at least 2 values.')

    _data = xr.DataArray(data, coords={'time': data_time})
    _drift = xr.DataArray(drift, coords={'time': drift_time})

    return data - _drift.interp(time=_data.time).data


def in_situ_sample_correction(data: NDArray, slope: float, offset: float):
    """Apply a linear correction using pre-computed linear regression coefficient. fixme TEST

    ```
    data_corr = slope * data + offset
    ```


    Parameters
    ----------
    data
    slope
    offset

    Returns
    -------

    """

    return slope * data + offset




if __name__ == "__main__":
    import pandas as pd
    import matplotlib.pyplot as plt

    data = np.random.random(200)
    data_time = pd.date_range('2020-05-01', '2020-09-01', 200)

    drift = np.array([0, 1, 3, 3.5])
    drift_time = pd.date_range('2020-05-01', '2020-09-01', 4)

    data_raw = time_drift_correction(data, data_time, -drift, drift_time)

    data_c = time_drift_correction(data_raw, data_time, drift, drift_time)


    plt.figure()
    plt.plot(data_raw, data_time, label='raw')
    plt.plot(data_c, data_time, label='corrected')
    plt.plot(drift, drift_time, label='drift')

    plt.legend()
    plt.show()



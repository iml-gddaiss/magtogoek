"""
Date: January 2023
Made by jeromejguay


This module contains Water Property Sensor (WPS) related mathematical and scientific functions.

Notes:
    This repository has better documentation on functions and additionnal function.
    Could be a good reference for improvements.

    https://github.com/ooici/ion-functions/blob/master/ion_functions/data/do2_functions.py

"""
import numpy as np
from nptyping import NDArray
from seawater import eos80 as eos
from typing import Union, List

GAS_CONSTANT = 8.31446261815324  # the constant in seabird docs differs 8.3144621 J/(K mol). Application Note 99
FARADAY_CONSTANT = 96485.365


def compute_density(
        temperature: np.ndarray,
        salinity: np.ndarray,
        pres: Union[float, List, np.ndarray] = None
):
    """Compute density using seawater package eos80 functions.

    Compute at sea surface if no `pres` is provided.

    Parameters
    ----------
    temperature :
        (ITS-90)
    salinity :
        (pss-78)
    pres :
        dbar

    Returns
    -------
        density
    """

    if pres is not None:
        return eos.dens(salinity, temperature, pres)
    else:
        return eos.dens0(salinity, temperature)


def rinko_raw_measurement_from_dissolved_oxygen(
        dissolved_oxygen: NDArray,
        temperature: NDArray,
        coeffs: List[float],
):
    """Compute raw measurements from dissolved oxygen using the temperature and calibration coefficients.


    ```(Uchida et al., 2010)

    The equation used, differs from the one in Uchida et al. (2010) since we are settings {e0=1, t=0}.

                        1 + d0 * T
              ----------------------------------  - d1
        N =     DO * (c0 + c1 + c2 * T**2) + 1
             -------------------------------------------
                             d2

    DO: dissolved oxygen [umol/L]
    N: raw values
    T: temperatures
    d0, d1, d2, c0, c1, c2: Calibration Coefficients.
    ```

    Parameters
    ----------
    dissolved_oxygen :

    temperature :

    coeffs :
        [d0, d1, d2, c0, c1, c2]

    Returns
    -------
    Raw measurements of dissolved oxygen.

    References
    ----------
    .. [1] Uchida et al. 2010, IOCCP Report Number 14; ICPO Publication Series Number 134,
            CTD Oxygen Sensor Calibration Procedures, DOI: https://doi.org/10.25607/OBP-1344
    """
    d0, d1, d2, c0, c1, c2 = coeffs

    A = 1 + d0 * temperature
    B = dissolved_oxygen * (c0 + c1 + c2 * temperature ** 2) + 1

    return (A / B - d1) / d2


def dissolved_oxygen_from_rinko_raw_measurement(
        raw: NDArray,
        temperature: NDArray,
        coeffs: List[float]
):
    """Compute dissolved oxygen from raw measurements using the temperature and calibration coefficients.

    ```(Uchida et al., 2010)

    The equation used, differs from the one in Uchida et al. (2010) since we are settings {e0=1, t=0}.

    Equation used:

                   1 + d0 * T
                -----------------  - 1
        D0 =      d1 + d2 * raw
             ----------------------------
                 c0 + c1 + c2 * T**2

    DO: dissolved oxygen [umol/L]
    N: raw values
    T: temperatures
    d0, d1, d2, c0, c1, c2: Calibration Coefficients.
    ```

    Parameters
    ----------
    raw :

    temperature :

    coeffs :
        [d0, d1, d2, c0, c1, c2]

    Returns
    -------
    Dissolved oxygen [umol/L]

    References
    ----------
    .. [1] Uchida et al. 2010, IOCCP Report Number 14; ICPO Publication Series Number 134,
            CTD Oxygen Sensor Calibration Procedures, DOI: https://doi.org/10.25607/OBP-1344

    """

    d0, d1, d2, c0, c1, c2 = coeffs

    A = 1 + d0 * temperature
    B = d1 + d2 * raw
    C = (c0 + c1 + c2 * temperature ** 2)

    return (A / B - 1) / C


def dissolved_oxygen_ml_per_L_to_umol_per_L(dissolved_oxygen: np.ndarray, inverse=False) -> np.ndarray:
    """
    ```(García and Gordon, 1992)

    O2 [umol/L] = 44.6596 * O2 [ml/L]

    ```

    Parameters
    ----------
    dissolved_oxygen : [ml/L] or [umol/L] if inverse is True

    inverse :
        Do the reverse conversion.

    Returns
    -------
    dissolved_oxygen: [umol/L] or [ml/L] if inverse is True,

    References
    ----------
    .. [1] García and Gordon 1992, Limnology and Oceanography, Oxygen solubility in seawater: Better fitting equations.
    """
    coeff = 44.6596
    if inverse:
        return dissolved_oxygen / coeff
    return coeff * dissolved_oxygen


def dissolved_oxygen_umol_per_L_to_umol_per_kg(dissolved_oxygen: np.ndarray, density: np.ndarray) -> np.ndarray:
    """
    ```

    O2 [umol/kg] =  1000 [L/m3] * O2 [umol/L] / density [kg/m3]

    ```

    Parameters
    ----------
    dissolved_oxygen : [umol/L]
    density : [kg/m3]
        potential density

    Returns
    -------
    dissolved_oxygen [umol/kg]

    """

    return 1000 * dissolved_oxygen / density


def compute_scaled_temperature(temperature: np.ndarray) -> np.ndarray:
    """

    ```
    T_s = ln[(298.15 - T) / (273.15 + T)]```

    Parameters
    ----------
    temperature :
        Temperature as measured by in-situ sensor.

    Returns
    -------

    """
    return np.log((298.15 - temperature) / (273.15 + temperature))


def voltEXT_from_pHEXT(temp: np.ndarray, psal: float, ph: np.ndarray, k0: float, k2: float) -> np.ndarray:
    """Based on Seabird documentations

    Compute voltExt from the pHext, the temperature measured by the pH probe, the salinity used in the probe configuration
    and the K0 and K2 exterior calibration coefficient.

    ```(Johnson et al. 2016)
    V_EXT = S_nernst*(pH_EXT
                      - log(Cl_T)
                      - 2*log(Y_HCl)_T
                      + log(1 + S_T/K_S)
                      + log((1000 - 1.005 * psal) / 1000))) + k0_EXT + k2_EXT * t

    S_nernst = (R * T * ln(10)) / F

    T : temperature in Kelvin
    t : temperature in Celsius
    psal : salinity in PSU
    V_EXT : raw exterior voltage
    K0_EXT : Exterior cell standard potential Offset (From Calibration).
    K2_Ext : Exterior temperature slope coefficient (From Calibration).
    F : Faraday Constant
    K_S : acid_dissociation_constant_HSO4
    log(Y_HCl)_T : log_of_HCl_activity_as_temperature_function
    ```

    Parameters
    ----------
    temp :
        Temperature in Celsius.
    psal :
        Practical salinity.
    ph :
        Exterior pH.
    k0 :
        Exterior cell standard potential Offset (From Calibration).
    k2 :
        Exterior temperature slope coefficient (From Calibration).

    Returns
    -------
    volt :
        Exterior Voltage

    References
    ----------
    .. [1] Johnson et al.2016, Analytical Chemistry, DeepSea DuraFET: A pressure tolerant pH sensor designed for global sensor networks.

    .. [2] Sea-Bird Scientific, Technical Note on Calculating pH, Application Note 99
    """
    s_nernst = GAS_CONSTANT * (temp + 273.15) * np.log(10) / FARADAY_CONSTANT
    cl_t = total_chloride_in_seawater(psal=psal)
    log_y_hcl_t = log_of_HCl_activity_as_temperature_function(temp=temp, psal=psal)
    s_t = total_sulfate_in_seawater(psal=psal)
    k_s = acid_dissociation_constant_HSO4(temp=temp, psal=psal)

    return k0 + k2 * temp + s_nernst * (ph
                                        - np.log10(cl_t)
                                        - 2 * log_y_hcl_t
                                        + np.log10(1 + (s_t / k_s))
                                        + np.log10((1000 - 1.005 * psal) / 1000))


def pHEXT_from_voltEXT(temp: np.ndarray, psal: np.ndarray, volt: np.ndarray, k0: float, k2: float) -> np.ndarray:
    """Taken from Seabird documentations

    Compute pH exterior from the exterior voltage using in-situ temperature and salinity.
    pH exterior can be calculated from the pH value return by the probe with the `voltEXT_from_pHEXT`.

    ```(Johnson et al. 2016)
    pH_EXT = (V_EXT - k0_EXT - k2_EXT * t) / S_nernst
             + log(Cl_T)
             + 2*log(Y_HCl)_T
             - log(1 + S_T/K_S)
             - log((1000 - 1.005 * psal) / 1000))

    S_nernst = (R * T * ln(10)) / F

    T : temperature in Kelvin
    t : temperature in Celsius
    psal : salinity in PSU
    V_EXT : raw exterior voltage
    K0_EXT : Exterior cell standard potential Offset (From Calibration).
    K2_Ext : Exterior temperature slope coefficient (From Calibration).
    F : Faraday Constant
    K_S : acid_dissociation_constant_HSO4
    log(Y_HCl)_T : log_of_HCl_activity_as_temperature_function
    ```

    Parameters
    ----------
    temp :
        Temperature in Celsius.
    psal :
        Practical salinity.
    volt :
        Raw exterior voltage.
    k0 :
        Exterior cell standard potential Offset (From Calibration).
    k2 :
        Exterior temperature slope coefficient (From Calibration).

    Returns
    -------
    ph :
        Exterior pH

    References
    ----------
    .. [1] Johnson et al.2016, Analytical Chemistry, DeepSea DuraFET: A pressure tolerant pH sensor designed for global sensor networks.

    .. [2] Sea-Bird Scientific, Technical Note on Calculating pH, Application Note 99

    """
    s_nernst = GAS_CONSTANT * (temp + 273.15) * np.log(10) / FARADAY_CONSTANT
    cl_t = total_chloride_in_seawater(psal=psal)
    log_y_hcl_t = log_of_HCl_activity_as_temperature_function(temp=temp, psal=psal)
    s_t = total_sulfate_in_seawater(psal=psal)
    k_s = acid_dissociation_constant_HSO4(temp=temp, psal=psal)

    return ((volt - k0 - k2 * temp) / s_nernst
            + np.log10(cl_t)
            + 2 * log_y_hcl_t
            - np.log10(1 + (s_t / k_s))
            - np.log10((1000 - 1.005 * psal) / 1000))


def total_chloride_in_seawater(psal: np.ndarray) -> np.ndarray:
    """Taken from Seabird documentations

    ```(Dickson et al. 2007)
    Cl_T = (0.99889/35.453)*(S/1.80655)*(1000/(1000-1.005*S))

    S : Salinity in PSU
    ```

    Parameters
    ----------
    psal :
        practical salinity

    References
    ----------
    .. [1] Dickson et al. 2007, IOCCP Report No.8, Guide to Best Practices for Ocean CO2 Measurements

    .. [2] Sea-Bird Scientific, Technical Note on Calculating pH, Application Note 99
    """
    return (0.99889 / 35.453) * (psal / 1.80655) * (1000 / (1000 - 1.005 * psal))


def sample_ionic_strength(psal: np.ndarray) -> np.ndarray:
    """Taken from Seabird documentations

    ```(Dickson et al. 2007)
    I = (19.924*psal)/(1000-1.005*psal)

    psal : Salinity in PSU
    ```

    Parameters
    ----------
    psal :
        practical salinity

    References
    ----------
    .. [1] Dickson et al. 2007, IOCCP Report No.8, Guide to Best Practices for Ocean CO2 Measurements

    .. [2] Sea-Bird Scientific, Technical Note on Calculating pH, Application Note 99
    """
    return (19.924 * psal) / (1000 - 1.005 * psal)


def debye_huckel_HCl_activity_constant(temp: np.ndarray) -> np.ndarray:
    """Taken from Seabird documentations

    ```(Khoo et al. 1977)
    A_DH = 0.0000034286 * t**2 + 0.00067524 * t + 0.49172143

    t: temperature in Celsius
    ```

    Parameters
    ----------
    temp :
        temperature in Celsius

    References
    ----------
    .. [1] Khoo et al. 1977, Analytical Chemistry,
        Determination of hydrogen ion concentrations in seawater from 5C to 40C: standard potentials at salinities 20 to 45%

    .. [2] Sea-Bird Scientific, Technical Note on Calculating pH, Application Note 99
    """
    return 0.0000034286 * temp ** 2 + 0.00067524 * temp + 0.49172143


def log_of_HCl_activity_as_temperature_function(temp: np.ndarray, psal: np.ndarray) -> np.ndarray:
    """Taken from Seabird documentations

    ```(Khoo et al. 1977)
                     -A_DH * sqrt(I)
    log(Y_HCl)_T = --------------------  + (0.08885 - 0.000111 * t) * I
                   1 + 1.394 * sqrt(I)

    t: temperature in Celsius
    I : sample_ionic_strength
    A_DH : HCl_activity_constant
    ```

    Parameters
    ----------
    psal :
        practical salinity
    temp :
        temperature in Celsius

    References
    ----------
    .. [1] Khoo et al. 1977, Analytical Chemistry,
        Determination of hydrogen ion concentrations in seawater from 5C to 40C: standard potentials at salinities 20 to 45%

    .. [2] Sea-Bird Scientific, Technical Note on Calculating pH, Application Note 99
    """
    a_dh = debye_huckel_HCl_activity_constant(temp=temp)
    ionic_s = sample_ionic_strength(psal=psal)

    return -(a_dh * np.sqrt(ionic_s)) / (1 + 1.394 * np.sqrt(ionic_s)) + (0.08885 - 0.000111 * temp) * ionic_s


def total_sulfate_in_seawater(psal: np.ndarray) -> np.ndarray:
    """Taken from Seabird Documentations

    ```(Dickson et al. 2007)
    S_T = (0.1400 / 96.062) * (psal / 1.80655)

    psal : Salinity in PSU
    ```

    Parameters
    ----------
    psal :
        practical salinity

    References
    ----------
    .. [1]  Dickson et al. 2007, IOCCP Report No.8, Guide to Best Practices for Ocean CO2 Measurements

    .. [2]  Sea-Bird Scientific, Technical Note on Calculating pH, Application Note 99
    """

    return (0.1400 / 96.062) * (psal / 1.80655)


def acid_dissociation_constant_HSO4(temp: np.ndarray, psal: np.ndarray) -> np.ndarray:
    """Taken from Seabird documentations

    ```(Dickson et al. 2007)
    K_S = (1 - 0.001005 * S)*exp( a0 + a1 + a2 + a3 + a4)

    a0 = (-4276.1/T) + 141.328 - 23.093 * ln(T)
    a1 = ((-13856/T) + 324.57 - 47.986*ln(T))*sqrt(I)
    a2 = ((35474/T) - 771.54 + 114.723*ln(T))*I
    a3 = -(2698/T)*I**(3/2)
    a4 =  (1776/T)*I**2

    T : temperature in Kelvin
    S : Salinity in PSU
    I : sample_ionic_strength
    ```

    Parameters
    ----------
    psal :
        practical salinity
    temp :
        temperature in Celsius

    References
    ----------
    .. [1] Dickson et al. 2007, IOCCP Report No.8, Guide to Best Practices for Ocean CO2 Measurements

    .. [2] Sea-Bird Scientific, Technical Note on Calculating pH, Application Note 99
    """
    temp_k = temp + 273.15
    ionic_s = sample_ionic_strength(psal=psal)
    a0 = (-4276.1 / temp_k) + 141.328 - 23.093 * np.log(temp_k)
    a1 = ((-13856 / temp_k) + 324.57 - 47.986 * np.log(temp_k)) * np.sqrt(ionic_s)
    a2 = ((35474 / temp_k) - 771.54 + 114.723 * np.log(temp_k)) * ionic_s
    a3 = -(2698 / temp_k) * ionic_s ** (3 / 2)
    a4 = (1776 / temp_k) * ionic_s ** 2

    return (1 - 0.001005 * psal) * np.exp(a0 + a1 + a2 + a3 + a4)


def log_of_HCl_activity_as_temperature_and_pressure_function(psal: np.ndarray,
                                                             temp: np.ndarray,
                                                             pres: np.ndarray) -> np.ndarray:
    """(Khoo et al. 1977)

   log(Y_HCL)_TP = log_t + ((V_HCl * P) / (10 * ln(10) * R * T)) / 2

   log_t : log_of_HCl_activity_as_temperature_function
   V_HCl : partial molal volume of HCl cm**3/mol
   P : pressure in dbar
   R : Gas Constant
   T : temperature in Kelvin

   Parameters
   ----------
   psal :
       practical salinity
   temp :
       temperature in Celsius
   pres :
       pressure in dbar
   """
    temp_k = 273.15 + temp
    log_t = log_of_HCl_activity_as_temperature_function(psal=psal, temp=temp)
    v_hcl = partial_molal_volume_hcl(temp=temp)

    return log_t + ((v_hcl * pres) / (10 * np.log(10) * GAS_CONSTANT * temp_k)) / 2


def partial_molal_volume_hcl(temp: np.ndarray) -> np.ndarray:
    """(Millero 1983)

   V_HCl = 17.85 + 0.1044 * t - 0.001316 * t**2

   t: temperature in Celsius

   Parameters
   ----------
   temp :
       temperature in Celsius

   """
    return 17.85 + 0.1044 * temp - 0.001316 * temp ** 2

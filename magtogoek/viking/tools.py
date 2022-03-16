"""
Algorithm to process Viking instrument data.

cal coeff      : c0, c1, c2, d0
pressure coeff : cp
salinity coeff : b0, b1, b2, b3, b4
winkler coeff  : d1, d2

"""

import numpy as np
import xarray as xr

GAS_CONSTANT = 8.31446261815324

FARADAY_CONSTANT = 96485.365

RINKO_COEFFS_KEYS = ('c0', 'c1', 'c2', 'd0', 'cp',
                     'b0', 'b1', 'b2', 'b3', 'b4',
                     'd1', 'd2')


def _compensation_pres_temp_psal_rinko(dataset: xr.Dataset, coeffs):
    """
    See compensation_pres_temp_psal_rinko

    Parameters
    ----------
    dataset

    """
    dataset['dissolved_oxygen'].values = compensation_pres_temp_psal_rinko(
        doxy=dataset['dissolved_oxygen'],
        temp=dataset['temperature'],
        pres=dataset['pres'],
        psal=dataset['salinity'],
        coeffs=coeffs
    )


def compensation_pres_temp_psal_rinko(doxy: np.ndarray,
                                      temp: np.ndarray,
                                      pres: np.ndarray,
                                      psal: np.ndarray,
                                      coeffs: dict) -> np.ndarray:
    f"""
    

    Parameters
    ----------
    doxy :
        oxygen in ml/l
    temp :
    pres :
        pressure in dbar
    psal :
    coeffs :
        keys = ('c0','c1','c2','d0','cp','b0','b1','b2','b3','b4','d1','d2')

    Returns
    -------
        compensated_doxy in ml/L
        
    Notes
    -----
    cal coeff      : c0, c1, c2, d0
    pressure coeff : cp
    salinity coeff : b0, b1, b2, b3, b4
    winkler coeff  : d1, d2
    
    Notes
    -----
       Seabird documentation ? Maybe FIXME
    
    """
    if not all(key in coeffs.keys() for key in RINKO_COEFFS_KEYS):
        raise ValueError(f'Some coefficients are missing from `coeffs`. Required keys are {RINKO_COEFFS_KEYS}')
    if len({array.shape for array in [doxy, temp, pres, psal]}) != 1:
        raise ValueError('Arrays length mismatch.')

    _doxy = doxy * 44.66  # ml/L -> uM
    _pres = pres / 100  # dbar -> MPa

    doxy_pc = _doxy * (1 + coeffs['cp'] * _pres)

    temp_s = np.log10((298.15 - temp) / (273.15 + temp))

    doxy_sc = doxy_pc * (np.exp(coeffs['b0']
                                + coeffs['b1'] * temp_s
                                + coeffs['b2'] * temp_s ** 2
                                + coeffs['b3'] * temp_s ** 3)
                         + coeffs['b4'] * psal ** 2)

    return doxy_sc * 44.66  # uM -> ml/L


def pHEXT_from_vFET():
    """(Johnson et al. 2016)

    pH_EXT = (V_EXT - k0_EXT - k2_EXT * temp) / S_nernst
             + log(Cl_T)
             + 2*log(Y_HCl)_T
             - log(1 - S_T/K_S)
             - log((1000 - 1.005 * psal) / 1000))

    S_nernst = (R * T * ln(10)) / F
    F : Faraday Constant
    K_S :
    """



def total_chloride_in_seawater(psal: np.ndarray) -> np.ndarray:
    """(Dickson et al. 2007)

    Cl_T = (0.99889/35.453)*(psal/1.80655)*(1000/(1000-1.005*psal))

    Parameters
    ----------
    psal :
        practical salinity

    Notes
    -----
        Dickson et al. 2007, IOCCP Report No.8, Guide to Best Practices for Ocean CO2 Measurements
    """
    return (0.99889 / 35.453) * (psal / 1.80655) * (1000 / (1000 - 1.005 * psal))


def sample_ionic_strength(psal: np.ndarray) -> np.ndarray:
    """(Dickson et al. 2007)

    I = (19.924*psal)/(1000-1.005*psal)

    Parameters
    ----------
    psal :
        practical salinity

    Notes
    -----
        Dickson et al. 2007, IOCCP Report No.8, Guide to Best Practices for Ocean CO2 Measurements
    """
    return (19.924 * psal) / (1000 - 1.005 * psal)


def debye_huckel_HCl_activity_constant(temp: np.ndarray) -> np.ndarray:
    """(Khoo et al. 1977)

    A_DH = 0.0000034286 * temp**2 + 0.00067524 * temp + 0.49172143

    Parameters
    ----------
    temp :
        temperature in Celsius

    """
    return 0.0000034286 * temp**2 + 0.00067524 * temp + 0.49172143


def total_sulfate_in_seawater(psal: np.ndarray) -> np.ndarray:
    """(Dickson et al. 2007)

    S_T = (0.1400 / 96.062) * (psal / 1.80655)

    Parameters
    ----------
    psal :
        practical salinity

    Notes
    -----
        Dickson et al. 2007, IOCCP Report No.8, Guide to Best Practices for Ocean CO2 Measurements
    """

    return (0.1400 / 96.062) * (psal / 1.80655)


def partial_molal_volume_hcl(temp: np.ndarray)->np.ndarray:
    """(Millero 1983)

    V_HCl = 17.85 + 0.1044 * temp - 0.001316 * temp**2

    Parameters
    ----------
    temp :
        temperature in Celsius

    """
    return 17.85 + 0.1044 * temp - 0.001316 * temp**2


def acid_dissociation_constant_HSO4(temp: np.ndarray, psal: np.ndarray) -> np.ndarray:
    """(Dickson et al. 2007)

    K_S = (1 - 0.001005 * psal)*e**Term
    Term = (-4276.1 / T) + 141.328 - 23.093 * ln(T) + sqrt(I) * ((-13856/T) + 324.57 - 47.986*ln(T)) + ....

    Parameters
    ----------
    psal :
        practical salinity
    temp :
        temperature in Celsius


    """


def log_of_HCl_activity_as_temperature_function(psal: np.temp, temp: np.ndarray) -> np.ndarray:
    """(Khoo et al. 1977)

    log(Y_HCl)_T = -(A_DH * sqrt(I))/(1 + 1.394*sqrt(I)) + (0.08885 - 0.000111 * t) * I

    I : sample_ionic_strength
    A_DH : HCl_activity_constant

    Parameters
    ----------
    psal :
        practical salinity
    temp :
        temperature in Celsius


    """
    a_dh = debye_huckel_HCl_activity_constant(temp=temp)
    i = sample_ionic_strength(psal=psal)

    return -(a_dh * np.sqrt(i))/(1 + 1.394 * np.sqrt(i)) + (0.08885 - 0.000111 * temp) * i


def log_of_HCl_activity_as_temperature_and_pressure_function(psal: np.temp,
                                                             temp: np.ndarray,
                                                             pres: np.ndarray) -> np.ndarray:
    """(Khoo et al. 1977)

    log(Y_HCL)_TP = log_t + ((V_HCl * P) / (10 * ln(10) * R * T)) / 2

    log_t : log_of_HCl_activity_as_temperature_function
    V_HCl : partial molal volume of HCl cm**3/mol
    P : pressure in dbar
    R : Gas Constant
    T : 273.15 + temperature

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

    return log_t + ((v_hcl * pres) / (np.log(10) * GAS_CONSTANT * temp * 10)) / 2


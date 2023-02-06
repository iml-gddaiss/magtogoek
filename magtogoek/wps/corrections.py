"""
Correction algorithm for Water Property Sensor (WPS) data.

cal coeff      : c0, c1, c2, d0
pressure coeff : cp
salinity coeff : b0, b1, b2, b3, b4
winkler coeff  : d1, d2


"""
import numpy as np

from magtogoek.wps.sci_tools import voltEXT_from_pHEXT, pHEXT_from_voltEXT

RINKO_COEFFS_KEYS = ('c0', 'c1', 'c2', 'd0', 'cp',
                     'b0', 'b1', 'b2', 'b3', 'b4',
                     'd1', 'd2')


def pH_correction_for_salinity(temperature: np.ndarray,
                               salinity: np.ndarray,
                               ph_temperature: np.ndarray,
                               cal_psal: float, k0: float, k2: float)->np.ndarray:
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


def dissolved_oxygen_rinko_correction(
        doxy: np.ndarray,
        temp: np.ndarray,
        pres: np.ndarray,
        psal: np.ndarray,
        coeffs: dict
) -> np.ndarray:
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

    _doxy = doxy * 44.66  # ml/L -> uM
    _pres = pres / 100  # dbar -> MPa

    doxy_pc = _doxy * (1 + coeffs['cp'] * _pres)

    temp_s = np.log10((298.15 - temp) / (273.15 + temp))

    doxy_sc = doxy_pc * (np.exp(coeffs['b0']
                                + coeffs['b1'] * temp_s
                                + coeffs['b2'] * temp_s ** 2
                                + coeffs['b3'] * temp_s ** 3)
                         + coeffs['b4'] * psal ** 2)

    return doxy_sc * 44.66  # uM -> ml/



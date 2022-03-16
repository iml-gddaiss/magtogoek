"""
Algorithm to process Viking instrument data.

cal coeff      : c0, c1, c2, d0
pressure coeff : cp
salinity coeff : b0, b1, b2, b3, b4
winkler coeff  : d1, d2

"""

import numpy as np
import xarray as xr

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

    temp_s = np.log((298.15 - temp) / (273.15 + temp))

    doxy_sc = doxy_pc * (np.exp(coeffs['b0']
                                + coeffs['b1'] * temp_s
                                + coeffs['b2'] * temp_s ** 2
                                + coeffs['b3'] * temp_s ** 3)
                         + coeffs['b4'] * psal ** 2)

    return doxy_sc * 44.66  # uM -> ml/L


def vFET_from_pHEXT():
    """

    Returns
    -------

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
    """

    Parameters
    ----------
    temp

    Returns
    -------

    """
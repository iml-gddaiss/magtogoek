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
    
    """
    if len({array.shape for array in [doxy, temp, pres, psal]}) != 1:
        raise ValueError('Arrays length mismatch.')

    _doxy = doxy*44.66 # ml/L -> uM
    _pres = pres/100   # dbar -> MPa

    doxy_pc = _doxy * (1 + coeffs['cp'] * _pres)

    temp_s = np.log((298.15 - temp) / (273.15 + temp))

    doxy_sc = doxy_pc * (np.exp(coeffs['b0']
                                + coeffs['b1'] * temp_s
                                + coeffs['b2'] * temp_s**2
                                + coeffs['b3'] * temp_s**3)
                         + coeffs['b4'] * psal**2)

    return doxy_sc * 44.66 # uM -> ml/L


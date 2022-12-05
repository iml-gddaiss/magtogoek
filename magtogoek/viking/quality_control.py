"""

"""

from typing import *
import xarray as xr
from magtogoek.viking.tools import compensation_pres_temp_psal_rinko, voltEXT_from_pHEXT, pHEXT_from_voltEXT

from magtogoek import logger as l


def no_meteoce_quality_control(dataset):
    return dataset


def meteoce_quality_control(
        dataset,
        ph_coeffs: Tuple[float] = None, # (psal, k0, k2)
        oxy_coeffs: Tuple[float] = None
):

    if 'ph' in dataset and ph_coeffs is not None:
        if all( var in dataset for var in ('ph_temperature', 'temperature', 'salinity')):
            _ph_correction(dataset, ph_coeffs)
        else:
            #FIXME replace error by logging.
            raise ValueError

    if 'oxy' in dataset and oxy_coeffs is not None:
        _dissolved_oxygen_compensation(dataset, oxy_coeffs)
        pass

    return dataset


def _ph_correction(dataset, ph_coeffs):
    """

    Parameters
    ----------
    dataset
    ph_coeffs

    Returns
    -------

    """
    [psal, k0, k2] = ph_coeffs
    volt = voltEXT_from_pHEXT(temp=dataset['ph_temperature'], psal=psal, k0=k0, k2=k2)
    ph = pHEXT_from_voltEXT(temp=dataset['temperature'], psal=dataset['salinity'], volt=volt, k0=k0, k2=k2)
    dataset['ph'].values = ph


def _dissolved_oxygen_compensation(dataset: xr.Dataset, coeffs):
    """
    See compensation_pres_temp_psal_rinko

    Parameters
    ----------
    dataset :
        variables needed: (dissolved_oxygen, temperature, pres, salinity)

    """
    dataset['dissolved_oxygen'].values = compensation_pres_temp_psal_rinko(
        doxy=dataset['dissolved_oxygen'],
        temp=dataset['temperature'],
        pres=dataset['pres'],
        psal=dataset['salinity'],
        coeffs=coeffs
    )
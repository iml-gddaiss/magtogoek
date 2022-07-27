"""

"""

from typing import *
import xarray as xr
from magtogoek.viking.tools import compensation_pres_temp_psal_rinko, voltEXT_from_pHEXT, pHEXT_from_voltEXT


def no_meteoce_quality_control(dataset):
    return dataset


def meteoce_quality_control(
        dataset,
        ph_coeff: Tuple[float, float, float] = 0, # (psal, k0, k2)
):

    if 'ph' in dataset and ph_coeff is not None:
        if all( var in dataset for var in ('ph_temperature', 'temperature', 'salinity')):
            dataset = _ph_correction(dataset, ph_coeff)
        else:
            #FIXME replace error by logging.
            raise ValueError

    return dataset


def _ph_correction(dataset, ph_coeff):
    """

    Parameters
    ----------
    dataset
    ph_coeff

    Returns
    -------

    """
    volt = voltEXT_from_pHEXT(temp=dataset['ph_temperature'], psal=ph_coeff[0], k0=ph_coeff[1], k2=ph_coeff[2])
    ph = pHEXT_from_voltEXT(temp=dataset['temperature'], psal=dataset['salinity'], volt=volt, k0=ph_coeff[1], k2=ph_coeff[2])
    dataset['ph'][:] = ph
    return dataset


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
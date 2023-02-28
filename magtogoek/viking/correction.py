"""
Module containing the correction functions for viking data processing.
"""
import xarray as xr
from typing import TYPE_CHECKING

from magtogoek import logger as l
from magtogoek.utils import ensure_list_format
from magtogoek.wps.corrections import pH_correction_for_salinity, dissolved_oxygen_correction_winkler, \
    dissolved_oxygen_correction_for_salinity_SCOR_WG_142, dissolved_oxygen_correction_for_pressure_JAC, \
    time_drift_correction, in_situ_sample_correction


if TYPE_CHECKING:
    from magtogoek.viking.process import ProcessConfig


WPS_VARIABLES_TO_CORRECT = [
    'salinity',
    'temperature',
    'dissolved_oxygen',
    'co2w',
    'ph',
    'fluorescence',
    'chlorophyll',
    'fdom'
]


def meteoce_correction(
        dataset: xr.Dataset,
        pconfig: "ProcessConfig"
):
    """
    Function that calls all the meteoce data corrections.

    Notes
    -----
    pconfig.p01_codes_map values can be modified when certain corrections are carried out.
    """

    if 'dissolved_oxygen' in dataset.variables:
        _dissolved_oxygen_corrections(dataset, pconfig)  # for Winkler recompute with drift corrected temperature ?

    if 'ph' in dataset.variables:
        if pconfig.ph_salinity_correction is True:
            _correct_ph_for_salinity(dataset, pconfig)

    for variable in WPS_VARIABLES_TO_CORRECT:
        if variable in dataset.variables:
            _add_correction_attributes_to_dataarray(dataset[variable])
            if pconfig.__dict__[variable + " _drift"] is not None:
                _time_drift_correction(dataset, variable, pconfig)

            if pconfig.__dict__[variable + " _sample_correction"] is not None:
                _in_situ_sample_correction(dataset, variable, pconfig)


def _dissolved_oxygen_corrections(dataset: xr.Dataset, pconfig: "ProcessConfig"):
    """
    Calls:
            _dissolved_oxygen_winkler_correction

            _dissolved_oxygen_salinity_correction

            _dissolved_oxygen_pressure_correction

    """
    _add_correction_attributes_to_dataarray(dataset['dissolved_oxygen'])
    if pconfig.dissolved_oxygen_winkler_correction:
        _dissolved_oxygen_winkler_correction(dataset, pconfig)
    if pconfig.dissolved_oxygen_salinity_correction:
        _dissolved_oxygen_salinity_correction(dataset)
    if pconfig.dissolved_oxygen_pressure_correction:
        _dissolved_oxygen_pressure_correction(dataset)


def _correct_ph_for_salinity(dataset: xr.Dataset, pconfig: "ProcessConfig"):
    """Ph correction for salinity.

    ph_temperature (temperature is used to find the voltage measured by the probe, but the CTD
    temperature is used to find the ph.

    #Todo Make a test.

    Notes
    -----
    The algorithm used were not tested (As of December 6 2022)
    """
    required_variables = ['ph_temperature', 'temperature', 'salinity']
    if pconfig.ph_coeffs is not None:
        if all((var in dataset for var in required_variables)):
            [psal, k0, k2] = pconfig.ph_coeffs
            ph = pH_correction_for_salinity(temperature=dataset.temperature.data,
                                            salinity=dataset.salinity.data,
                                            ph_temperature=dataset.ph_temperature.data,
                                            cal_psal=psal, k0=k0, k2=k2)
            dataset['ph'].values = ph
            l.log('pH correction was carried out')
        else:
            l.warning(f'pH correction aborted. One of more variables in {required_variables} was missing.')
    else:
        l.warning(f'pH correction aborted. `ph_coeffs` were not provided.')


def _dissolved_oxygen_winkler_correction(dataset: xr.Dataset, pconfig: "ProcessConfig"):
    """
    If the correction can be made, the p01_code_map for dissolved_oxygen is updated.
    """
    if all(var in dataset.variables for var in ['temperature']):
        if len(pconfig.rinko_coeffs) == 6:
            if len(pconfig.winkler_coeffs) == 2:
                dissolved_oxygen_correction_winkler(
                    dataset['dissolved_oxygen'], coeffs=pconfig.rinko_coeffs, winkler_coeffs=pconfig.winkler_coeffs
                )
                pconfig.p01_codes_map['dissolved_oxygen'] = "DOXYCZ01"
                dataset['dissolved_oxygen'].attrs["corrections"].append('Winkler correction carried out.')
            else:
                l.warning(
                    f'Winkler dissolved oxygen correction aborted. Wrong number of winkler coefficient. Expected 2.')
        else:
            l.warning(
                f'Winkler dissolved oxygen correction aborted. Wrong number of rinko coefficient. Expected 6.')
    else:
        l.warning(
            f'Winkler dissolved oxygen correction aborted. Temperature data missing.')


def _dissolved_oxygen_salinity_correction(dataset: xr.Dataset):
    if all(var in dataset.variables for var in ['temperature', 'salinity']):
        dataset.dissolved_oxygen.values = dissolved_oxygen_correction_for_salinity_SCOR_WG_142(
            dissolved_oxygen=dataset.dissolbed_oxygen.data,
            temperature=dataset.temperature.data,
            salinity=dataset.salinity.data
        )
        l.log(f'Dissolved oxygen correction for salinity was carried out')
        dataset['dissolved_oxygen'].attrs["corrections"].append('Salinity correction carried out.')
    else:
        l.warning(f'Dissolved oxygen correction for salinity aborted. `temperature` and/or `salinity` not found.')


def _dissolved_oxygen_pressure_correction(dataset: xr.Dataset):
    if all(var in dataset.variables for var in ['atm_pressure']):
        dataset.dissolved_oxygen.values = dissolved_oxygen_correction_for_pressure_JAC(
                dissolved_oxygen=dataset.dissolved_oxygen.data,
                pressure=dataset.atm_pressure.pint.quantify().to('dbar').data
            )
        l.log(f'Dissolved oxygen correction for pressure was carried out')
        dataset['dissolved_oxygen'].attrs["corrections"].append('Pressure correction carried out.')
    else:
        l.warning(f'Dissolved oxygen correction for pressure aborted. `atm_pressure` ot found.')


def _add_correction_attributes_to_dataarray(dataarray: xr.DataArray):
    """Add corrections (list) attributes to dataarray if it does not exist.

    If it does exist, it makes sure it is a list.
    """
    attr_name = "corrections"
    if attr_name not in dataarray.attrs:
        dataarray.attrs[attr_name] = []
    else:
        dataarray.attrs[attr_name] = ensure_list_format(dataarray.attrs[attr_name])


def _time_drift_correction(dataset: xr.Dataset, variable: str, pconfig: "ProcessConfig"):
    """
    """
    try:
        dataset[variable].data = time_drift_correction(
            data=dataset[variable].data,
            data_time=dataset.time.data,
            drift=pconfig.__dict__[variable + " _drift"],
            drift_time=pconfig.__dict__[variable + " _drift_time"]
        )
        l.log(f'Time drift correction applied to {variable}.')
    except ValueError as msg:
        l.warning(f'Time drift correction for {variable} failed. Error: {msg}.')



def _in_situ_sample_correction(dataset: xr.Dataset, variable: str, pconfig: "ProcessConfig"):
    """
    """
    slope = pconfig.__dict__[variable + " _sample_correction"][0]
    offset = pconfig.__dict__[variable + " _sample_correction"][1]
    dataset[variable].data = in_situ_sample_correction(
        data=dataset[variable].data,
        slope=slope,
        offset=offset
    )
    l.log(f'In situ sample correction applied to {variable}. Slope: {slope}, Offset: {offset}.')

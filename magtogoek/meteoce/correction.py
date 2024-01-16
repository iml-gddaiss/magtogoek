"""
Date: February 2023
Made by jeromejguay

Module containing the correction functions for meteoce data processing.
"""
import xarray as xr
from typing import TYPE_CHECKING

from magtogoek import logger as l
from magtogoek.process_common import add_correction_attributes_to_dataarray
from magtogoek.sci_tools import rotate_heading, cartesian2north_polar, north_polar2cartesian
from magtogoek.wps.correction import pH_correction_for_salinity, dissolved_oxygen_correction_winkler, \
    dissolved_oxygen_correction_for_salinity_SCOR_WG_142, dissolved_oxygen_correction_for_pressure_JAC, \
    time_drift_correction, in_situ_sample_correction

if TYPE_CHECKING:
    from magtogoek.meteoce.process import ProcessConfig

WPS_VARIABLES_TO_CORRECT_FOR_DRIFT_AND_IN_SITU = [
    'salinity',
    'temperature',
    'dissolved_oxygen',
    'co2w',
    'ph',
    'fluorescence',
    'chlorophyll',
    'fdom'
]


def meteoce_data_magnetic_declination_correction(dataset: xr.Dataset, pconfig: "ProcessConfig"):
    """Carry magnetic declination correction for meteoce variables

    [-180, 180]: heading
    [0, 360 ]: mean_wind_direction, wave_direction

    """

    if pconfig.magnetic_declination is not None:
        # '-180, 180'
        if 'heading' in dataset.variables:
            add_correction_attributes_to_dataarray(dataset['heading'])
            dataset.heading.values = rotate_heading(dataset.heading.data, dataset.magnetic_declination)
            dataset['heading'].attrs['corrections'] += 'Corrected for magnetic declination.\n'
            l.log(f"Heading transformed to true north.")

        # '0, 360'
        for variable in {'mean_wind_direction', 'wave_direction'}.intersection(set(dataset.variables)):
            add_correction_attributes_to_dataarray(dataset[variable])
            dataset[variable].values = (dataset[variable].values + pconfig.magnetic_declination) % 360
            dataset[variable].attrs['corrections'] += 'Corrected for magnetic declination.\n'
            l.log(f"{variable} transformed to true north.")


def wps_data_correction(
        dataset: xr.Dataset,
        pconfig: "ProcessConfig"
):
    """
    Function that calls all the wps data corrections.

    pconfig.p01_codes_map values can be modified when certain corrections are carried out.

    Notes
    -----
    Could be moved to magtogoek.wps in the future.
    """

    if 'dissolved_oxygen' in dataset.variables:
        _dissolved_oxygen_corrections(dataset, pconfig)  # for Winkler recompute with drift corrected temperature ?

    if 'ph' in dataset.variables:
        if pconfig.ph_salinity_correction is True:
            _correct_ph_for_salinity(dataset, pconfig)

    for variable in set(WPS_VARIABLES_TO_CORRECT_FOR_DRIFT_AND_IN_SITU).intersection(set(dataset.variables)):
        add_correction_attributes_to_dataarray(dataset[variable])
        if pconfig.__getattribute__(variable + "_drift") is not None:
            _time_drift_correction(dataset, variable, pconfig)

        if pconfig.__getattribute__(variable + "_sample_correction") is not None:
            _in_situ_sample_correction(dataset, variable, pconfig)


def _dissolved_oxygen_corrections(dataset: xr.Dataset, pconfig: "ProcessConfig"):
    """
    Calls:
            _dissolved_oxygen_winkler_correction

            _dissolved_oxygen_salinity_correction

            _dissolved_oxygen_pressure_correction

    """
    add_correction_attributes_to_dataarray(dataset['dissolved_oxygen'])
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
    add_correction_attributes_to_dataarray(dataset['ph'])
    required_variables = ['ph_temperature', 'temperature', 'salinity']
    if pconfig.ph_salinity_coeffs is not None:
        if all((var in dataset for var in required_variables)):
            [psal, k0, k2] = pconfig.ph_salinity_coeffs
            ph = pH_correction_for_salinity(temperature=dataset.temperature.data,
                                            salinity=dataset.salinity.data,
                                            ph_temperature=dataset.ph_temperature.data,
                                            cal_psal=psal, k0=k0, k2=k2)
            dataset['ph'].values = ph
            dataset['ph'].attrs['corrections'] += 'ph values corrected using in-situ salinity.\n'
            l.log('pH correction for in-sity salinity was carried out')
        else:
            l.warning(f'pH correction aborted. One of more variables in {required_variables} was missing.')
    else:
        l.warning(f'pH correction aborted. `ph_coeffs` were not provided.')


def _dissolved_oxygen_winkler_correction(dataset: xr.Dataset, pconfig: "ProcessConfig"):
    """
    If the correction can be made, the p01_code_map for dissolved_oxygen is updated.
    """
    if all(var in dataset.variables for var in ['temperature']):
        if len(pconfig.dissolved_oxygen_rinko_coeffs) == 6:
            if len(pconfig.dissolved_oxygen_winkler_coeffs) == 2:
                dissolved_oxygen_correction_winkler(
                    dataset['dissolved_oxygen'].data, dataset['temperature'].data,
                    rinko_coeffs=pconfig.dissolved_oxygen_rinko_coeffs, winkler_coeffs=pconfig.dissolved_oxygen_winkler_coeffs
                )
                pconfig.p01_codes_map['dissolved_oxygen'] = "DOXYCZ01"
                dataset['dissolved_oxygen'].attrs["corrections"] += 'Winkler correction carried out.\n'
            else:
                l.warning(
                    f'Winkler dissolved oxygen correction aborted. Wrong number of Winkler coefficient. Expected 2.')
        else:
            l.warning(
                f'Winkler dissolved oxygen correction aborted. Wrong number of Rinko coefficient. Expected 6.')
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
        dataset['dissolved_oxygen'].attrs["corrections"] += 'Salinity correction carried out.\n'
    else:
        l.warning(f'Dissolved oxygen correction for salinity aborted. `temperature` and/or `salinity` not found.')


def _dissolved_oxygen_pressure_correction(dataset: xr.Dataset):
    """Apply `magtogoek.wps.correction.dissolved_oxygen_correction_for_pressure_JAC`

    """
    if all(var in dataset.variables for var in ['pres']):
        dataset.dissolved_oxygen.values = dissolved_oxygen_correction_for_pressure_JAC(
            dissolved_oxygen=dataset.dissolved_oxygen.values,
            pressure=dataset['pres'].values
        )
        l.log(f'Dissolved oxygen correction for pressure was carried out')
        dataset['dissolved_oxygen'].attrs["corrections"] += 'Pressure correction carried out.\n'
    else:
        l.warning(f'Dissolved oxygen correction for pressure aborted. `pres` missing.')


def _time_drift_correction(dataset: xr.Dataset, variable: str, pconfig: "ProcessConfig"):
    """Apply `magtogoek.wps.correction.time_drift_correction`
    """
    try:
        dataset[variable].data = time_drift_correction(
            data=dataset[variable].values,
            data_time=dataset.time.values,
            drift=pconfig.__dict__[variable + "_drift"],
            drift_time=pconfig.__dict__[variable + "_drift_time"]
        )
        l.log(f'Time drift correction applied to {variable}.')
        dataset[variable].attrs['corrections'] += "Correction applied for sensor drift.\n"
    except ValueError as msg:
        l.warning(f'Time drift correction for {variable} failed. Error: {msg}.')


def _in_situ_sample_correction(dataset: xr.Dataset, variable: str, pconfig: "ProcessConfig"):
    """Apply `magtogoek.wps.correction.in_situ_sample_correction`
    """
    slope = pconfig.__dict__[variable + "_sample_correction"][0]
    offset = pconfig.__dict__[variable + "_sample_correction"][1]
    dataset[variable].data = in_situ_sample_correction(
        data=dataset[variable].values,
        slope=slope,
        offset=offset
    )
    dataset[variable].attrs['corrections'] += "Correction applied with in-situ sample.\n"
    l.log(f'In situ sample correction applied to {variable}. Slope: {slope}, Offset: {offset}.')

"""
Date: February 2023
Made by jeromejguay

Module that contains function for meteoce data quality control.


Notes
-----
    + Absolute outliers get a flag of 4


   Tests return `True` where cells fail a test.

   SeaDataNet Quality Control Flags Value
   * 0: no_quality_control
   * 1: good_value
   * 2: probably_good_value
   * 3: probably_bad_value
       - Unusual data value, inconsistent with real phenomena.
   * 4: bad_value
       - Obviously erroneous data value.
   * 5: changed_value
   * 6: value_below_detection
   * 7: value_in_excess
   * 8: interpolated_value
   * 9: missing_value


"""
import numpy as np
import xarray as xr
from typing import List

from magtogoek import logger as l
from magtogoek.quality_control_common import IMPOSSIBLE_PARAMETERS_VALUES, values_outliers_detection, \
    add_ancillary_QC_variable_to_dataset, add_flags_values, merge_flags, \
    find_missing_values
from magtogoek.process_common import FLAG_ATTRIBUTES


VARIABLES_WITH_QC = { # 1: QC(default flag = 1) , 0: No Qc (default flag = 0)
    "wind_speed":0,
    "wind_direction":0,
    "wind_gust":0,
    'atm_temperature': 1,
    'atm_humidity': 1,
    'atm_pressure': 1,
    'wave_mean_height': 0,
    'wave_maximal_height': 0,
    'wave_period': 0,
    'wave_direction': 0,
    'temperature': 1,
    'conductivity': 0,
    'salinity': 1,
    'density': 1,
    'dissolved_oxygen': 1,
    'ph': 1,
    'par': 0,
    'scattering': 0,
    'chlorophyll': 0,
    'fdom': 0,
    'co2_a': 0,
    'co2_w': 0
    }

QC_VARIABLES = [k for k, v in VARIABLES_WITH_QC.items() if v == 1]


NO_QC_VARIABLES = [k for k, v in VARIABLES_WITH_QC.items() if v == 0]


def no_meteoce_quality_control(dataset: xr.Dataset):
    """
    Notes
    -----
        SeaDataNet Quality Control Flags Value
        * 0: no_quality_control
    """
    l.section("Meteoce Quality Control")

    l.log("No quality control carried out")

    _add_ancillary_variables_to_dataset(dataset, variables=list(dataset.keys()), default_flag=0)

    dataset.attrs.update(FLAG_ATTRIBUTES)
    dataset.attrs["quality_comments"] = "No quality control."


def meteoce_quality_control(
        dataset: xr.Dataset,

        regional_outlier: str = None,
        absolute_outlier: bool = True,
        propagate_flags: bool = True,
):
    """

    Flag propagation:

    Pressure -> Depth |
    Depth, Temperature, Salinity -> Density
    Pressure, Temperature, Salinity -> Dissolved Oxygen
    Temperature, Salinity -> pH


    Parameters
    ----------
    dataset

    regional_outlier
    absolute_outlier

    propagate_flags


    Notes
    -----
       Tests return `True` where cells fail a test.

       SeaDataNet Quality Control Flags Value
       * 0: no_quality_control
       * 1: good_value
       * 2: probably_good_value
       * 3: probably_bad_value
           - Unusual data value, inconsistent with real phenomena.
       * 4: bad_value
           - Obviously erroneous data value.
       * 5: changed_value
       * 6: value_below_detection
       * 7: value_in_excess
       * 8: interpolated_value
       * 9: missing_value


    """
    l.section("Meteoce Quality Control")

    _add_ancillary_variables_to_dataset(dataset, variables=QC_VARIABLES, default_flag=1)
    _add_ancillary_variables_to_dataset(dataset, variables=NO_QC_VARIABLES, default_flag=0)

    if regional_outlier is not None:
        if regional_outlier in IMPOSSIBLE_PARAMETERS_VALUES:
            _impossible_values_tests(dataset, region=regional_outlier, flag=3)
        else:
            l.warning(f'Region {regional_outlier} not found in the impossible parameters values file {IMPOSSIBLE_PARAMETERS_VALUES}')

    if absolute_outlier is True:
        _impossible_values_tests(dataset, region='global', flag=4)

    _flag_missing_values(dataset)

    if propagate_flags is True:
        _propagate_flag(dataset, use_atm_pressure=True)

    _print_percent_of_good_values(dataset)

    dataset.attrs["quality_comments"] = l.logbook.split("[Meteoce Quality Control]\n")[1]
    dataset.attrs.update(FLAG_ATTRIBUTES)


def _add_ancillary_variables_to_dataset(dataset: xr.Dataset, variables: List[str], default_flag: int = 1):
    for variable in set(dataset.keys()) & set(variables):
        add_ancillary_QC_variable_to_dataset(dataset=dataset, variable=variable, default_flag=default_flag)


def _impossible_values_tests(dataset: xr.Dataset, region: str, flag: int):
    """
    Iterates over the values in impossible_parameter_values.json for the region.
    """
    outliers_values = IMPOSSIBLE_PARAMETERS_VALUES[region]

    for variable in set(dataset.keys()) & set(outliers_values.keys()) & set(QC_VARIABLES):
        _data = dataset[variable].values

        if 'units' in dataset[variable].attrs:
            if dataset[variable].attrs['units'] != outliers_values[variable]['units']:
                _data = dataset[variable].pint.quantify().pint.to(
                    outliers_values[variable]['units']
                ).pint.dequantify().values
        else:
            l.warning(f"(outlier test, region: {region}) Could not verify units for {variable} due missing units on loaded variable.")

        outliers_flag = values_outliers_detection(
            _data,
            lower_limit=outliers_values[variable]['min'],
            upper_limit=outliers_values[variable]['max']
        )
        add_flags_values(dataset[variable + "_QC"].values, outliers_flag * flag)

        test_comment = \
            f"{region} outlier threshold: less than {outliers_values[variable]['min']} {outliers_values[variable]['units']} " \
            f"and greater than {outliers_values[variable]['max']} {outliers_values[variable]['units']} (flag={flag})."

        l.log(f"{variable} :" + test_comment)

        dataset[variable+"_QC"].attrs['quality_test'] += test_comment + "\n"


def _flag_missing_values(dataset: xr.Dataset):
    """Flag missing values for all meteoce variables."""
    for variable in set(dataset.variables).intersection(set(VARIABLES_WITH_QC.keys())):
        add_flags_values(dataset[variable + "_QC"].data, find_missing_values(dataset[variable].values) * 9)


def _propagate_flag(dataset: xr.Dataset, use_atm_pressure: bool = False):
    """ Maybe move to wps

    Parameters
    ----------
    dataset :

    use_atm_pressure :
        if True, atm_pressure flag will be used instead of pres for propagation. (surface data).

    Pressure -> Depth
    Depth, Temperature, Salinity -> Density
    Pressure, Temperature, Salinity -> Dissolved Oxygen
    Temperature, Salinity -> pH
    """

    flag_propagation_rules = {
        'density': ['temperature', 'salinity', 'density'],
        'dissolved_oxygen': ['temperature', 'salinity', 'dissolved_oxygen'],
        'ph': ['temperature', 'salinity', 'ph'],
        }

    if use_atm_pressure is True:
        flag_propagation_rules['density'].append('atm_pressure')
        flag_propagation_rules['dissolved_oxygen'].append('atm_pressure')

    for variable in set(dataset.keys()).intersection(set(flag_propagation_rules.keys())):
        flags_parameters = [
            dataset[_var + '_QC'].data for _var in flag_propagation_rules[variable]
        ]

        dataset[variable + "_QC"].data = merge_flags(flags_arrays=flags_parameters)

        propagation_comment = f'Flags propagation {flag_propagation_rules[variable]} -> {variable}.'

        l.log(propagation_comment)

        dataset[variable + "_QC"].attrs['quality_test'] += propagation_comment + "\n"


def _print_percent_of_good_values(dataset: xr.Dataset):
    """Only check for variables in QC_VARIABLES"""
    for variable in set(dataset.keys()).intersection(set(QC_VARIABLES)):
        if "_QC" in variable:
            percent_of_good_values = np.sum(dataset[variable + "_QC"] <= 2) / len(dataset.time)
            l.log(f"{round(percent_of_good_values * 100, 2)}% of {variable.strip('_QC')} have flags of 1 or 2.")

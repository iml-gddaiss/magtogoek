"""
Module that contains function for viking data quality control.


Tests Flags
-----------

Notes
-----
    + Spike return a flag of 3
    + Climatology outliers get a flag of 3
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
from typing import *
import numpy as np
from pandas import Timestamp
import xarray as xr
from magtogoek import logger as l, FLAG_VALUES, FLAG_MEANINGS, FLAG_REFERENCE, \
    GLOBAL_IMPOSSIBLE_PARAMETERS, SPIKE_DETECTION_PARAMETERS
from magtogoek.tools import outlier_values_test, climatology_outlier_test
from magtogoek.wps.quality_control import spike_detection

QC_VARIABLES = [
    'atm_pressure',  # Need since atm_pressure is used for correction Dissolved Oxygen or compute Density
    'temperature',
    'salinity',
    'density',
    'dissolved_oxygen',
    'ph',
    'par',
    'fluorescence',
    'chlorophyll',
    'fdom',
    'co2_w',
]


def no_meteoce_quality_control(dataset: xr.Dataset):
    """
    Notes
    -----
        SeaDataNet Quality Control Flags Value
        * 0: no_quality_control
    """
    l.section("Meteoce Quality Control")

    l.log("No quality control carried out")

    _add_ancillary_variables_to_dataset(dataset, default_flag=0)

    dataset.attrs["flags_reference"] = FLAG_REFERENCE
    dataset.attrs["flags_values"] = FLAG_VALUES
    dataset.attrs["flags_meanings"] = FLAG_MEANINGS
    dataset.attrs["quality_comments"] = "No quality control."


def meteoce_quality_control(
        dataset: xr.Dataset,

        climatology_variables: List[str] = None,
        climatology_dataset: xr.Dataset = None,
        climatology_threshold: float = None,
        climatology_depth_interpolation_method: str = None,

):
    """

    Flag propagation:

    Pressure -> Depth
    Depth, Temperature, Salinity -> Density
    Pressure, Temperature, Salinity -> Dissolved Oxygen
    Temperature, Salinity -> pH


    Parameters
    ----------
    dataset

    climatology_variables
    climatology_dataset
    climatology_threshold
    climatology_depth_interpolation_method


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


    Todos
    -----
    + spike detection
    + absolute limit detection
    + Flag propagation
    + Flag Comments attrs.

    """
    l.section("Meteoce Quality Control")

    l.warning('QUALITY CONTROL IN DEVELOPMENT')

    _add_ancillary_variables_to_dataset(dataset)

    _spike_detection_tests(dataset)

    if climatology_variables is not None:
        for variables in climatology_variables:
            _climatology_outlier_tests(
                dataset=dataset,
                climatology_dataset=climatology_dataset,
                variables=variables,
                threshold=climatology_threshold,
                depth_interpolation_method=climatology_depth_interpolation_method
            )

    _absolute_outlier_tests(dataset)

    _flag_propagation(dataset)

    _print_percent_of_good_values(dataset)

    dataset.attrs["quality_comments"] = l.logbook.split("[Meteoce Quality Control]\n")[1]
    dataset.attrs["flags_reference"] = FLAG_REFERENCE
    dataset.attrs["flags_values"] = FLAG_VALUES
    dataset.attrs["flags_meanings"] = FLAG_MEANINGS


def _add_ancillary_variables_to_dataset(dataset: xr.Dataset, default_flag: int = 1):
    for variable in QC_VARIABLES:
        if variable in dataset.variables:
            dataset[variable + "_QC"] = (
                ['time'], np.ones(dataset.time.shape).astype(int) * default_flag,
                {
                    'quality_test': "",
                    "quality_date": Timestamp.now().strftime("%Y-%m-%d"),
                    "flag_meanings": FLAG_MEANINGS,
                    "flag_values": FLAG_VALUES,
                    "flag_reference": FLAG_REFERENCE
                }
            )


def _climatology_outlier_tests(
        dataset: xr.Dataset,
        climatology_dataset: xr.Dataset,
        variables: str,
        threshold: float,
        depth_interpolation_method: str,
):
    for variable in variables:
        try:
            outliers_flag = climatology_outlier_test(
                dataset=dataset,
                climatology_dataset=climatology_dataset,
                variable=variable,
                threshold=threshold,
                depth_interpolation_method=depth_interpolation_method
            )
            dataset[variable + "_QC"][outliers_flag] = 3

            test_comment = f"Climatology outlier test. (flag=3)"
            l.log(f"{variable}" + test_comment)
            dataset[variable + "_QC"].attrs['quality_test'].append(test_comment + "\n")

        except ValueError as msg:
            l.warning(f'Unable to carry out climatology outlier qc on {variable}.\n\t Error: {msg}')
    pass


def _absolute_outlier_tests(dataset: xr.Dataset):
    """
    Iterates over GLOBAL_IMPOSSIBLE_PARAMETERS (in magtogoek/__init__) for min and max absolute values.

    """
    for variable in set(dataset.variables).intersection(set(GLOBAL_IMPOSSIBLE_PARAMETERS.keys())):
        outliers_flag = outlier_values_test(
            dataset[variable].data,
            lower_limit=GLOBAL_IMPOSSIBLE_PARAMETERS[variable]['min'],
            upper_limit=GLOBAL_IMPOSSIBLE_PARAMETERS[variable]['max']
        )
        dataset[variable + "_QC"][outliers_flag] = 4

        test_comment = \
            f"Absolute outlier threshold: less than {GLOBAL_IMPOSSIBLE_PARAMETERS[variable]['min']} {GLOBAL_IMPOSSIBLE_PARAMETERS[variable]['units']} " \
            f"and greater than {GLOBAL_IMPOSSIBLE_PARAMETERS[variable]['max']} {GLOBAL_IMPOSSIBLE_PARAMETERS[variable]['units']} (flag=4)."

        l.log(f"{variable} :" + test_comment)
        dataset[variable+"_QC"].attrs['quality_test'].append(test_comment + "\n")


def _spike_detection_tests(dataset: xr.Dataset):
    """
    Iterates over SPIKE_DETECTION (in magtogoek/__init__) for inner and outer absolute values.
    """
    for variable in set(dataset.variables).intersection(set(SPIKE_DETECTION_PARAMETERS.keys())):
        spikes_flag = spike_detection(
            dataset[variable].data,
            inner=SPIKE_DETECTION_PARAMETERS[variable]['inner'],
            outer=SPIKE_DETECTION_PARAMETERS[variable]['outer']
        )
        dataset[variable + "_QC"][spikes_flag] = 3

        test_comment = \
            f"Spike detection inner threshold {SPIKE_DETECTION_PARAMETERS[variable]['inner']} {SPIKE_DETECTION_PARAMETERS[variable]['units']} " \
            f"and outer threshold {SPIKE_DETECTION_PARAMETERS[variable]['outer']} {SPIKE_DETECTION_PARAMETERS[variable]['units']} (flag=3)"

        l.log(f"{variable} :" + test_comment)
        dataset[variable+"_QC"].attrs['quality_test'].append(test_comment + "\n")


def _flag_propagation(dataset: xr.Dataset):
    """ Maybe move to wps
    Pressure -> Depth
    Depth, Temperature, Salinity -> Density
    Pressure, Temperature, Salinity -> Dissolved Oxygen
    Temperature, Salinity -> pH
    """
    flag_propagation_rules = {
        'depth': ['pres'],
        'density': ['pres', 'temperature', 'salinity'],
        'dissolved_oxygen': ['pres', 'temperature', 'salinity'],
        'ph': ['temperature', 'salinity'],
        }
    for variable in set(dataset.variables).intersection(set(flag_propagation_rules.keys())):
        _flags = flag_propagation_rules[variable] + [variable]
        dataset[variable+"_QC"] = np.stack([dataset[v+'_QC'].data for v in _flags], axis=-1).max(axis=-1)
        propagation_comment = f'Flags propagation {flag_propagation_rules[variable]} -> {variable}.\n'
        l.log(propagation_comment)
        dataset[variable].attrs['quality_test'].append(propagation_comment)


def _print_percent_of_good_values(dataset: xr.Dataset):
    for variable in dataset.variables:
        if "_QC" in variable:
            percent_of_good_values = np.sum(dataset.variables <= 2) / len(dataset.time)
            l.log(f"{round(percent_of_good_values * 100, 2)}% of {variable.strip('_QC')} have flags of 1 or 2.")


if __name__ == "__main__":
    import xarray as xr

    # CLIMATOLOGY COMPARISON TEST #
    path = '/home/jeromejguay/WorkSpace/Data/Sillex2018/Raw/FreshWater/'
    # data_path = path + 'discharge1944_2019.nc'
    # clim_path = path + 'discharge1994_2019_clim.nc'

    data_2d_path = path + 'test_2d_data.nc'
    clim_2d_path = path + 'test_2d_clim.nc'

    ds = xr.open_dataset(data_2d_path)
    clim_ds = xr.open_dataset(clim_2d_path)

    _variable = 'discharge'
    _threshold = 1

    outlier = climatology_outlier_test(
        dataset=ds,
        climatology_dataset=clim_ds,
        variable=_variable,
        threshold=_threshold,
        depth_interpolation_method='linear'
    )
    outlier.plot()



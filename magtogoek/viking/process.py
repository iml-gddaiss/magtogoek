"""
This script has to functions to process and quick process viking buoy data.
These functions are called by the app command `process` and `quick viking`.

Date: July 25 2022
Made by: jeromejguay

Notes
-----
Missing BODC: oxy

At the moment for some data correction. If the variable used has nans, the corrected value will (should) be a nan as well.
Therefore, if a variable is present but all the values are nan, the corrected data will also be all nan.

Maybe quality control should be done before and the transformation should check the flag values.

"""

import pint_xarray as px
import xarray as xr
from typing import *

from magtogoek import logger as l
from magtogoek.process_common import BaseProcessConfig, resolve_output_paths, add_global_attributes, write_log, write_netcdf, \
    add_processing_timestamp, clean_dataset_for_nc_output, format_data_encoding, add_navigation, save_variables_name_for_odf_output
from magtogoek.attributes_formatter import format_variables_names_and_attributes
from magtogoek.wps.corrections import pH_correction_for_salinity, dissolved_oxygen_correction_for_salinity_SCOR_WG_142, dissolved_oxygen_correction_for_pressure_JAC
from magtogoek.wps.sci_tools import compute_density, dissolved_oxygen_ml_per_L_to_umol_per_L, dissolved_oxygen_umol_per_L_to_umol_per_kg
from magtogoek.sci_tools import north_polar2cartesian
from magtogoek.viking.loader import load_meteoce_data
from magtogoek.viking.quality_control import meteoce_quality_control, no_meteoce_quality_control

# import click

l.get_logger("viking_processing")

STANDARD_GLOBAL_ATTRIBUTES = {"process": "viking_buoy", "featureType": "timeSeriesProfile"}

VARIABLES_TO_DROP = ['ph_temperature', 'wind_direction_max', 'speed', 'course', 'magnetic_declination']

GLOBAL_ATTRS_TO_DROP = [
    #"sensor_type",
    "process",
    "platform_type",
    "VAR_TO_ADD_SENSOR_TYPE",
    "P01_CODES",
    "xducer_depth",
    "variables_gen_name",
    "binary_mask_tests",
    "binary_mask_tests_values",
    "bodc_name"
]


P01_CODES_MAP = {
    'time': "ELTMEP01",
    'wind_mean': "EWSBZZ01",
    'wind_max': "EWDAZZ01",
    'wind_direction_mean': "EGTSZZ01",
    'atm_temperature': "CTMPZZ01",
    'atm_humidity': "CRELZZ01",
    'atm_pressure': "CAPHZZ01",
    'temperature': "TEMPPR01",
    'conductivity': "CNDCZZ01",
    'salinity': "PSLTZZ01",
    'density': "SIGTEQ01",
    'ph': "PHXXZZXX",
    'fluorescence': "FLUOZZZZ",
    'chlorophyll': "CPHLPR01",
    'fdom': "CCOMD002",
    'co2_a': "ACO2XXXX",
    'co2_w': "PCO2XXXX",
    'wave_mean_height': "GAVHZZ01",
    'wave_maximal_height': "GCMXZZ01",
    'wave_period': "GTAMZZ01",
    'par': "PFDPAR01",
    'u': "LCEWAP01",
    'v': "LCNSAP01",
    'w': "LRZAAP01",
    'e': "LERRAP01",
    'u_QC': "LCEWAP01_QC",
    'v_QC': "LCNSAP01_QC",
    'w_QC': "LRZAAP01_QC",
    'pg': "PCGDAP01",
    'pg1': "PCGDAP00",
    'pg2': "PCGDAP02",
    'pg3': "PCGDAP03",
    'pg4': "PCGDAP04",
    'corr1': "CMAGZZ01",
    'corr2': "CMAGZZ02",
    'corr3': "CMAGZZ03",
    'corr4': "CMAGZZ04",
    'amp1': "TNIHCE01",
    'amp2': "TNIHCE02",
    'amp3': "TNIHCE03",
    'amp4': "TNIHCE04",
    'bt_u': "APEWBT01",
    'bt_v': "APNSBT01",
    'bt_w': "LRZABT01",
    'bt_e': "LERRBT01",
    'lon': "ALONZZ01",
    'lat': "ALATZZ01",
    'heading': "HEADCM01",
    'roll_': "ROLLGP01",
    'pitch': "PTCHGP01",
    'u_ship': "APEWGP01",
    'v_ship': "APNSGP01"
}

SENSOR_TYPE_TO_SENSORS_ID_MAP = {
    'adcp': [
        "u", "v", "w", "e", "bt_u", "bt_v", "bt_w", "bt_e",
        'pg', 'pg1', 'pg2', 'pg3', 'pg4',
        'corr1', 'corr2', 'corr3', 'corr4',
        'amp1', 'amp2', 'amp3', 'amp4'
    ],
    "ctd": ["conductivity", "salinity", "temperature", "density"],
    "ctdo": ["conductivity", "salinity", "temperature", "density", "dissolved_oxygen"],
    "doxy": ["dissolved_oxygen"],
    # 'nitrate': [],  # Not implemented yet.
    "ph": ['ph'],
    'par': ['par'],
    'triplet': ['fluorescence', 'chlorophyll', 'fdom'],
    'co2w': ['co2_w'],
    'co2a': ['co2_a'],
    'wave': ['wave_mean_height', 'wave_maximal_height', 'wave_period'],
    'wind': ['wind_mean', 'wind_max', 'wind_direction_mean', 'wind_direction_max'],
    'meteo': ['atm_temperature', 'atm_humidity', 'atm_pressure']
}


class ProcessConfig(BaseProcessConfig):
    # PROCESSING
    buoy_name: str = None
    data_format: str = None
    sensor_depth: float = None
    wind_sensor: str = None # wmt700 or wxt520

    adcp_id: str = None
    ctd_id: str = None
    ctdo_id: str = None
    nitrate_id: str = None
    # ADD MORE


    # CTD
    compute_density: bool = None
    # PH
    ph_correction: bool = None
    ph_coeffs: Tuple[float] = None  # psal, k0, k2
    # OXY
    d_oxy_correction: bool = None
    #winkler ?

    # ADCP
    motion_correction_mode: str = None # maybe adcp/process/adcp_processing...c

    # QUALITY_CONTROL  ... adcp ...
    quality_control: bool = None

    def __init__(self, config_dict: dict = None):
        super().__init__(config_dict)
        self.sensors_id = SENSOR_TYPE_TO_SENSORS_ID_MAP
        self.variables_to_drop = VARIABLES_TO_DROP
        self.global_attributes_to_drop = GLOBAL_ATTRS_TO_DROP


def process_viking(config: dict, drop_empty_attrs: bool = False, headless: bool = False):
    """Process Viking data with parameters from a config file.

    call process_common.process

    Parameters
    ----------
    config :
        Dictionary make from a configfile (see config_handler.load_config).
    drop_empty_attrs :
        If true, all netcdf empty ('') global attributes will be dropped from
        the output.
    headless :
        If true, figures are not displayed.

    The actual data processing is carried out by _process_viking_data.
    """
    pconfig = ProcessConfig(config)
    pconfig.drop_empty_attrs = drop_empty_attrs
    pconfig.headless = headless

    _process_viking_data(pconfig)


@resolve_output_paths
def _process_viking_data(pconfig: ProcessConfig):
    """

    """

    # ------------------- #
    # LOADING VIKING DATA #
    # ------------------- #

    dataset = _load_viking_data(pconfig)

    # ----------------------------------------- #
    # ADDING THE NAVIGATION DATA TO THE DATASET #
    # ----------------------------------------- #
    # NOTE: PROBABLY NOT NEED SINCE VIKING DATA have GPS.
    if pconfig.navigation_file:
        l.section("Navigation data")
        dataset = add_navigation(dataset, pconfig.navigation_file)

    # ------- #
    # Compute #
    # ------- #

    l.section("Data Computation")

    if 'density' not in dataset:
        _compute_ctdo_potential_density(dataset)

    if all(x in dataset for x in ('speed', 'course')):
        _compute_uv_ship(dataset)

    if 'dissolved_oxygen' in dataset.variables:
        _dissolved_oxygen_ml_per_L_to_umol_per_L(dataset)
        _dissolved_oxygen_umol_per_L_to_umol_per_kg(dataset)

    # ----------- #
    # CORRECTION  #
    # ----------- #

    l.section("Data Correction")

    if 'dissolved_oxygen' in dataset.variables and pconfig.d_oxy_correction is True:
        # SDN:P01::DOXYAAOP .. uncompensated for salinity and pressure, umol/L
        # SDN:P01::DOXYMMOP .. Salinity compensated maybe
        _dissolved_oxygen_corrections(dataset)

    if 'ph' in dataset:
        _correct_ph_for_salinity(dataset, pconfig)

    # MAGNETIC DECLINATION SHOULD BE ALREADY CORRECTED FOR VIKING

    # --------------- #
    # QUALITY CONTROL #
    # --------------- #

    # TODO

    if pconfig.quality_control:
        _quality_control(dataset, pconfig)

        # For adcp quality control, make a sub-dataset with a temporary depth coords.
        #ADCP QUALITY CONTROL ? For adcp data.
    else:
        no_meteoce_quality_control(dataset)

    # ----------------------------- #
    # ADDING SOME GLOBAL ATTRIBUTES #
    # ----------------------------- #

    l.section("Adding Global Attributes")

    add_global_attributes(dataset, pconfig, STANDARD_GLOBAL_ATTRIBUTES)

    # ------------- #
    # DATA ENCODING #
    # ------------- #
    l.section("Data Encoding")

    format_data_encoding(dataset)

    # -------------------- #
    # VARIABLES ATTRIBUTES #
    # -------------------- #
    l.section("Variables attributes")

    save_variables_name_for_odf_output(dataset, pconfig)
    dataset = format_variables_names_and_attributes(
        dataset=dataset,
        use_bodc_name=pconfig.bodc_name,
        p01_codes_map=P01_CODES_MAP,
        sensors_id=pconfig.sensors_id,
        #variable_to_add_sensor_type=pconfig.variables_to_add_sensor_type,
        cf_profile_id='time'
    )
    # ------------ #
    # MAKE FIGURES #
    # ------------ #

    # TODO

    # --------------- #
    # POST-PROCESSING #
    # --------------- #
    l.section("Post-processing")
    l.log("Nothing to do")

    # TODO if needed

    # ---------- #
    # ODF OUTPUT #
    # ---------- #

    l.section("Output")
    if pconfig.odf_output is True:
        l.warning('ODF output implemented yet') #TODO
#        _write_odf(dataset, pconfig)

    # ----------------- #
    # NETCDF FORMATTING #
    # ------------------#

    add_processing_timestamp(dataset)

    dataset = clean_dataset_for_nc_output(dataset, pconfig)

    dataset.attrs["history"] = l.logbook

    # ------------- #
    # NETCDF OUTPUT #
    # ------------- #
    if pconfig.netcdf_output is True:
        write_netcdf(dataset, pconfig)

    # ---------- #
    # LOG OUTPUT #
    # ---------- #
    if pconfig.make_log is True:
        write_log(pconfig)


def _load_viking_data(pconfig: ProcessConfig):
    dataset = load_meteoce_data(
        filenames=pconfig.input_files,
        buoy_name=pconfig.buoy_name,
        data_format=pconfig.data_format,
    )
    return dataset


def _compute_ctdo_potential_density(dataset: xr.Dataset):
    """Compute potential density as sigma_t:= Density(S,T,P) - 1000

    -Pressure used needs to be in dbar

    """

    required_variables = ['temperature', 'salinity']
    if all((var in dataset for var in required_variables)):

        if 'pres' in dataset.variables:
            pres = dataset.pres.pint.quantify().pint.to('dbar').data
        elif 'atm_pressure' in dataset.variables:
            pres = dataset.atm_pressure.pint.quantify().pint.to('dbar').data
        else:
            pres = None

        density = compute_density(
            temperature=dataset.temperature.data,
            salinity=dataset.salinity.data,
            pres=pres
        )
        dataset['density'] = (['time'], density - 1000)
        l.log('Potential density computed.')
    else:
        l.warning(f'Potential density computation aborted. One of more variables in {required_variables} was missing.')


def _correct_ph_for_salinity(dataset: xr.Dataset, pconfig: ProcessConfig):
    """Ph correction for salinity.

    ph_temperature (temperature is used to find the voltage measured by the probe, but the CTD
    temperature is used to find the ph.

    # TODO TEST THE DIFFERENCE BETWEEN USING PH AND TEMPERATURE_PH
    # Maje a test.

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


def _dissolved_oxygen_ml_per_L_to_umol_per_L(dataset: xr.Dataset):
    """
    """
    if dataset.dissolved_oxygen.attrs['units'] == ['ml/L']:
        dataset.dissolved_oxygen.values = dissolved_oxygen_ml_per_L_to_umol_per_L(dataset.dissolved_oxygen)
        dataset.dissolved_oxygen.attrs['units'] = 'umol/L'
        l.log('Dissolved Oxygen converted from [ml/L] to [umol/L].')
    else:
        l.warning(f"Wrong dissolved oxygen units {dataset.dissolved_oxygen.attrs['units']} for conversion from [ml/L] to [umol/L].")


def _dissolved_oxygen_umol_per_L_to_umol_per_kg(dataset: xr.Dataset):
    if dataset.dissolved_oxygen.attrs['units'] == ['umol/L']:
        if 'density' in dataset.variables:
            dataset.dissolved_oxygen.values = dissolved_oxygen_umol_per_L_to_umol_per_kg(dataset.dissolved_oxygen. dataset.density)
            dataset.dissolved_oxygen.attrs['units'] = 'umol/kg'
            l.log('Dissolved Oxygen converted from [umol/L] to [umol/kg].')
        else:
            l.warning(f"Density missing for oxygen conversion from [umol/L] to [umol/kg].")
    else:
        l.warning(f"Wrong dissolved oxygen units {dataset.dissolved_oxygen.attrs['units']} for conversion from [umol/L] to [umol/kg].")


def _dissolved_oxygen_corrections(dataset: xr.Dataset):
    """Dissolved oxygen correction for salinity, temperature and pressure.
    Atmospheric pressure is used since the probe is on a buoy.
    """
    # Temperature and Salinity Compensation
    if all(var in dataset.variables for var in ['temperature', 'salinity']):
        dataset.dissolved_oxygen.values = dissolved_oxygen_correction_for_salinity_SCOR_WG_142(
            dissolved_oxygen=dataset.dissolbed_oxygen.data,
            temperature=dataset.temperature.data,
            salinity=dataset.salinity.data
        )
        l.log(f'Dissolved oxygen correction for salinity was carried out')
    else:
        l.warning(f'Dissolved oxygen correction for salinity aborted. `temperature` and/or `salinity` not found.')

    # Pressure Compensation
    if all(var in dataset.variables for var in ['atm_pressure', 'density']):
        if dataset.dissolved_oxygen.attrs['units'] == ['umol/kg']:
            dataset.dissolved_oxygen.values = dissolved_oxygen_correction_for_pressure_JAC(
                dissolved_oxygen=dataset.dissolved_oxygen.data,
                pressure=dataset.atm_pressure.pint.quantify().to('dbar').data
            )
            l.log(f'Dissolved oxygen correction for pressure was carried out')
        else:
            l.warning(f'Dissolved oxygen correction for pressure aborted. Wrong dissolved oxygen units.')

    else:
        l.warning(f'Dissolved oxygen correction for pressure aborted. `atm_pressure` and or `density` not found.')

    # FIXME, Look a the BODC possible names for each correction.


def _compute_uv_ship(dataset: xr.Dataset):
    """Compute uship and vship from speed and course."""
    dataset["u_ship"], dataset["v_ship"] = north_polar2cartesian(dataset.speed, dataset.course)
    l.log('Platform velocities (u_ship, v_ship) computed from speed and course.')


def _quality_control(dataset: xr.Dataset, pconfig: ProcessConfig):
    """Pipe to adcp quality control for adcp data ?
    """

    dataset = meteoce_quality_control(
        dataset
    )
    return dataset


if __name__ == "__main__":
    import getpass
    import pandas as pd
    import matplotlib.pyplot as plt
    import scipy as sp
    file_path = '/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat'
    out_path = '/home/jeromejguay/Desktop/viking_test.nc'
    config = dict(
        HEADER=dict(
            process="viking_buoy",
            platform_type=None
        ),
        INPUT=dict(
            input_files=file_path,
            platform_file=None,
            platform_id=None
        ),
        OUTPUT=dict(
            netcdf_output=out_path,
            odf_output=None
        ),
        CRUISE=dict(
            event_qualifier1="meteoce"
        ),
        NETCDF_CF=dict(
            date_created=pd.Timestamp.now().strftime("%Y-%m-%d"),
            publisher_name=getpass.getuser(),
            source='viking_buoy'
        ),

        VIKING_PROCESSING=dict(
            buoy_name="pmza_riki",
            data_format="raw_dat",
            sensor_depth=0,
            navigation_file=None,
            leading_trim=None,
            trailing_trim=None,
            magnetic_declination=0,
            magnetic_declination_preset=None,
        ),
        VIKING_QUALITY_CONTROL=dict(quality_control=None),
        VIKING_OUTPUT=dict(
            merge_output_files=True,
            bodc_name=False,
            force_platform_metadata=None,
            odf_data=False,
            make_figures=False,
            make_log=False
        )
    )

    process_viking(config)

    ds = xr.open_dataset(out_path)

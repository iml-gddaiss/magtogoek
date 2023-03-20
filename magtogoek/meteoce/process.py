"""
This script has to functions to process and quick process meteoce buoy data.
These functions are called by the app command `process` and `quick meteoce`.

Date: July 25 2022
Made by: jeromejguay

Notes
-----

[February 2023]
    Missing BODC: oxy

    At the moment for some data correction. If the variable used has nans, the corrected value will (should) be a nan as well.
    Therefore, if a variable is present but all the values are nan, the corrected data will also be all nan.

    Maybe quality control should be done before and the transformation should check the flag values.

[March 2023]
    + Data from the wave_s wave heights are truncated to the first decimal.
    + Wind and Compass sample for 1 minute.
    + Direction are from 0 to 360 except for compass which is computed.


Todos
-----
[March 2023]
    For Wind and Wave directions:
    + The last heading value need to be subtracted (located in the short string)
    + Then the compass heading value needs to be added.

    For Flow Meter:
    + Add a correction option to correct for buoy uship,vship assuming that the flow meter
      measured the direction along the heading and that the heading "always" correspond the the surface
      current direction.
"""
import sys

import xarray as xr
from typing import *

from magtogoek import logger as l
from magtogoek.sci_tools import _rotate_heading
from magtogoek.process_common import BaseProcessConfig, resolve_output_paths, add_global_attributes, write_log, \
    write_netcdf, \
    add_processing_timestamp, clean_dataset_for_nc_output, format_data_encoding, add_navigation, \
    save_variables_name_for_odf_output
from magtogoek.attributes_formatter import format_variables_names_and_attributes
from magtogoek.meteoce.correction import meteoce_correction
from magtogoek.wps.sci_tools import compute_density, dissolved_oxygen_ml_per_L_to_umol_per_L, \
    dissolved_oxygen_umol_per_L_to_umol_per_kg
from magtogoek.sci_tools import north_polar2cartesian
from magtogoek.meteoce.loader import load_meteoce_data
from magtogoek.meteoce.quality_control import meteoce_quality_control, no_meteoce_quality_control
from magtogoek.adcp.correction import apply_motion_correction
from magtogoek.adcp.quality_control import adcp_quality_control, no_adcp_quality_control

# import click

l.get_logger("meteoce_processing")

STANDARD_GLOBAL_ATTRIBUTES = {"featureType": "timeSeriesProfile"}

VARIABLES_TO_DROP = ['ph_temperature', 'speed', 'course', 'magnetic_declination']

GLOBAL_ATTRS_TO_DROP = [
    "platform_type",
    "VAR_TO_ADD_SENSOR_TYPE",
    "P01_CODES_MAP",
    "xducer_depth",
    "variables_gen_name",
    "binary_mask_tests",
    "binary_mask_tests_values",
    "bodc_name"
]

# This mapping can be updating by the meteoce.corrections modules.
P01_CODES_MAP = {
    'time': "ELTMEP01",
    'wind_mean': "EWSBZZ01",
    'wind_max': "EGTSZZ01",
    'wind_direction_mean': "EWDAZZ01",
    'wind_direction_max': "EGTDSS01",
    'atm_temperature': "CTMPZZ01",
    'atm_humidity': "CRELZZ01",
    'atm_pressure': "CAPHZZ01",
    'wave_mean_height': "GAVHZZ01",
    'wave_maximal_height': "GCMXZZ01",
    'wave_period': "GTAMZZ01",
    'wave_direction': "GWDRWW01",
    'temperature': "TEMPPR01",
    'conductivity': "CNDCZZ01",
    'salinity': "PSLTZZ01",
    'density': "SIGTEQ01",
    'dissolved_oxygen': "DOXYUZ01",
    'ph': "PHXXZZXX",
    'par': "PFDPAR01",
    'fluorescence': "FLUOZZZZ",
    'chlorophyll': "CPHLPR01",
    'fdom': "CCOMD002",
    'co2_a': "ACO2XXXX",
    'co2_w': "PCO2XXXX",
    'u': "LCEWAP01",
    'v': "LCNSAP01",
    'w': "LRZAAP01",
    'e': "LERRAP01",
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

ADCP_VARIABLES_FOR_QC = [
    "u", "v", "w", "e",
    "bt_u", "bt_v", "bt_w", "bt_e",
    'pg', 'pg1', 'pg2', 'pg3', 'pg4',
    'corr1', 'corr2', 'corr3', 'corr4',
    'amp1', 'amp2', 'amp3', 'amp4',
    'roll_', 'pitch',
]


class ProcessConfig(BaseProcessConfig):
    # PROCESSING
    buoy_name: str = None
    data_format: str = None
    sensor_depth: float = None
    # wind_sensor: str = None # only the wmt700 is used for wind.

    ### ID
    adcp_id: str = None
    ctd_id: str = None
    ctdo_id: str = None
    nitrate_id: str = None
    # ADD MORE

    ### COMPUTE
    # CTD
    recompute_density: bool = None

    ### CORRECTION
    # Compass
    magnetic_declination_correction: bool

    # PH
    ph_salinity_correction: bool = None
    ph_coeffs: List[float] = None  # psal, k0, k2

    # OXY
    dissolved_oxygen_winkler_correction: bool = None
    rinko_coeffs: List[float] = None
    winkler_coeffs: List[float] = None
    dissolved_oxygen_pressure_correction: bool = None
    dissolved_oxygen_salinity_correction: bool = None

    # WPS sample and drift correction
    salinity_drift: List[float] = None
    salinity_drift_time: List[str] = None
    salinity_sample_correction: List[float] = None  # a*x + b

    temperature_drift: List[float] = None
    temperature_drift_time: List[str] = None
    temperature_sample_correction: List[float] = None

    dissolved_oxygen_drift: List[float] = None
    dissolved_oxygen_drift_time: List[str] = None
    dissolved_oxygen_sample_correction: List[float] = None

    co2w_drift: List[float] = None
    co2w_drift_time: List[str] = None
    co2w_sample_correction: List[float] = None

    ph_drift: List[float] = None
    ph_drift_time: List[str] = None
    ph_sample_correction: List[float] = None

    fluorescence_drift: List[float] = None
    fluorescence_drift_time: List[str] = None
    fluorescence_sample_correction: List[float] = None

    chlorophyll_drift: List[float] = None
    chlorophyll_drift_time: List[str] = None
    chlorophyll_sample_correction: List[float] = None

    fdom_drift: List[float] = None
    fdom_drift_time: List[str] = None
    fdom_sample_correction: List[float] = None

    # ADCP
    motion_correction_mode: str = None  # maybe adcp/process/adcp_processing...c

    # QUALITY_CONTROL

    # meteoce
    quality_control: bool = None

    regional_outlier: str = None,
    absolute_outlier: bool = True,

    climatology_variables: List[str] = None,
    climatology_dataset_path: str = None,  # A PATH to a netcdf
    climatology_threshold: float = None,
    # Set choices in tparser: "linear", "nearest", "zero", "slinear", "quadratic", "cubic"
    climatology_depth_interpolation_method: str = None,

    propagate_flags: bool = True,

    # adcp quality_control
    amplitude_threshold: int = None
    percentgood_threshold: int = None
    correlation_threshold: int = None
    horizontal_velocity_threshold: float = None
    vertical_velocity_threshold: float = None
    error_velocity_threshold: float = None
    pitch_threshold: float = None
    roll_threshold: float = None

    ## Variables set by the processing##
    climatology_dataset: xr.Dataset = None

    def __init__(self, config_dict: dict = None):
        super().__init__(config_dict)
        self.sensors_id = SENSOR_TYPE_TO_SENSORS_ID_MAP
        self.variables_to_drop = VARIABLES_TO_DROP
        self.global_attributes_to_drop = GLOBAL_ATTRS_TO_DROP
        self.p01_codes_map = P01_CODES_MAP


def process_meteoce(config: dict, drop_empty_attrs: bool = False, headless: bool = False):
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

    _load_climatology(pconfig)  # This is done here to catch an error early and exit.

    _process_meteoce_data(pconfig)


def _load_climatology(pconfig: ProcessConfig):
    try:
        pconfig.climatology_dataset = xr.open_dataset(pconfig.climatology_dataset_path)
    except ValueError as msg:
        l.warning(f'Unable to load the climatology netcdf file.\n\t Error: {msg}')


@resolve_output_paths
def _process_meteoce_data(pconfig: ProcessConfig):
    """
    Notes
    -----
    Time drift corrections are the last to be carried out.

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

    l.section("Data Computation (pre-correction).")

    # --------- #
    # COMPUTE 1 #
    # --------- #

    if all(x in dataset for x in ('speed', 'course')):
        _compute_uv_ship(dataset)

    # ----------- #
    # CORRECTION  #
    # ----------- #

    l.section("Data Correction")

    _magnetic_declination_correction(dataset, pconfig)  # <--+

    _meteoce_correction(dataset, pconfig)

    _adcp_correction(dataset, pconfig)  # ADD MAGNETIC DECLINATION --+

    # --------- #
    # COMPUTE 2 #
    # --------- #

    l.section("Data Computation (post-correction).")

    if 'density' not in dataset or pconfig.recompute_density is True:
        _compute_ctdo_potential_density(dataset)

    # --------------- #
    # QUALITY CONTROL #
    # --------------- #

    _quality_control(dataset, pconfig)

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
        p01_codes_map=pconfig.p01_codes_map,
        sensors_id=pconfig.sensors_id,
        # variable_to_add_sensor_type=pconfig.variables_to_add_sensor_type,
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
        l.warning('ODF output implemented yet')  # TODO
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

    Density computed using UNESCO 1983 (EOS 80) polynomial
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
        l.log('Potential density computed using UNESCO 1983 (EOS 80) polynomial.')
    else:
        l.warning(f'Potential density computation aborted. One of more variables in {required_variables} was missing.')


def _meteoce_correction(dataset: xr.Dataset, pconfig: ProcessConfig):
    meteoce_correction(dataset, pconfig)


def _adcp_correction(dataset: xr.Dataset, pconfig: ProcessConfig):
    if pconfig.motion_correction_mode in ["bt", "nav"]:
        apply_motion_correction(dataset, pconfig.motion_correction_mode)


def _compute_uv_ship(dataset: xr.Dataset):
    """Compute uship and vship from speed and course."""
    dataset["u_ship"], dataset["v_ship"] = north_polar2cartesian(dataset.speed, dataset.course)
    l.log('Platform velocities (u_ship, v_ship) computed from speed and course.')


def _quality_control(dataset: xr.Dataset, pconfig: ProcessConfig) -> xr.Dataset:
    """
    Pipe a sub-dataset to adcp quality control for adcp data ?
    Or call the qc function from viking_quality_control. ??
    """
    adcp_dataset = _make_adcp_sub_dataset(dataset)

    if pconfig.quality_control is True:
        dataset = _meteoce_quality_control(dataset, pconfig)
        adcp_dataset = _adcp_quality_control(dataset, pconfig)
    else:
        dataset = no_meteoce_quality_control(dataset)
        adcp_dataset = no_adcp_quality_control(adcp_dataset)

    _merge_adcp_quality_control(dataset, adcp_dataset)

    return dataset


def _make_adcp_sub_dataset(dataset: xr.Dataset) -> xr.Dataset:
    """Return dataset with the adcp variables.

    `temperature` and `pres` variables are omitted since they are not from the adcp.

    """
    adcp_variable_subset = set(dataset.variables).intersection(set(ADCP_VARIABLES_FOR_QC))
    return dataset[adcp_variable_subset]


def _merge_adcp_quality_control(dataset: xr.Dataset, adcp_dataset: xr.Dataset):
    """add `adcp_dataset` ancillary variables and `quality_comments` `global_attrs` to `dataset`."""
    for var in {v + "_QC" for v in ADCP_VARIABLES_FOR_QC}.intersection(set(adcp_dataset.variables)):
        dataset[var] = adcp_dataset[var]

    dataset.attrs["quality_comments"] += adcp_dataset.attrs["quality_comments"]


def _meteoce_quality_control(dataset: xr.Dataset, pconfig: ProcessConfig):
    """fixme"""
    try:
        climatology_dataset = xr.load_dataset(pconfig.climatology_dataset)
    except ValueError:
        # FIXME
        climatology_dataset = None

    dataset = meteoce_quality_control(
        dataset,
        regional_outlier=pconfig.regional_outlier,
        absolute_outlier=pconfig.absolute_outlier,
        climatology_variables=pconfig.climatology_variables,
        climatology_path=pconfig.climatology_dataset,
        climatology_threshold=pconfig.climatology_threshold,
        climatology_depth_interpolation_method=pconfig.climatology_depth_interpolation_method,
        propagate_flags=pconfig.propagate_flags
    )
    return dataset


def _adcp_quality_control(dataset: xr.Dataset, pconfig: ProcessConfig):
    """fixme"""
    dataset = dataset.expand_dims(dim={'depth': [0]})

    dataset.attrs['coord_system'] = "earth"

    dataset = adcp_quality_control(
        dataset,
        amp_th=pconfig.amplitude_threshold,
        corr_th=pconfig.correlation_threshold,
        pg_th=pconfig.percentgood_threshold,
        roll_th=pconfig.roll_threshold,
        pitch_th=pconfig.pitch_threshold,
        horizontal_vel_th=pconfig.horizontal_velocity_threshold,
        vertical_vel_th=pconfig.vertical_velocity_threshold,
        error_vel_th=pconfig.error_velocity_threshold,
        sidelobes_correction=False,
        bottom_depth=None,
        bad_pressure=False,
    )

    dataset = dataset.squeeze(['depth'])
    return dataset


def _magnetic_declination_correction(dataset: xr.Dataset, pconfig: ProcessConfig):
    if pconfig.magnetic_declination_correction is True:
        if all(var in dataset.variables for var in ['heading', 'magnetic_declination']):
            dataset.heading.values = _rotate_heading(dataset.heading.data, dataset.magnetic_declination.data)
            l.log(f"Heading transformed to true north.")
        else:
            l.warning("Unable to transform heading to true north. Variables missing.")


def _dissolved_oxygen_ml_per_L_to_umol_per_L(dataset: xr.Dataset):
    """
    """
    if dataset.dissolved_oxygen.attrs['units'] == ['ml/L']:
        dataset.dissolved_oxygen.values = dissolved_oxygen_ml_per_L_to_umol_per_L(dataset.dissolved_oxygen)
        dataset.dissolved_oxygen.attrs['units'] = 'umol/L'
        l.log('Dissolved Oxygen converted from [ml/L] to [umol/L].')
    else:
        l.warning(
            f"Wrong dissolved oxygen units {dataset.dissolved_oxygen.attrs['units']} for conversion from [ml/L] to [umol/L].")


def _dissolved_oxygen_umol_per_L_to_umol_per_kg(dataset: xr.Dataset):
    if dataset.dissolved_oxygen.attrs['units'] == ['umol/L']:
        if 'density' in dataset.variables:
            dataset.dissolved_oxygen.values = dissolved_oxygen_umol_per_L_to_umol_per_kg(
                dataset.dissolved_oxygen.dataset.density)
            dataset.dissolved_oxygen.attrs['units'] = 'umol/kg'
            l.log('Dissolved Oxygen converted from [umol/L] to [umol/kg].')
        else:
            l.warning(f"Density missing for oxygen conversion from [umol/L] to [umol/kg].")
    else:
        l.warning(
            f"Wrong dissolved oxygen units {dataset.dissolved_oxygen.attrs['units']} for conversion from [umol/L] to [umol/kg].")


if __name__ == "__main__":
    import getpass
    import pandas as pd

    file_path = '/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat'
    out_path = '/home/jeromejguay/ImlSpace/Data/iml4_2021/meteoc_riki_2021.nc'
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
        # METEO_QC
        # WPS_QC
        # ADCP_QC
    )

    # process_viking(config)

    ds = xr.open_dataset(out_path)

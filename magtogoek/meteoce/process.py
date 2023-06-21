"""
Date: July 2022
Made by: jeromejguay

This script has to functions to process and quick process meteoce buoy data.
These functions are called by the app command `process` and `quick meteoce`.

TODO:
-Specify the depth of the adcp first bin ? config file ?

Notes
-----

[1] .. [February 2023] JeromeJGuay
    When variables requires other variables for corrections, Nan values will propagate.
    At the moment, variables full of Nan will still be use for correction.
    This could possibly a problem.

[2] .. [March 2023] JeromeJGuay
    Data from the wave_s wave heights are truncated to the first decimal.

[3] .. [March 2023] JeromeJGuay
    GPS bearing and course data seem to be bad. We believe that the bearing and course data are instant measurements.
    Thus wave induced rapid horizontal oscillation and the rocking of the buoy, the GPS being located about ~2-3 meters
    above the floating line, result in higher oscillation and amplitude in the speed values. Since speed dependent values
    are average over ~ 1 minutes, we need at least ~1 minutes average values from the gps.who C<e

"""

import xarray as xr
from typing import *

from magtogoek import logger as l
from magtogoek.sci_tools import rotate_2d_vector, north_polar2cartesian
from magtogoek.process_common import BaseProcessConfig, resolve_output_paths, add_global_attributes, write_log, \
    write_netcdf, add_processing_timestamp, clean_dataset_for_nc_output, format_data_encoding, add_navigation, \
    add_platform_metadata_to_dataset, add_correction_attributes_to_dataarray
from magtogoek.attributes_formatter import format_variables_names_and_attributes
from magtogoek.platforms import PlatformMetadata

from magtogoek.wps.sci_tools import compute_in_situ_density, dissolved_oxygen_ml_per_L_to_umol_per_L, dissolved_oxygen_umol_per_L_to_umol_per_kg

from magtogoek.meteoce.loader import load_meteoce_data
from magtogoek.meteoce.correction import wps_data_correction, meteoce_data_magnetic_declination_correction, wind_motion_correction
from magtogoek.meteoce.quality_control import meteoce_quality_control, no_meteoce_quality_control
from magtogoek.meteoce.odf_exporter import make_odf

from magtogoek.adcp.correction import apply_motion_correction as adcp_motion_correction
from magtogoek.adcp.quality_control import adcp_quality_control, no_adcp_quality_control

from magtogoek.navigation import _compute_navigation


l.get_logger("meteoce_processing")

STANDARD_GLOBAL_ATTRIBUTES = {"featureType": "timeSeriesProfile"}

VARIABLES_TO_DROP = ['ph_temperature', 'speed', 'course', 'gps_magnetic_declination']#, 'last_heading'] Not currently loaded

GLOBAL_ATTRS_TO_DROP = [
    "binary_mask_tests",
    "binary_mask_tests_values",
]

# This mapping can be updating by the meteoce.corrections modules.
P01_CODES_MAP = {
    'time': "ELTMEP01",
    'mean_wind_speed': "EWSBZZ01",
    'max_wind_speed': "EGTSZZ01",
    'mean_wind_direction': "EWDAZZ01",
    'max_wind_direction': "EGTDSS01",
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
    #'fluorescence': "FLUOZZZZ",
    'scattering': "ABSP700A",
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
    'roll_std': "ROLLSD01",
    'pitch_std': "PTCHSD01",
    'u_ship': "APEWGP01",
    'v_ship': "APNSGP01"
}


SENSORS_TO_VARIABLES_MAP = {
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
    'triplet': ['scattering', 'chlorophyll', 'fdom'],
    'co2w': ['co2_w'],
    'co2a': ['co2_a'],
    'wave': ['wave_mean_height', 'wave_maximal_height', 'wave_period'],
    'wind': ['mean_wind_speed', 'max_wind_speed', 'mean_wind_direction', 'max_wind_direction'],
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
    data_format: str = None  # [viking_dat, ]

    ##### ID #####
    adcp_id: str = None
    ctd_id: str = None
    ctdo_id: str = None
    doxy_id: str = None
    #nitrate_id: str = None
    ph_id: str = None
    par_id: str = None
    triplet_id: str = None
    co2w_id: str = None
    co2a_id: str = None
    wave_id: str = None
    wind_id: str = None
    meteo_id: str = None

    ##### COMPUTE #####
    # GPS
    #navigation: str = "drop" # ["drop", "keep", "recompute"]
    compute_uv_ship: str = None

    # CTD
    recompute_density: bool = None

    ##### CORRECTION #####
    magnetic_declination: Union[bool, float] = None
    motion_correction_mode: str = "nav" # ["bt", "nav", "off"]

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

    scattering_drift: List[float] = None
    scattering_drift_time: List[str] = None
    scattering_sample_correction: List[float] = None

    chlorophyll_drift: List[float] = None
    chlorophyll_drift_time: List[str] = None
    chlorophyll_sample_correction: List[float] = None

    fdom_drift: List[float] = None
    fdom_drift_time: List[str] = None
    fdom_sample_correction: List[float] = None

    # ADCP
    magnetic_declination_preset: float = None

    ##### QUALITY_CONTROL #####

    # meteoce
    quality_control: bool = None

    regional_outlier: str = None
    absolute_outlier: bool = True

    climatology_variables: List[str] = None
    climatology_dataset_path: str = None  # A PATH to a netcdf
    climatology_threshold: float = None
    # Set choices in tparser: "linear", "nearest", "zero", "slinear", "quadratic", "cubic"
    climatology_depth_interpolation_method: str = None

    propagate_flags: bool = True

    # adcp quality_control
    amplitude_threshold: int = None
    percentgood_threshold: int = None
    correlation_threshold: int = None
    horizontal_velocity_threshold: float = None
    vertical_velocity_threshold: float = None
    error_velocity_threshold: float = None
    pitch_threshold: float = None
    roll_threshold: float = None

    ##### Variables set by the processing #######
    climatology_dataset: xr.Dataset = None

    def __init__(self, config_dict: dict = None):
        super().__init__(config_dict)
        self.platform_type = "buoy"  # This needs to be buoy
        self.sensors_to_variables_map = SENSORS_TO_VARIABLES_MAP
        self.variables_to_drop = VARIABLES_TO_DROP
        self.global_attributes_to_drop = GLOBAL_ATTRS_TO_DROP
        self.p01_codes_map = P01_CODES_MAP

        self.sensors_to_instrument_id = {
            'adcp': self.adcp_id,
            "ctd": self.ctd_id,
            "ctdo": self.ctdo_id,
            "doxy": self.doxy_id,
            # 'nitrate': None,  # Not implemented yet.
            "ph": self.ph_id,
            'par': self.par_id,
            'triplet': self.triplet_id,
            'co2w': self.co2w_id,
            'co2a': self.co2a_id,
            'wave': self.wave_id,
            'wind': self.wind_id,
            'meteo': self.meteo_id
        }

        self.merge_output_files = True # FIXME BUG


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
    l.reset()
    pconfig = ProcessConfig(config)
    pconfig.drop_empty_attrs = drop_empty_attrs
    pconfig.headless = headless

    if pconfig.climatology_dataset_path is not None:
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
    l.section("Navigation data")

    if pconfig.navigation_file:
        l.section("Navigation data")
        l.log(f"Loading the following navigation data from {pconfig.navigation_file}")
        add_navigation(dataset, pconfig.navigation_file)

    l.section('Navigation data computation')

    if pconfig.compute_uv_ship != "off":
        _compute_uv_ship(dataset=dataset, pconfig=pconfig)

    # ------------------- #
    # METEOCE CORRECTION  #
    # ------------------- #

    l.section("Meteoce data correction")

    _set_magnetic_declination(dataset, pconfig)

    meteoce_data_magnetic_declination_correction(dataset, pconfig)

    wps_data_correction(dataset, pconfig)

    wind_motion_correction(dataset)

    # --------------- #
    # METEOCE COMPUTE #
    # --------------- #

    l.section("Meteoce data computation.")

    if 'density' not in dataset or pconfig.recompute_density is True:
        _compute_ctdo_potential_density(dataset)

    # ---------------- #
    # ADCP CORRECTION  #
    # ---------------- #

    l.section("Adcp data correction")

    _adcp_correction(dataset, pconfig)

    # --------------- #
    # QUALITY CONTROL #
    # --------------- #

    _quality_control(dataset, pconfig)

    # ------------------------ #
    # ADDING GLOBAL ATTRIBUTES #
    # ------------------------ #

    l.section("Adding Global Attributes")

    add_global_attributes(dataset, pconfig, STANDARD_GLOBAL_ATTRIBUTES)

    add_platform_metadata_to_dataset(dataset=dataset, pconfig=pconfig)

    _add_platform_instrument_metadata_to_dataset(dataset, pconfig) # TODO TEST

    # ------------- #
    # DATA ENCODING #
    # ------------- #
    l.section("Data Encoding")

    format_data_encoding(dataset)

    # -------------------- #
    # VARIABLES ATTRIBUTES #
    # -------------------- #
    l.section("Variables attributes")

    dataset = format_variables_names_and_attributes(
        dataset=dataset,
        use_bodc_name=pconfig.use_bodc_name,
        p01_codes_map=pconfig.p01_codes_map,
        cf_profile_id='time'
    )

    _add_platform_instrument_metadata_to_variables(dataset, pconfig) # TODO TEST

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
        _write_odf(dataset, pconfig)

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

    Density computed using TEOS-10 polynomial (Roquet et al., 2015)

    """

    required_variables = ['temperature', 'salinity']
    if all((var in dataset for var in required_variables)):
        _log_msg = 'Potential density computed using TEOS-10 polynomial. Absolute Salinity, Conservative Temperature'
        if 'pres' in dataset.variables:
            pres = dataset.pres.pint.quantify().pint.to('dbar').pint.dequantify().values
        elif 'atm_pressure' in dataset.variables:
            pres = dataset.atm_pressure.pint.quantify().pint.to('dbar').pint.dequantify().values - 10.1325
        else:
            pres = 0
            _log_msg += ', sea pressure = 0'

        if "longitude" in dataset.variables:
            longitude = dataset.longitude.data
        else:
            longitude = 0
            _log_msg += ', longitude = 0'

        if "latitude" in dataset.variables:
            latitude = dataset.latitude.data
        else:
            latitude = 0
            _log_msg += ', latitude = 0'

        density = compute_in_situ_density(
            temperature=dataset.temperature.data,
            salinity=dataset.salinity.data,
            pres=pres,
            latitude=latitude,
            longitude=longitude
        )

        dataset['density'] = (['time'], density - 1000)

        l.log(_log_msg + '.')
    else:
        l.warning(f'Potential density computation aborted. One of more variables in {required_variables} was missing.')


def _set_magnetic_declination(dataset: xr.Dataset, pconfig: ProcessConfig):
    """Set the magnetic_declination value or values in the process config.

    Either from the GPS (dataset variable) or the ProcessConfig.magnetic_declination .

    If the magnetic declination is taken from the GSP data, any nan values will be interpolated.
    """
    if pconfig.magnetic_declination is True:
        if 'gps_magnetic_declination' in dataset.variables:
            pconfig.magnetic_declination = dataset['gps_magnetic_declination'].interpolate_na('time').data
        else:
            l.warning('Unable to carry magnetic declination correction. No magnetic declination value found.')
            pconfig.magnetic_declination = None

    if isinstance(pconfig.magnetic_declination, (float, int)):
        pconfig.magnetic_declination = pconfig.magnetic_declination

    pconfig.magnetic_declination = None


def _adcp_correction(dataset: xr.Dataset, pconfig: ProcessConfig):
    """
    Carry magnetic declination correction and motion correction.
    """
    if pconfig.magnetic_declination is not None:
        if pconfig.magnetic_declination_preset is not None:
            angle = round((pconfig.magnetic_declination - pconfig.magnetic_declination_preset), 4)
            l.log(f"An additional correction of {angle} degree east was applied to the ADCP velocities.")
        else:
            angle = pconfig.magnetic_declination
            l.log(f"A correction of {angle} degree east was applied to the ADCP velocities.")

        if all(v in dataset for v in ["bt_u", "bt_v"]):
            dataset.u.values, dataset.v.values = rotate_2d_vector(dataset.u, dataset.v, -angle)
            l.log(f"Velocities transformed to true north and true east.")

        if all(v in dataset for v in ["bt_u", "bt_v"]):
            dataset.bt_u.values, dataset.bt_v.values = rotate_2d_vector(dataset.bt_u, dataset.bt_v, -angle)
            l.log(f"Bottom velocities transformed to true north and true east.")

    if pconfig.motion_correction_mode in ["bt", "nav"]:
        adcp_motion_correction(dataset, pconfig.motion_correction_mode)


def _compute_uv_ship(dataset: xr.Dataset, pconfig: ProcessConfig):
    """Compute u_ship and v_ship and add them to dataset.

    Either from speed and course or longitude and latitude depending on
    `pconfig.compute_uv_ship` value.
        ll: longitude and latitude
        sc: speed and course
    """
    if pconfig.compute_uv_ship == "ll":
        if all(v in dataset for v in ['lon', 'lat']):
            l.log('Platform velocities (u_ship, v_ship) computed from longitude and latitude data.')
            _compute_navigation(dataset)

    elif pconfig.compute_uv_ship == "sp":
        if all(x in dataset for x in ('speed', 'course')):
            l.log('Platform velocities (u_ship, v_ship) computed from speed and course data.')
            dataset["u_ship"], dataset["v_ship"] = north_polar2cartesian(dataset.speed, dataset.course)


def _quality_control(dataset: xr.Dataset, pconfig: ProcessConfig) -> xr.Dataset:
    """
    Pipe a sub-dataset to adcp quality control for adcp data ?
    Or call the qc function from viking_quality_control. ??
    """
    # FIXME ERROR WITH HORIZONTAL VEL TEST FLAG DIMS
    # adcp_dataset = _make_adcp_sub_dataset(dataset)
    # adcp_dataset.attrs['coord_system'] = 'earth'
    l.warning('ADCP QC DISABLED FIXME')
    if pconfig.quality_control is True:
        dataset = _meteoce_quality_control(dataset, pconfig)
        #adcp_dataset = _adcp_quality_control(adcp_dataset, pconfig)
        # no_adcp_quality_control(adcp_dataset)  # FIXME ERROR WITH HORIZONTAL VEL TEST FLAG DIMS
    else:
        no_meteoce_quality_control(dataset)
        # no_adcp_quality_control(adcp_dataset)

    # adcp_dataset.attrs.pop('coord_system')

    # _merge_adcp_quality_control(dataset, adcp_dataset)

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
        climatology_dataset=pconfig.climatology_dataset,
        climatology_threshold=pconfig.climatology_threshold,
        climatology_depth_interpolation_method=pconfig.climatology_depth_interpolation_method,
        propagate_flags=pconfig.propagate_flags
    )
    return dataset


def _adcp_quality_control(dataset: xr.Dataset, pconfig: ProcessConfig):
    """fixme"""
    adcp_dataset = dataset.expand_dims(dim={'depth': [0]})

    adcp_dataset.attrs['coord_system'] = "earth"

    adcp_dataset = adcp_quality_control(
        adcp_dataset,
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

    return adcp_dataset.squeeze(['depth'])


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


def _add_platform_instrument_metadata_to_dataset(dataset: xr.Dataset, pconfig: ProcessConfig):
    if pconfig.platform_metadata is not None:
        for sensor, instrument_id in pconfig.sensors_to_instrument_id.items():
            if instrument_id not in pconfig.platform_metadata.instruments:
                continue

            instrument_metadata = {
                'sensor_type': pconfig.platform_metadata.instruments[pconfig.adcp_id].sensor_type,
                'sensor_height': pconfig.platform_metadata.instruments[pconfig.adcp_id].sensor_height,
                'sensor_depth': pconfig.platform_metadata.instruments[pconfig.adcp_id].sensor_depth,
                'serial_number': pconfig.platform_metadata.instruments[pconfig.adcp_id].serial_number, # could be set from raw
                'manufacturer': pconfig.platform_metadata.instruments[pconfig.adcp_id].manufacturer,
                'model': pconfig.platform_metadata.instruments[pconfig.adcp_id].model, # could be set from raw (model_number)
                'firmware_version': pconfig.platform_metadata.instruments[pconfig.adcp_id].firmware_version,
                'chief_scientist': pconfig.platform_metadata.instruments[pconfig.adcp_id].chief_scientist,
                'description': pconfig.platform_metadata.instruments[pconfig.adcp_id].description,
                'comments': pconfig.platform_metadata.instruments[pconfig.adcp_id].comments,
            }

            for key, value in instrument_metadata.items():
                if value is None:
                    instrument_metadata.pop(key)

            for variable in set(pconfig.sensors_to_variables_map[sensor]).intersection(set(dataset.variables)):
                for key, value in instrument_metadata.items():
                    if key in dataset[variable].attrs and not pconfig.force_platform_metadata:
                        if not dataset[variable].attrs[key]:
                            dataset[variable].attrs[key] = value
                    else:
                        dataset[variable].attrs[key] = value


def _add_platform_instrument_metadata_to_variables(dataset: xr.Dataset, pconfig: ProcessConfig):
    if pconfig.platform_metadata is not None:
        for sensor, instrument_id in pconfig.sensors_to_instrument_id.items():
            if instrument_id not in pconfig.platform_metadata.instruments:
                continue

            instrument_metadata = {
                sensor + '_sensor_height': pconfig.platform_metadata.instruments[pconfig.adcp_id].sensor_height,
                sensor + '_sensor_depth': pconfig.platform_metadata.instruments[pconfig.adcp_id].sensor_depth,
                sensor + '_serial_number': pconfig.platform_metadata.instruments[pconfig.adcp_id].serial_number,
                sensor + '_manufacturer': pconfig.platform_metadata.instruments[pconfig.adcp_id].manufacturer,
                sensor + '_model': pconfig.platform_metadata.instruments[pconfig.adcp_id].model,
                sensor + '_firmware_version': pconfig.platform_metadata.instruments[pconfig.adcp_id].firmware_version,
                sensor + '_chief_scientist': pconfig.platform_metadata.instruments[pconfig.adcp_id].chief_scientist,
                sensor + '_description': pconfig.platform_metadata.instruments[pconfig.adcp_id].description,
                sensor + '_comments': pconfig.platform_metadata.instruments[pconfig.adcp_id].comments,
            }

            for key, value in instrument_metadata.items():
                if value is None:
                    continue

                if key in dataset.attrs and not pconfig.force_platform_metadata:
                    if not dataset.attrs[key]:
                        dataset.attrs[key] = value
                else:
                    dataset.attrs[key] = value


def _write_odf(dataset: xr.Dataset, pconfig: ProcessConfig):
    if pconfig.platform_metadata is None:
        pconfig.platform_metadata = PlatformMetadata()
        pconfig.platform_metadata.platform.platform_type = pconfig.platform_type

    for key, value in pconfig.sensors_to_instrument_id.items():
        if value is None:
            pconfig.platform_metadata.add_instrument(instrument_id=key+f"_01",
                                                     instrument_meta={"sensor_type": key})

    _ = make_odf(
        dataset=dataset,
        platform_metadata=pconfig.platform_metadata,
        global_attributes=pconfig.global_attributes,
        p01_codes_map=pconfig.p01_codes_map,
        use_bodc_name=pconfig.use_bodc_name,
        output_path=pconfig.odf_path,
    )


if __name__ == "__main__":
    import getpass
    import pandas as pd

    file_path = '/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat'
    out_path = '/home/jeromejguay/ImlSpace/Data/iml4_2021/meteoc_riki_2021.nc'
    _config = dict(
        HEADER=dict(
            process="meteoce",
        ),
        INPUT=dict(
            input_files=file_path,
            platform_file=None,
            platform_id=None
        ),
        OUTPUT=dict(
            netcdf_output=out_path,
            odf_output=True
        ),
        CRUISE=dict(
            country_institute_code="",
            organization="",
            chief_scientist="",
            start_date="",
            end_date="",
            cruise_number="BOUEE2021",
            cruise_name="",
            cruise_description="",
            event_number="RIMOUSKI",
            event_qualifier1="IML4",
            event_comments=""
        ),
        NETCDF_CF=dict(
            date_created=pd.Timestamp.now().strftime("%Y-%m-%d"),
            publisher_name=getpass.getuser(),
            source='viking_buoy'
        ),
        PROCESSING=dict(
            navigation_file=None,
            leading_trim=None,
            trailing_trim=None,
        ),

        VIKING_PROCESSING=dict(
            buoy_name="PMZA-RIKI",
            data_format="viking_dat",
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

    process_meteoce(_config)

    ds = xr.open_dataset(out_path)

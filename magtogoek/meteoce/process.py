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
import sys

import gsw
import numpy as np
import xarray as xr
from typing import *

from magtogoek import logger as l

from magtogoek.tools import cut_index, cut_times, get_datetime_and_count
from magtogoek.process_common import BaseProcessConfig, resolve_output_paths, add_global_attributes, write_log, \
    write_netcdf, netcdf_raw_exist, load_netcdf_raw, write_netcdf_raw, \
    add_processing_timestamp, clean_dataset_for_nc_output, format_data_encoding, add_navigation, \
    add_platform_metadata_to_dataset
from magtogoek.attributes_formatter import format_variables_names_and_attributes
from magtogoek.platforms import PlatformMetadata

from magtogoek.wps.sci_tools import compute_in_situ_density, dissolved_oxygen_ml_per_L_to_umol_per_L, dissolved_oxygen_umol_per_L_to_umol_per_kg

from magtogoek.meteoce.loader import load_meteoce_data
from magtogoek.meteoce.correction import wps_data_correction, apply_magnetic_correction, apply_motion_correction
from magtogoek.meteoce.quality_control import meteoce_quality_control, no_meteoce_quality_control
from magtogoek.meteoce.plots import make_meteoce_figure
from magtogoek.meteoce.odf_exporter import make_odf

from magtogoek.adcp.quality_control import adcp_quality_control, no_adcp_quality_control

from magtogoek.navigation import compute_speed_and_course, compute_uv_ship


l.get_logger("meteoce_processing")

STANDARD_GLOBAL_ATTRIBUTES = {"featureType": "timeSeriesProfile"}

VARIABLES_TO_DROP = ['ph_temperature', 'pres'] # 'magnetic_declination' can be added in _set_magnetic_declination

GLOBAL_ATTRS_TO_DROP = [
]


# This mapping can be changed by the meteoce.corrections modules.
P01_CODES_MAP = {
    'time': "ELTMEP01",
    "wind_speed": "EWSBSS01",
    "wind_speed_QC": "EWSBSS01_QC",
    "wind_direction": "EWDASS01",
    "wind_direction_QC": "EWDASS01_QC",
    "wind_gust": "EGTSSS01",
    "wind_gust_QC": "EGTSSS01_QC",
    "wind_gust_direction": "EGTDSS01",         # Not in Viking Data
    "wind_gust_direction_QC": "EGTDSS01_QC",   # Not in Viking Data
    'atm_temperature': "CTMPZZ01",
    'atm_temperature_QC': "CTMPZZ01_QC",
    'atm_humidity': "CRELZZ01",
    'atm_humidity_QC': "CRELZZ01_QC",
    'atm_pressure': "CAPHZZ01",
    'atm_pressure_QC': "CAPHZZ01_QC",
    'wave_mean_height': "GAVHZZ01",
    'wave_mean_height_QC': "GAVHZZ01_QC",
    'wave_maximal_height': "GCMXZZ01",
    'wave_maximal_height_QC': "GCMXZZ01_QC",
    'wave_period': "GTAMZZ01",
    'wave_period_QC': "GTAMZZ01_QC",
    'wave_direction': "GWDRWW01",
    'wave_direction_QC': "GWDRWW01_QC",
    'temperature': "TEMPPR01",
    'temperature_QC': "TEMPPR01_QC",
    'conductivity': "CNDCZZ01",
    'conductivity_QC': "CNDCZZ01_QC",
    'salinity': "PSLTZZ01",
    'salinity_QC': "PSLTZZ01_QC",
    'density': "SIGTEQ01",
    'density_QC': "SIGTEQ01_QC",
    'dissolved_oxygen': "DOXYUZ01",
    'dissolved_oxygen_QC': "DOXYUZ01_QC",
    'ph': "PHXXZZXX",
    'ph_QC': "PHXXZZXX_QC",
    'par': "PFDPAR01",
    'par_QC': "PFDPAR01_QC",
    'scattering': "ABSP700A",
    'scattering_QC': "ABSP700A_QC",
    'chlorophyll': "CPHLPR01",
    'chlorophyll_QC': "CPHLPR01_QC",
    'fdom': "CCOMD002",
    'fdom_QC': "CCOMD002_QC",
    'co2_a': "ACO2XXXX",
    'co2_a_QC': "ACO2XXXX_QC",
    'co2_w': "PCO2XXXX",
    'co2_w_QC': "PCO2XXXX_QC",
    'u': "LCEWAP01",
    'u_QC': "LCEWAP01_QC",
    'v': "LCNSAP01",
    'v_QC': "LCNSAP01_QC",
    'w': "LRZAAP01",
    'w_QC': "LRZAAP01_QC",
    'e': "LERRAP01",
    'lon': "ALONZZ01",
    'lat': "ALATZZ01",
    'heading': "HEADCM01",
    'roll_': "ROLLGP01",
    'pitch': "PTCHGP01",
    'roll_std': "ROLLSD01",
    'pitch_std': "PTCHSD01",
    'u_ship': "APEWZZ01",
    'v_ship': "APNSZZ01",
    "speed": "APSAZZ01",
    "course": "APDAZZ01"
}


SENSORS_TO_VARIABLES_MAP = {
    'adcp': ["u", "v", "w", "e"],
    "ctd": ["conductivity", "salinity", "temperature", "density"],
    "ctdo": ["conductivity", "salinity", "temperature", "density", "dissolved_oxygen"],
    # "doxy": ["dissolved_oxygen"], # Not implemented yet.
    # 'nitrate': [],  # Not implemented yet.
    "ph": ['ph'],
    'par': ['par'],
    'triplet': ['scattering', 'chlorophyll', 'fdom'],
    'co2w': ['co2_w'],
    'co2a': ['co2_a'],
    'wave': ['wave_mean_height', 'wave_maximal_height', 'wave_period'],
    'wind': ["wind_speed", "wind_direction", "wind_gust"],
    'meteo': ['atm_temperature', 'atm_humidity', 'atm_pressure']
}


# If modified, carry the modification to `meteoce.process.ProcessConfig` and to `config_handler.py`.
SPIKE_QC_VARIABLES = [
    "salinity", "temperature", "dissolved_oxygen", "co2w", "ph", "scattering", "chlorophyll", "fdom"
]


class ProcessConfig(BaseProcessConfig):
    # PROCESSING
    buoy_name: str = None
    data_format: str = None  # [viking_dat, ]
    sampling_depth: float = None  # Used for computation *(density) and for EVENT HEADER IN METEOCE

    ##### ID #####
    adcp_id: str = None
    ctd_id: str = None
    ctdo_id: str = None
    # doxy_id: str = None # Not implemented yet.
    # nitrate_id: str = None # Not implemented yet.
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
    recompute_speed_course: bool = None
    compute_uv_ship: bool = None

    # CTD
    recompute_density: bool = None

    ##### CORRECTION #####
    magnetic_declination: float = None
    adcp_motion_correction: bool = None
    wind_motion_correction: bool = None

    # PH
    ph_salinity_correction: bool = None
    ph_salinity_coeffs: List[float] = None  # psal, k0, k2

    # OXY
    dissolved_oxygen_winkler_correction: bool = None
    dissolved_oxygen_winkler_coeffs: List[float] = None  # d1_w, d2_w
    dissolved_oxygen_rinko_coeffs: List[float] = None  # d0, d1, d2, c0, c1, c2
    dissolved_oxygen_pressure_correction: bool = None
    dissolved_oxygen_salinity_correction: bool = None

    # WPS sample and drift correction
    salinity_drift: List[float] = None
    salinity_drift_start_time: List[str] = None
    salinity_sample_correction: List[float] = None  # a*x + b

    temperature_drift: List[float] = None
    temperature_drift_start_time: List[str] = None
    temperature_sample_correction: List[float] = None

    dissolved_oxygen_drift: List[float] = None
    dissolved_oxygen_drift_start_time: List[str] = None
    dissolved_oxygen_sample_correction: List[float] = None

    co2w_drift: List[float] = None
    co2w_drift_start_time: List[str] = None
    co2w_sample_correction: List[float] = None

    ph_drift: List[float] = None
    ph_drift_start_time: List[str] = None
    ph_sample_correction: List[float] = None

    scattering_drift: List[float] = None
    scattering_drift_start_time: List[str] = None
    scattering_sample_correction: List[float] = None

    chlorophyll_drift: List[float] = None
    chlorophyll_drift_start_time: List[str] = None
    chlorophyll_sample_correction: List[float] = None

    fdom_drift: List[float] = None
    fdom_drift_start_time: List[str] = None
    fdom_sample_correction: List[float] = None

    salinity_spike_threshold: float = None
    salinity_spike_window: int = None

    temperature_spike_threshold: float = None
    temperature_spike_window: int = None

    dissolved_oxygen_spike_threshold: float = None
    dissolved_oxygen_spike_window: int = None

    co2w_spike_threshold: float = None
    co2w_spike_window: int = None

    ph_spike_threshold: float = None
    ph_spike_window: int = None

    scattering_spike_threshold: float = None
    scattering_spike_window: int = None

    chlorophyll_spike_threshold: float = None
    chlorophyll_spike_window: int = None

    fdom_spike_threshold: float = None
    fdom_spike_window: int = None

    # ADCP
    adcp_magnetic_declination_preset: float = None # set in the adcp config.

    ##### QUALITY_CONTROL #####

    # meteoce
    quality_control: bool = None
    propagate_flags: bool = True

    absolute_outlier: bool = True
    regional_outlier: str = None

    # adcp quality_control
    adcp_horizontal_velocity_threshold: float = None
    adcp_vertical_velocity_threshold: float = None
    adcp_error_velocity_threshold: float = None
    adcp_pitch_threshold: float = None
    adcp_roll_threshold: float = None


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
            # "doxy": self.doxy_id, # Not implemented yet.
            # 'nitrate': None,      # Not implemented yet.
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

        self.magnetic_correction_to_apply: float = None


def process_meteoce(config: dict, drop_empty_attrs: bool = False,
                    headless: bool = False, from_raw: bool = False):
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
        If true, figures are not displayed but are saved in the output directory.
    from_raw :
        If true, data is loaded from the raw files (input_files).

    The actual data processing is carried out by _process_viking_data.
    """
    l.reset()
    pconfig = ProcessConfig(config)
    pconfig.drop_empty_attrs = drop_empty_attrs
    pconfig.headless = headless
    pconfig.from_raw = from_raw

    _process_meteoce_data(pconfig)


@resolve_output_paths
def _process_meteoce_data(pconfig: ProcessConfig):

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
    if pconfig.recompute_speed_course is True:
        _recompute_speed_course(dataset=dataset)
    if pconfig.compute_uv_ship is True:
        _compute_uv_ship(dataset=dataset)

    # ------------------- #
    # METEOCE CORRECTION  #
    # ------------------- #

    l.section("Meteoce data correction")

    _compute_pressure_at_sampling_depth(dataset, pconfig) # pressure (water pressure) is required for some wps correction

    apply_magnetic_correction(dataset, pconfig)

    apply_motion_correction(dataset, pconfig)

    wps_data_correction(dataset, pconfig)

    # --------------- #
    # METEOCE COMPUTE #
    # --------------- #

    l.section("Meteoce data computation.")

    if 'density' not in dataset or pconfig.recompute_density is True:
        _compute_ctd_potential_density(dataset, pconfig)


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

    # >>>> METEOCE SPECIFIC
    _add_platform_instrument_metadata_to_dataset(dataset, pconfig)

    if pconfig.sampling_depth is not None:
        dataset.attrs['sampling_depth_m'] = pconfig.sampling_depth # used for ODF and remove from netcdf output.
    # <<<<

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
    # >>>> METEOCE SPECIFIC
    _add_platform_instrument_metadata_to_variables(dataset, pconfig)
    # <<<<

    # ------------ #
    # MAKE FIGURES #
    # ------------ #

    if pconfig.figures_output is True:
        #if plot_against_raw ... (add to pconfig comon)
        dataset_raw=load_netcdf_raw(pconfig).sel(time=slice(dataset.time[0], dataset.time[-1]))
        make_meteoce_figure(
            dataset,
            save_path=pconfig.figures_path,
            show_fig=not pconfig.headless,
            dataset_raw=dataset_raw
        )

    # --------------- #
    # POST-PROCESSING #
    # --------------- #
    l.section("Post-processing")
    l.log("Nothing to do")

    # If needed

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
    if netcdf_raw_exist(pconfig) and pconfig.from_raw is not True:
        dataset = load_netcdf_raw(pconfig)
    else:
        dataset = load_meteoce_data(
            filenames=pconfig.input_files,
            buoy_name=pconfig.buoy_name,
            data_format=pconfig.data_format,
        )
        write_netcdf_raw(dataset=dataset, pconfig=pconfig)


    start_time, start_trim = get_datetime_and_count(pconfig.leading_trim)
    end_time, end_trim = get_datetime_and_count(pconfig.trailing_trim)

    dataset = cut_times(dataset, start_time, end_time)

    dataset = cut_index(dataset=dataset, dim='time', start_trim=start_trim, end_trim=end_trim)

    return dataset


def _compute_pressure_at_sampling_depth(dataset: xr.Dataset, pconfig: ProcessConfig):
    """FIXME maybe add loggings ?"""
    if "lat" in dataset.variables:
        latitude = dataset.lat.data
    elif isinstance(pconfig.platform_metadata.platform.latitude, (int, float)):
        latitude = str(pconfig.platform_metadata.platform.latitude)
    else:
        latitude = 0

    if 'atm_pressure' in dataset.variables:
        pres = dataset.atm_pressure.pint.quantify().pint.to('dbar').pint.dequantify().values - 10.1325
    else:
        pres = np.zeros(dataset.time.shape)

    if pconfig.sampling_depth is not None:
        pres += gsw.p_from_z(z=-pconfig.sampling_depth, lat=latitude)

    dataset['pres'] = (['time'], pres, {"units": "dbar"})


def _compute_ctd_potential_density(dataset: xr.Dataset, pconfig: ProcessConfig):
    """Compute potential density as sigma_t:= Density(S,T,P) - 1000

    Density computed using TEOS-10 polynomial (Roquet et al., 2015)

    """

    required_variables = ['temperature', 'salinity']
    if all((var in dataset for var in required_variables)):
        _log_msg = 'Potential density computed using TEOS-10 polynomial. Absolute Salinity, Conservative Temperature'

        if "lon" in dataset.variables:
            longitude = dataset.lon.data
        elif isinstance(pconfig.platform_metadata.platform.latitude, (int, float)):
            longitude = pconfig.platform_metadata.platform.latitude
            _log_msg += f', longitude = {longitude}'
        else:
            longitude = 0
            _log_msg += ', longitude = 0'

        if "lat" in dataset.variables:
            latitude = dataset.lat.data
        elif isinstance(pconfig.platform_metadata.platform.latitude, (int, float)):
            latitude = pconfig.platform_metadata.platform.latitude
            _log_msg += f', latitude = {latitude}'
        else:
            latitude = 0
            _log_msg += ', latitude = 0'

        if 'pres' in dataset.variables:
            pres = dataset.pres.values
        else:
            pres = 0
            _log_msg += f', pressure = 0'

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


def _recompute_speed_course(dataset: xr.Dataset):
    if all(v in dataset for v in ['lon', 'lat']):
        l.log('Platform `speed` and `course` computed from longitude and latitude data.')
        compute_speed_and_course(dataset=dataset)
    else:
        l.warning("Could not compute `speed` and `course`. `lon`/`lat` data not found.")


def _compute_uv_ship(dataset: xr.Dataset):
    if all(x in dataset for x in ('speed', 'course')):
        l.log('Platform `u_ship`, `v_ship` computed from speed and course data.')
        compute_uv_ship(dataset=dataset)

    elif all(v in dataset for v in ['lon', 'lat']):
        l.log('Platform velocities (u_ship, v_ship) computed from longitude and latitude data.')
        compute_speed_and_course(dataset=dataset)
        compute_uv_ship(dataset=dataset)

    else:
        l.warning("Could not compute `u_ship` and `v_ship`. GPS data not found.")



def _quality_control(dataset: xr.Dataset, pconfig: ProcessConfig) -> xr.Dataset:
    """
    Pipe a sub-dataset to adcp quality control for adcp data ?
    Or call the qc function from viking_quality_control. ??
    """
    if pconfig.quality_control is True:
        _meteoce_quality_control(dataset, pconfig)
        _adcp_quality_control(dataset, pconfig)
    else:
        no_meteoce_quality_control(dataset)
        no_adcp_quality_control(dataset, velocity_only=True)

    return dataset


def _meteoce_quality_control(dataset: xr.Dataset, pconfig: ProcessConfig):
    """fixme"""
    spike_tests = {
        var: {
            'threshold': pconfig.__getattribute__(var + "_spike_threshold"),
            'window': pconfig.__getattribute__(var + "_spike_window")}
        for var in SPIKE_QC_VARIABLES
    }
    dataset = meteoce_quality_control(
        dataset,
        regional_outlier=pconfig.regional_outlier,
        absolute_outlier=pconfig.absolute_outlier,
        propagate_flags=pconfig.propagate_flags,
        spike_tests = spike_tests
    )
    return dataset


def _adcp_quality_control(dataset: xr.Dataset, pconfig: ProcessConfig):
    """fixme"""
    adcp_dataset = dataset[set(dataset.variables) & {"u", "v", "w", "e"}]

    adcp_dataset = adcp_dataset.expand_dims(dim={'depth': [0]})

    for var in set(dataset.variables) & {'roll_', 'pitch'}:
        adcp_dataset[var] = dataset[var]

    adcp_dataset.attrs['coord_system'] = "earth"

    adcp_quality_control(
        adcp_dataset,
        amp_th=None,
        corr_th=None,
        pg_th=None,
        roll_th=pconfig.adcp_roll_threshold,
        pitch_th=pconfig.adcp_pitch_threshold,
        horizontal_vel_th=pconfig.adcp_horizontal_velocity_threshold,
        vertical_vel_th=pconfig.adcp_vertical_velocity_threshold,
        error_vel_th=pconfig.adcp_error_velocity_threshold,
        sidelobes_correction=False,
        bottom_depth=None,
        bad_pressure=False,
    )

    adcp_dataset.attrs.pop('coord_system')

    for var in set(adcp_dataset.variables) & {"u_QC", "v_QC", "w_QC"}:
        dataset[var] = adcp_dataset[var].squeeze(['depth'], drop=True)


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
                dataset.dissolved_oxygen.dataset.density
            )
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

            for [key, value] in list(instrument_metadata.items()):
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

    import matplotlib
    matplotlib.use('Qt5Agg')
    import matplotlib.pyplot as plt

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
            odf_output=True,
            merge_output_files=True,
            bodc_name=True, # NOT WORKING FIXME
            force_platform_metadata=None,
            odf_data=False,
            make_figures=True,
            make_log=False
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
            quality_control=True,
        ),

        METEOCE_PROCESSING=dict(
            buoy_name="PMZA-RIKI",
            data_format="viking",
            magnetic_declination=0,
            magnetic_declination_preset=None,
        ),
        WPS_PROCESSING=dict(),
        ADCP_PROCESSING=dict(),
        METEOCE_QUALITY_CONTROL=dict(),
        ADCP_QUALITY_CONTROL=dict(
            horizontal_velocity_threshold=2,
            vertical_velocity_threshold=1,
            error_velocity_threshold=1,
            roll_threshold=10,
            pitch_threshold=10,
        )
    )

    process_meteoce(_config)

    ds = xr.open_dataset(out_path)

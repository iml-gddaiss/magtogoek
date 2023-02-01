"""
This script has to functions to process and quick process viking buoy data.
These functions are called by the app command `process` and `quick viking`.

Date: July 25 2022
Made by: jeromejguay

Notes
-----
Missing BODC: 'chlorophyle', 'fdom', 'par'.

At the moment for some of the data correction. If the variable used has nans, the corrected value will (should) be a nan as well.
Therefore, if a variable is present but all the values are nan, the corrected data will also be all nan.

Maybe quality control should be done before and the transformation should check the flag values.

"""

import getpass

import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
from typing import *

from magtogoek import logger as l
from magtogoek import TERMINAL_WIDTH
from magtogoek.process_common import BaseProcessConfig, add_global_attributes, write_log, write_netcdf, \
    add_processing_timestamp, clean_dataset_for_nc_output, format_data_encoding, format_variables_names_and_attributes, \
    add_navigation, save_variables_name_for_odf_output
from magtogoek.attributes_formatter import (
    compute_global_attrs, format_variables_names_and_attributes,
)
from magtogoek.ctd.correction import RINKO_COEFFS_KEYS, dissolved_oxygen_rinko_correction, voltEXT_from_pHEXT, \
    pHEXT_from_voltEXT, compute_density
from magtogoek.navigation import load_navigation
from magtogoek.tools import rotate_2d_vector, north_polar2cartesian
# from magtogoek.platforms import _add_platform
from magtogoek.utils import ensure_list_format
from magtogoek.viking.loader import load_meteoce_data
# from magtogoek.viking.odf_exporter import make_odf
from magtogoek.viking.quality_control import meteoce_quality_control, no_meteoce_quality_control

# import click

l.get_logger("viking_processing")

STANDARD_GLOBAL_ATTRIBUTES = {
    "sensor_type": "viking_buoy",
    "featureType": "timeSeriesProfile",
    "data_type": "meteoce",  # TODO CHECK IF ITS RIGHTS
    "data_subtype": "BUOY",
    "source": None,

}

VARIABLES_TO_DROP = ['ph_temperature', 'wind_direction_max', 'speed', 'course', 'magnetic_declination']

GLOBAL_ATTRS_TO_DROP = [
    "sensor_type",
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

VAR_TO_ADD_SENSOR_TYPE = []

#TIME_ATTRS = {"cf_role": "profile_id"}

#TIME_ENCODING = {
    # "units": "seconds since 1970-1-1 00:00:00Z",
    # "calendar": "gregorian",
    # "_FillValue": None,
# }
#TIME_STRING_ENCODING = {"dtype": "S1"}

#DATE_STRING_FILL_VALUE = "17-NOV-1858 00:00:00.00"  # filled value used by ODF format
#QC_FILL_VALUE = 127
#QC_ENCODING = {"dtype": "int8", "_FillValue": QC_FILL_VALUE}

#DATA_FILL_VALUE = -9999.0
#DATA_ENCODING = {"dtype": "float32", "_FillValue": DATA_FILL_VALUE}


class ProcessConfig(BaseProcessConfig):
    # PROCESSING
    buoy_name: str = None
    data_format: str = None
    sensor_depth: float = None
    leading_trim: Union[int, str] = None
    trailing_trim: Union[int, str] = None
    magnetic_declination: float = None
    magnetic_declination_preset: float = None

    # CTD
    compute_density: bool = None
    ph_correction: bool = None
    ph_coeffs: Tuple[float] = None  # psal, k0, k2
    oxy_correction: bool = None
    oxy_coeffs: Tuple[float] = None

    # ADCP
    motion_correction_mode: str = None

    # QUALITY_CONTROL
    quality_control: bool = None

    def __init__(self, config_dict: dict = None):
        super().__init__(config_dict)
        self.variables_to_add_sensor_type = VAR_TO_ADD_SENSOR_TYPE
        self.variables_to_drop = VARIABLES_TO_DROP
        self.global_attributes_to_drop = GLOBAL_ATTRS_TO_DROP


def process_viking(config: dict, drop_empty_attrs: bool = False, headless: bool = False):
    """Process Viking data with parameters from a config file.

    If `pconfig.merge_output_files` is False, each input file is process individually.

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

    if pconfig.merge_output_files:
        pconfig.resolve_outputs()
        return _process_viking_data(pconfig)  # FIXME
    else:
        input_files = list(pconfig.input_files)
        odf_output = pconfig.odf_output
        netcdf_output = pconfig.netcdf_output
        event_qualifier1 = pconfig.metadata['event_qualifier1']
        for count, filename in enumerate(input_files):
            pconfig.input_files = [filename]
            # If the user set path ...
            if isinstance(netcdf_output, str):
                # If the path is a filename ...
                if not Path(netcdf_output).is_dir():
                    # An incrementing suffix is added to the filename
                    pconfig.netcdf_output = str(Path(netcdf_output).with_suffix("")) + f"_{count}"

            # If the user set path ...
            if isinstance(odf_output, str):
                # If the path is a filename ...
                if not Path(odf_output).is_dir():
                    # An incrementing suffix is added to the filename
                    pconfig.odf_output = str(Path(odf_output).with_suffix("")) + f"_{count}"
                # If it's a directory
                else:
                    # An incrementing suffix is added to the event_qualifier that builds the filename
                    # PREVENTS FROM OVERWRITING THE SAME FILE
                    pconfig.metadata[
                        'event_qualifier1'] = event_qualifier1 + f"_{Path(filename).name}"  # PREVENTS FROM OVERWRITING THE SAME FILE
            elif odf_output is True:
                # An incrementing suffix is added to the event_qualifier that builds the filename
                # PREVENTS FROM OVERWRITING THE SAME FILE
                pconfig.metadata['event_qualifier1'] = event_qualifier1 + f"_{Path(filename).name}"

            pconfig.resolve_outputs()

            _process_viking_data(pconfig)


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
        _compute_ctdo_density(dataset)

    if all(x in dataset for x in ('speed', 'course')):
        _compute_uv_ship(dataset)

    # ----------- #
    # CORRECTION  #
    # ----------- #

    l.section("Data Correction")

    if 'dissolved_oxygen' in dataset:
        _correction_dissolved_oxygen_rinko(dataset, pconfig)

    if 'ph' in dataset:
        _correct_ph_for_salinity(dataset, pconfig)

    # MAGNETIC DECLINATION SHOULD BE ALREADY CORRECTED FOR VIKING

    # --------------- #
    # QUALITY CONTROL #
    # --------------- #

    # TODO

    if pconfig.quality_control:
        _quality_control(dataset, pconfig)
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
        variable_to_add_sensor_type=pconfig.variables_to_add_sensor_type,
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

    return dataset # FIXME to remove


def _load_viking_data(pconfig: ProcessConfig):
    dataset = load_meteoce_data(
        filenames=pconfig.input_files,
        buoy_name=pconfig.buoy_name,
        data_format=pconfig.data_format,
    )
    return dataset


######### VIKING ############ -> CTD ... tools ?
def _compute_ctdo_density(dataset: xr.Dataset):
    """Compute density as sigma_t:= Density(S,T) - 1000

    """
    try:
        # COMPUTE DENSITY USES EOS. is that what we want ? FIXME
        dataset['density'] = (['time'], np.asarray(compute_density(dataset) - 1000))
        l.log(f'Density was computed.')
    except ValueError:
        required_variables = ['temperature', 'salinity']
        l.warning(
            f'density computation aborted. One of more variables in {required_variables} was missing.')


######### VIKING ############
def _correct_ph_for_salinity(dataset: xr.Dataset, pconfig: ProcessConfig):
    """Ph correction for salinity.

    ph_temperature (temperature is used to find the voltage measured by the probe, but the ctd
    temperature is used to find the ph.

    TODO TEST THE DIFFERENCE BETWEEN USING PH AND TEMPERATURE_PH

    Notes
    -----
    The algorithm used were not tested (As of December 6 2022)
    """
    required_variables = ['ph_temperature', 'temperature', 'salinity']
    if pconfig.ph_coeffs is not None:
        if all((var in dataset for var in required_variables)): #FIXME MAKE A FUNCITON IN ctd/correction.py
            [psal, k0, k2] = pconfig.ph_coeffs
            volt = voltEXT_from_pHEXT(temp=dataset['ph_temperature'], psal=psal, k0=k0, k2=k2)
            ph = pHEXT_from_voltEXT(temp=dataset['temperature'], psal=dataset['salinity'], volt=volt, k0=k0, k2=k2)
            dataset['ph'].values = ph
            l.log('pH correction was carried out')
        else:
            l.warning(f'pH correction aborted. One of more variables in {required_variables} was missing.')
    else:
        l.warning(f'pH correction aborted. `ph_coeffs` were not provided.')


######### VIKING ############
def _correction_dissolved_oxygen_rinko(dataset: xr.Dataset, pconfig: ProcessConfig):
    """Dissolved oxygen correction for salinity, temperature and pressure.
    Atmospheric pressure is used since the probe is on a buoy. TODO CHECK IF THIS IS OK
    """
    required_variables = ['dissolved_oxygen', 'temperature', 'salinity', 'atm_pressure']
    if pconfig.oxy_coeffs is not None:
        coeffs = dict(zip(RINKO_COEFFS_KEYS, pconfig.oxy_coeffs))
        if all((var in dataset for var in required_variables)):
            dataset['dissolved_oxygen'].values = dissolved_oxygen_rinko_correction(
                doxy=dataset['dissolved_oxygen'],
                temp=dataset['temperature'],
                pres=dataset['atm_pressure'],
                psal=dataset['salinity'],
                coeffs=coeffs
            )
            l.log(f'Dissolved oxygen correction (Rinko) was carried out')
        else:
            l.warning(f'Dissolved oxygen correction (Rinko) aborted. One of more variables in {required_variables} was missing.')
    else:
        l.warning(
            f'Dissolved oxygen correction (Rinko) aborted. `oxy_coeffs` were not provided.')


def _compute_uv_ship(dataset: xr.Dataset): # FIXME put in navigation or does it already exist ?
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


# def _load_navigation(dataset: xr.Dataset, navigation_files: str):
#     """Load navigation data from nmea, gpx or netcdf files.
#
#     Returns the dataset with the added navigation data. Data from the navigation file
#     are interpolated on the dataset time vector.
#
#     Parameters
#     ----------
#     dataset :
#         Dataset to which add the navigation data.
#
#     navigation_files :
#         nmea(ascii), gpx(xml) or netcdf files containing the navigation data. For the
#         netcdf file, variable must be `lon`, `lat` and the coordinates `time`.
#
#     Notes
#     -----
#         Using the magtogoek function `mtgk compute nav`, u_ship, v_ship can be computed from `lon`, `lat`
#     data to correct the data for the platform motion by setting the config parameter `m_corr` to `nav`.
#     """
#     nav_ds = load_navigation(navigation_files)
#     if nav_ds is not None:
#         if nav_ds.attrs['time_flag'] is True:
#             nav_ds = nav_ds.interp(time=dataset.time)
#             if nav_ds.attrs['lonlat_flag']:
#                 dataset['lon'] = nav_ds['lon']
#                 dataset['lat'] = nav_ds['lat']
#                 l.log("Platform GPS data loaded.")
#             if nav_ds.attrs['uv_ship_flag']:
#                 dataset['u_ship'] = nav_ds['u_ship']
#                 dataset['v_ship'] = nav_ds['v_ship']
#                 l.log("Platform velocity data loaded.")
#             nav_ds.close()
#             return dataset
#     l.warning('Could not load navigation data file.')
#     return dataset

#
# def _apply_magnetic_correction(dataset: xr.Dataset, magnetic_declination: float):
#     """Transform velocities (u,v, bt_u,bt_v, u_ship, v_ship) to true north and east.
#
#     Rotates velocities vector clockwise by `magnetic_declination` angle effectively
#     rotating the frame fo reference by the `magnetic_declination` anti-clockwise.
#     Corrects the heading with the `magnetic_declination`:
#
#     Parameters
#     ----------
#     dataset :
#       dataset optional variables: (u, v), (bt_u, bt_v), (u_ship, v_ship).
#     magnetic_declination :
#         angle in decimal degrees measured in the geographic frame of reference.
#     """
#
#     if all(v in dataset for v in ["u", "v"]):
#         dataset.u.values, dataset.v.values = rotate_2d_vector(
#             dataset.u, dataset.v, -magnetic_declination
#         )
#         l.log(f"Velocities transformed to true north and true east.")
#     if all(v in dataset for v in ["bt_u", "bt_v"]):
#         dataset.bt_u.values, dataset.bt_v.values = rotate_2d_vector(
#             dataset.bt_u, dataset.bt_v, -magnetic_declination
#         )
#         l.log(f"Bottom velocities transformed to true north and true east.")
#
#     if all(v in dataset for v in ["u_ship", "v_ship"]):
#         dataset.u_ship.values, dataset.v_ship.values = rotate_2d_vector(
#             dataset.u_ship, dataset.v_ship, -magnetic_declination
#         )
#         l.log(f"Platform velocities transformed to true north and true east.")
#
#
# def _drop_variables(dataset):
#     """Drop variables in VARIABLES_TO_DROP from dataset"""
#     for var in VARIABLES_TO_DROP:
#         if var in dataset.variables:
#             dataset = dataset.drop_vars([var])
#     return dataset
#
#
# def _drop_global_attributes(dataset: xr.Dataset):
#     """Drop global attributes in GLOBAL_ATTRS_TO_DROP from dataset"""
#     for attr in GLOBAL_ATTRS_TO_DROP:
#         if attr in dataset.attrs:
#             del dataset.attrs[attr]
#     return dataset
#
#
# def _handle_null_global_attributes(dataset: xr.Dataset, pconfig: ProcessConfig):
#     """Drop or set to empty string global attributes depending
#     on the value of pconfig.drop_empty_attrs"""
#     for attr in list(dataset.attrs.keys()):
#         if not dataset.attrs[attr]:
#             if pconfig.drop_empty_attrs is True:
#                 del dataset.attrs[attr]
#             else:
#                 dataset.attrs[attr] = ""
#     return dataset
#
#
# def _resolve_outputs(pconfig: ProcessConfig):
#     """ Figure out the outputs to make and their path.
#     """
#     input_path = pconfig.input_files[0]
#     default_path = Path(input_path).parent
#     default_filename = Path(input_path).name
#
#     if not pconfig.odf_output and not pconfig.netcdf_output:
#         pconfig.netcdf_output = True
#
#     default_path, default_filename = _netcdf_output_handler(pconfig, default_path, default_filename)
#
#     default_path, default_filename = _odf_output_handler(pconfig, default_path, default_filename)
#
#     _figure_output_handler(pconfig, default_path, default_filename)
#
#     pconfig.log_path = str(default_path.joinpath(default_filename))
#
#
# def _netcdf_output_handler(pconfig: ProcessConfig, default_path: Path, default_filename: Path) -> Tuple[Path, Path]:
#     if isinstance(pconfig.netcdf_output, bool):
#         if pconfig.netcdf_output is True:
#             pconfig.netcdf_path = str(default_path.joinpath(default_filename))
#     elif isinstance(pconfig.netcdf_output, str):
#         _netcdf_output = Path(pconfig.netcdf_output)
#         if Path(_netcdf_output.name) == _netcdf_output:
#             netcdf_path = default_path.joinpath(_netcdf_output).resolve()
#         elif _netcdf_output.absolute().is_dir():
#             netcdf_path = _netcdf_output.joinpath(default_filename)
#         elif _netcdf_output.parent.is_dir():
#             netcdf_path = _netcdf_output
#         else:
#             raise ValueError(f'Path path to {_netcdf_output} does not exists.')
#         default_path = netcdf_path.parent
#         default_filename = netcdf_path.stem
#         pconfig.netcdf_path = str(netcdf_path)
#         pconfig.netcdf_output = True
#
#     return default_path, default_filename
#
#
# def _odf_output_handler(pconfig: ProcessConfig, default_path: Path, default_filename: Path) -> Tuple[Path, Path]:
#     if isinstance(pconfig.odf_output, bool):
#         if pconfig.odf_output is True:
#             pconfig.odf_path = str(default_path)
#     elif isinstance(pconfig.odf_output, str):
#         _odf_output = Path(pconfig.odf_output)
#         if Path(_odf_output.name) == _odf_output:
#             _odf_path = default_path.joinpath(_odf_output).resolve()
#         elif _odf_output.is_dir():
#             _odf_path = _odf_output
#         elif _odf_output.parent.is_dir():
#             _odf_path = _odf_output
#         else:
#             raise ValueError(f'Path to {_odf_output} does not exists.')
#
#         pconfig.odf_path = str(_odf_path)
#         pconfig.odf_output = True
#
#         if not pconfig.netcdf_output:
#             default_path = _odf_path.parent
#             default_filename = _odf_path.stem
#
#     return default_path, default_filename
#
#
# def _figure_output_handler(pconfig: ProcessConfig, default_path: Path, default_filename: Path):
#     if isinstance(pconfig.make_figures, bool):
#         if pconfig.make_figures is True:
#             pconfig.figures_output = True
#             if pconfig.headless is True:
#                 pconfig.figures_path = str(default_path.joinpath(default_filename))
#     elif isinstance(pconfig.make_figures, str):
#         _figures_output = Path(pconfig.make_figures)
#         if Path(_figures_output.name) == _figures_output:
#             _figures_path = default_path.joinpath(_figures_output).resolve()
#         elif _figures_output.is_dir():
#             _figures_path = _figures_output.joinpath(default_filename)
#         elif _figures_output.parent.is_dir():
#             _figures_path = _figures_output
#         else:
#             raise ValueError(f'Path to {_figures_output} does not exists.')
#
#         pconfig.figures_path = str(_figures_path)
#         pconfig.figures_output = True


if __name__ == "__main__":
    file_path = '/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat'
    out_path = '/home/jeromejguay/Desktop/viking_test.nc'
    config = dict(
        HEADER=dict(
            sensor_type="viking_buoy",
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
            event_qualifier1="meteoc"
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

    ds = process_viking(config)

    print(list(ds.variables))
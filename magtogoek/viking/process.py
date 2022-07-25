"""
This script has to functions to process and quick process viking buoy data.
These functions are called by the app command `process` and `quick viking`.

Date: July 25 2022
Made by: jeromejguay

METEOCE BODC:
        Time                                                 : SYTM_01 : SDN:P01::
        Longitude (East +ve)                                 : LOND_01 : SDN:P01::
        Latitude (North +ve)                                 : LATD_01 : SDN:P01::
        Horizontal Wind Speed                                : WSPD_01 : SDN:P01::EWSBZZ01
        Gust Wind Speed                                      : GSPD_01 : SDN:P01::EGTSZZ01
        Wind Direction relative to North (T)                 : WDIR_01 : SDN:P01::EWDAZZ01
        Dry Bulb Temperature                                 : DRYT_01 : SDN:P01::CTMPZZ01
        Relative Humidity                                    : RELH_01 : SDN:P01::CRELZZ01
        Atmospheric pressure                                 : ATMP_01 : SDN:P01::CAPHZZ01
        Temperature (1990 scale)                             : TE90_01 : SDN:P01::TEMPPR01
        Electrical Conductivity                              : CNDC_01 : SDN:P01::CNDCZZ01
        Practical Salinity                                   : PSAL_01 : SDN:P01::PSLTZZ01
        Sea Density                                          : DENS_01 : SDN:P01::SIGTEQ01
        Hydrogen Ion Concentration (pH)                      : PHPH_01 : SDN:P01::PHXXZZXX
        Fluorescence                                         : FLOR_01 : SDN:P01::FLUOZZZZ
        Partial pressure of carbon dioxide in the atmosphere : ACO2_01 : SDN:P01::ACO2XXXX
        Partial pressure of carbon dioxide in the water body : PCO2_01 : SDN:P01::PCO2XXXX
        Wave mean height                                     : VRMS_01 : SDN:P01::GAVHZZ01
        Wave maximum height                                  : VMXL_01 : SDN:P01::GCMXZZ01
        Wave period                                          : VTCA_01 : SDN:P01::GTAMZZ01
        u
        v
        w
        e
        bt_u
        bt_v
        bt_w
        bt_e
TODO DO SOME LOGGINS
"""

import numpy as np
import pandas as pd
import xarray as xr
import getpass
from pathlib import Path
from typing import *
import click

from magtogoek.navigation import load_navigation
from magtogoek.platforms import _add_platform
from magtogoek.utils import Logger, ensure_list_format, json2dict

from magtogoek.attributes_formatter import (
    compute_global_attrs, format_variables_names_and_attributes, _add_data_min_max_to_var_attrs)

from magtogoek.viking.loader import load_meteoce_data
from magtogoek.viking.odf_exporter import make_odf
from magtogoek.viking.quality_control import meteoce_quality_control, no_meteoce_quality_control

from magtogoek.tools import rotate_2d_vector

TERMINAL_WIDTH = 80

STANDARD_ADCP_GLOBAL_ATTRIBUTES = {
    "sensor_type": "viking_buoy",
    "featureType": "timeSeriesProfile",
}
DEFAULT_CONFIG_ATTRIBUTES = {
    "date_created": pd.Timestamp.now().strftime("%Y-%m-%d"),
    "publisher_name": getpass.getuser(),
    "source": "viking_buoy",
}
VARIABLES_TO_DROP = []
GLOBAL_ATTRS_TO_DROP = []

CONFIG_GLOBAL_ATTRS_SECTIONS = ["NETCDF_CF", "PROJECT", "CRUISE", "GLOBAL_ATTRIBUTES"]

PLATFORM_TYPES = ['buoy']
DEFAULT_PLATFORM_TYPE = "buoy"
DATA_TYPE = 'meteoce'  # TODO VERIFY
DATA_SUBTYPE = 'BUOY'

P01_CODES = dict(
    wind_mean="EWSBZZ01",
    wind_direction_mean="EGTSZZ01",
    wind_max="EWDAZZ01",
    atm_temperature="CTMPZZ01",
    atm_humidity="CRELZZ01",
    atm_pressure="CAPHZZ01",
    temperature="TEMPPR01",
    conductivity="CNDCZZ01",
    salinity="PSLTZZ01",
    density="SIGTEQ01",
    ph="PHXXZZXX",
    fluorescence="FLUOZZZZ",
    co2_a="ACO2XXXX",
    co2_w="PCO2XXXX",
    wave_mean_height="GAVHZZ01",
    wave_maximal_height="GCMXZZ01",
    wave_period="GTAMZZ01",
    u="LCEWAP01",
    v="LCNSAP01",
    w="LRZAAP01",
    e="LERRAP01",
    u_QC="LCEWAP01_QC",
    v_QC="LCNSAP01_QC",
    w_QC="LRZAAP01_QC",
    pg="PCGDAP01",
    pg1="PCGDAP00",
    pg2="PCGDAP02",
    pg3="PCGDAP03",
    pg4="PCGDAP04",
    corr1="CMAGZZ01",
    corr2="CMAGZZ02",
    corr3="CMAGZZ03",
    corr4="CMAGZZ04",
    amp1="TNIHCE01",
    amp2="TNIHCE02",
    amp3="TNIHCE03",
    amp4="TNIHCE04",
    bt_u="APEWBT01",
    bt_v="APNSBT01",
    bt_w="APZABT01",
    bt_e="APERBT01",
)

VAR_TO_ADD_SENSOR_TYPE = []

TIME_ATTRS = {"cf_role": "profile_id"}

TIME_ENCODING = {
    "units": "seconds since 1970-1-1 00:00:00Z",
    "calendar": "gregorian",
    "_FillValue": None,
}
TIME_STRING_ENCODING = {"dtype": "S1"}
DEPTH_ENCODING = {
    "_FillValue": -9999.0,
    "dtype": "float32",
}

DATE_STRING_FILL_VALUE = "17-NOV-1858 00:00:00.00"  # filled value used by ODF format
QC_FILL_VALUE = 127
QC_ENCODING = {"dtype": "int8", "_FillValue": QC_FILL_VALUE}

DATA_FILL_VALUE = -9999.0
DATA_ENCODING = {"dtype": "float32", "_FillValue": DATA_FILL_VALUE}

l = Logger()


class ProcessConfig:
    sensor_type: str = None
    platform_type: str = None
    input_files: str = None
    platform_file: str = None
    platform_id: str = None

    netcdf_output: Union[str, bool] = None
    odf_output: Union[str, bool] = None

    navigation_file: str = None
    leading_trim: Union[int, str] = None
    trailing_trim: Union[int, str] = None
    magnetic_declination: float = None

    quality_control: bool = None

    # motion_correction_mode: str = None
    merge_output_files: bool = None
    bodc_name: bool = None
    # force_platform_metadata: bool = None

    make_figures: bool = None
    make_log: bool = None
    odf_data: str = None
    metadata: dict = {}
    # platform_metadata: dict = {}

    netcdf_path: str = None
    odf_path: str = None
    log_path: str = None
    figures_path: str = None
    figures_output: bool = None

    drop_empty_attrs: bool = False
    headless: bool = False

    def __init__(self, config_dict: dict = None):
        self.metadata: dict = {}
        self.platform_metadata: dict = {}
        self.platform_type = DEFAULT_PLATFORM_TYPE

        if config_dict is not None:
            self._load_config_dict(config_dict)

        if isinstance(self.input_files, str):
            self.input_files = ensure_list_format(self.input_files)

        if len(self.input_files) == 0:
            raise ValueError("No adcp file was provided in the configfile.")

        self._get_platform_metadata()
        self.platform_type = self.platform_metadata["platform"]['platform_type']

    def _load_config_dict(self, config: dict) -> dict:
        """Split and flattens"""
        for section, options in config.items():
            if section in CONFIG_GLOBAL_ATTRS_SECTIONS:
                for option in options:
                    self.metadata[option] = config[section][option]
            else:
                for option in options:
                    self.__dict__[option] = config[section][option]

    def _get_platform_metadata(self):
        pass

    def resolve_outputs(self):
        _resolve_outputs(self)


def process_viking(config: dict,
                   drop_empty_attrs: bool = False,
                   headless: bool = False):
    pconfig = ProcessConfig(config)
    pconfig.drop_empty_attrs = drop_empty_attrs
    pconfig.headless = headless
    pconfig.resolve_outputs()
    if pconfig.merge_output_files:
        _process_viking_data(pconfig)
    else:
        netcdf_output = pconfig.netcdf_output
        input_files = pconfig.input_files
        for filename, count in zip(input_files, range(len(input_files))):
            if netcdf_output:
                if isinstance(netcdf_output, bool):
                    pconfig.netcdf_output = filename
                else:
                    pconfig.netcdf_output = Path(netcdf_output).absolute().resolve()
                    if pconfig.netcdf_output.is_dir():
                        pconfig.netcdf_output = str(pconfig.netcdf_output.joinpath(filename))
                    else:
                        pconfig.netcdf_output = str(pconfig.netcdf_output.with_suffix("")) + f"_{count}"
            pconfig.input_files = [filename]

            _process_viking_data(pconfig)


def _process_viking_data(pconfig: ProcessConfig):
    """

    """
    l.reset()
    # ------------------- #
    # LOADING VIKING DATA #
    # ------------------- #

    dataset = _load_viking_data(pconfig)

    # ----------------------------------------- #
    # ADDING THE NAVIGATION DATA TO THE DATASET #
    # ----------------------------------------- #
    if pconfig.navigation_file:
        l.section("Navigation data")
        dataset = _load_navigation(dataset, pconfig.navigation_file)

    # ----------------------------- #
    # ADDING SOME GLOBAL ATTRIBUTES #
    # ----------------------------- #

    dataset = dataset.assign_attrs(STANDARD_ADCP_GLOBAL_ATTRIBUTES)

    dataset.attrs["data_type"] = DATA_TYPE
    dataset.attrs["data_subtype"] = DATA_SUBTYPE

    # if pconfig.platform_metadata["platform"]["longitude"]:
    #     dataset.attrs["longitude"] = pconfig.platform_metadata["platform"]["longitude"]
    # if pconfig.platform_metadata["platform"]["latitude"]:
    #     dataset.attrs["latitude"] = pconfig.platform_metadata["platform"]["latitude"]

    compute_global_attrs(dataset)

    dataset = dataset.assign_attrs(pconfig.metadata)

    _set_platform_metadata(dataset, pconfig)

    if not dataset.attrs["source"]:
        dataset.attrs["source"] = pconfig.platform_type

    # --------------- #
    # QUALITY CONTROL #
    # --------------- #

    dataset.attrs["logbook"] += l.logbook

    if pconfig.quality_control:
        _quality_control(dataset, pconfig)
    else:
        no_meteoce_quality_control(dataset)

    l.reset()

    # ----------------------------------- #
    # CORRECTION FOR MAGNETIC DECLINATION #
    # ----------------------------------- #

    l.section("Data transformation")

    if pconfig.magnetic_declination:
        angle = pconfig.magnetic_declination
        _apply_magnetic_correction(dataset, angle)
        dataset.attrs["magnetic_declination"] = pconfig.magnetic_declination
        l.log(f"Absolute magnetic declination: {dataset.attrs['magnetic_declination']} degree east.")

    # ------------- #
    # DATA ENCODING #
    # ------------- #
    _format_data_encoding(dataset)

    # -------------------- #
    # VARIABLES ATTRIBUTES #
    # -------------------- #
    dataset.attrs['bodc_name'] = pconfig.bodc_name
    dataset.attrs["VAR_TO_ADD_SENSOR_TYPE"] = VAR_TO_ADD_SENSOR_TYPE
    dataset.attrs["P01_CODES"] = {
        **P01_CODES,
    }
    dataset.attrs["variables_gen_name"] = [var for var in dataset.variables]  # For Odf outputs

    l.section("Variables attributes")
    dataset = format_variables_names_and_attributes(dataset)

    # --------------------------- #
    # ADDING OF GLOBAL ATTRIBUTES #
    # ----------------------------#

    if not dataset.attrs["date_created"]:
        dataset.attrs["date_created"] = pd.Timestamp.now().strftime("%Y-%m-%d")

    dataset.attrs["date_modified"] = pd.Timestamp.now().strftime("%Y-%m-%d")

    dataset.attrs["logbook"] += l.logbook

    dataset.attrs["history"] = dataset.attrs["logbook"]
    del dataset.attrs["logbook"]

    if "platform_name" in dataset.attrs:
        dataset.attrs["platform"] = dataset.attrs.pop("platform_name")

    # ----------- #
    # ODF OUTPUTS #
    # ----------- #

    l.section("Output")
    if pconfig.odf_output is True:
        if pconfig.odf_data is None:
            pconfig.odf_data = 'both'
        #odf_data = {'both': ['VEL', 'ANC'], 'vel': ['VEL'], 'anc': ['ANC']}[pconfig.odf_data]
        odf_data = "METEOCE" #?
        for qualifier in odf_data:
            _ = make_odf(
                dataset=dataset,
                platform_metadata=pconfig.platform_metadata,
                config_attrs=pconfig.metadata,
                bodc_name=pconfig.bodc_name,
                event_qualifier2=qualifier,
                output_path=pconfig.odf_path,
            )

        # ------------------------------------ #
        # FORMATTING DATASET FOR NETCDF OUTPUT #
        # ------------------------------------ #
    for var in VARIABLES_TO_DROP:
        if var in dataset.variables:
            dataset = dataset.drop_vars([var])

    for attr in GLOBAL_ATTRS_TO_DROP:
        if attr in dataset.attrs:
            del dataset.attrs[attr]

    for attr in list(dataset.attrs.keys()):
        if not dataset.attrs[attr]:
            if pconfig.drop_empty_attrs is True:
                del dataset.attrs[attr]
            else:
                dataset.attrs[attr] = ""

        # ---------- #
        # NC OUTPUTS #
        # ---------- #
    if pconfig.netcdf_output is True:
        netcdf_path = Path(pconfig.netcdf_path).with_suffix('.nc')
        dataset.to_netcdf(netcdf_path)
        l.log(f"netcdf file made -> {netcdf_path.resolve()}")

    if pconfig.make_log is True:
        log_path = Path(pconfig.log_path).with_suffix(".log")
        with open(log_path, "w") as log_file:
            log_file.write(dataset.attrs["history"])
            print(f"log file made -> {log_path.resolve()}")

    click.echo(click.style("=" * TERMINAL_WIDTH, fg="white", bold=True))

def _load_viking_data():
    pass


def _set_platform_metadata():
    pass


def _quality_control(dataset: xr.Dataset, pconfig: ProcessConfig):
    dataset = meteoce_quality_control(dataset)
    return dataset


def _load_navigation(dataset: xr.Dataset, navigation_files: str):
    """Load navigation data from nmea, gpx or netcdf files.

    Returns the dataset with the added navigation data. Data from the navigation file
    are interpolated on the dataset time vector.

    Parameters
    ----------
    dataset :
        Dataset to which add the navigation data.

    navigation_files :
        nmea(ascii), gpx(xml) or netcdf files containing the navigation data. For the
        netcdf file, variable must be `lon`, `lat` and the coordinates `time`.

    Notes
    -----
        Using the magtogoek function `mtgk compute nav`, u_ship, v_ship can be computed from `lon`, `lat`
    data to correct the data for the platform motion by setting the config parameter `m_corr` to `nav`.
    """
    nav_ds = load_navigation(navigation_files)
    if nav_ds is not None:
        if nav_ds.attrs['time_flag'] is True:
            nav_ds = nav_ds.interp(time=dataset.time)
            if nav_ds.attrs['lonlat_flag']:
                dataset['lon'] = nav_ds['lon']
                dataset['lat'] = nav_ds['lat']
                l.log("Platform GPS data loaded.")
            if nav_ds.attrs['uv_ship_flag']:
                dataset['u_ship'] = nav_ds['u_ship']
                dataset['v_ship'] = nav_ds['v_ship']
                l.log("Platform velocity data loaded.")
            nav_ds.close()
            return dataset
    l.warning('Could not load navigation data file.')
    return dataset


def _format_data_encoding(dataset: xr.Dataset):
    """Format data encoding with default value in module."""
    l.section("Data Encoding")
    for var in dataset.variables:
        if var == "time":
            dataset.time.encoding = TIME_ENCODING
        elif "_QC" in var:
            dataset[var].values = dataset[var].values.astype("int8")
            dataset[var].encoding = QC_ENCODING
        elif var == "time_string":
            dataset[var].encoding = TIME_STRING_ENCODING
        else:
            dataset[var].encoding = DATA_ENCODING

    l.log(f"Data _FillValue: {DATA_FILL_VALUE}")
    l.log(f"Ancillary Data _FillValue: {QC_FILL_VALUE}")


def _apply_magnetic_correction(dataset: xr.Dataset, magnetic_declination: float):  # PUT IN ADCP UTILS
    """Transform velocities and heading to true north and east.

    Rotates velocities vector clockwise by `magnetic_declination` angle effectively
    rotating the frame fo reference by the `magnetic_declination` anti-clockwise.
    Corrects the heading with the `magnetic_declination`:

    Equation for the heading: (heading + 180 + magnetic_declination) % 360 - 180
        [-180, 180[ -> [0, 360[ -> [MD, 360+MD[
        -> [MD, 360+MD[ -> [0, 360[ -> [-180, 180[

    Parameters
    ----------
    dataset :
      dataset containing variables (u, v) (required) and (bt_u, bt_v) (optional).
    magnetic_declination :
        angle in decimal degrees measured in the geographic frame of reference.
    """

    dataset.u.values, dataset.v.values = rotate_2d_vector(
        dataset.u, dataset.v, -magnetic_declination
    )
    l.log(f"Velocities transformed to true north and true east.")
    if all(v in dataset for v in ["bt_u", "bt_v"]):
        dataset.bt_u.values, dataset.bt_v.values = rotate_2d_vector(
            dataset.bt_u, dataset.bt_v, -magnetic_declination
        )
        l.log(f"Bottom velocities transformed to true north and true east.")

    # heading goes from -180 to 180
    if "heading" in dataset:
        dataset.heading.values = (
                                         dataset.heading.data + 180 + magnetic_declination
                                 ) % 360 - 180
        l.log(f"Heading transformed to true north.")


def _resolve_outputs(pconfig: ProcessConfig):
    """ Figure out the outputs to make and their path.
    """
    input_path = pconfig.input_files[0]
    default_path = Path(input_path).parent
    default_filename = Path(input_path).name

    if not pconfig.odf_output and not pconfig.netcdf_output:
        pconfig.netcdf_output = True

    default_path, default_filename = _netcdf_output_handler(pconfig, default_path, default_filename)

    default_path, default_filename = _odf_output_handler(pconfig, default_path, default_filename)

    _figure_output_handler(pconfig, default_path, default_filename)

    pconfig.log_path = str(default_path.joinpath(default_filename))


def _netcdf_output_handler(pconfig: ProcessConfig, default_path: Path, default_filename: Path) -> Tuple[Path, Path]:
    if isinstance(pconfig.netcdf_output, bool):
        if pconfig.netcdf_output is True:
            pconfig.netcdf_path = str(default_path.joinpath(default_filename))
    elif isinstance(pconfig.netcdf_output, str):
        _netcdf_output = Path(pconfig.netcdf_output)
        if Path(_netcdf_output.name) == _netcdf_output:
            netcdf_path = default_path.joinpath(_netcdf_output).resolve()
        elif _netcdf_output.absolute().is_dir():
            netcdf_path = _netcdf_output.joinpath(default_filename)
        elif _netcdf_output.parent.is_dir():
            netcdf_path = _netcdf_output
        else:
            raise ValueError(f'Path path to {_netcdf_output} does not exists.')
        default_path = netcdf_path.parent
        default_filename = netcdf_path.stem
        pconfig.netcdf_path = str(netcdf_path)
        pconfig.netcdf_output = True

    return default_path, default_filename


def _odf_output_handler(pconfig: ProcessConfig, default_path: Path, default_filename: Path) -> Tuple[Path, Path]:
    if isinstance(pconfig.odf_output, bool):
        if pconfig.odf_output is True:
            pconfig.odf_path = str(default_path)
    elif isinstance(pconfig.odf_output, str):
        _odf_output = Path(pconfig.odf_output)
        if Path(_odf_output.name) == _odf_output:
            _odf_path = default_path.joinpath(_odf_output).resolve()
        elif _odf_output.is_dir():
            _odf_path = _odf_output
        elif _odf_output.parent.is_dir():
            _odf_path = _odf_output
        else:
            raise ValueError(f'Path to {_odf_output} does not exists.')

        pconfig.odf_path = str(_odf_path)
        pconfig.odf_output = True

        if not pconfig.netcdf_output:
            default_path = _odf_path.parent
            default_filename = _odf_path.stem

    return default_path, default_filename


def _figure_output_handler(pconfig: ProcessConfig, default_path: Path, default_filename: Path):
    if isinstance(pconfig.make_figures, bool):
        if pconfig.make_figures is True:
            pconfig.figures_output = True
            if pconfig.headless is True:
                pconfig.figures_path = str(default_path.joinpath(default_filename))
    elif isinstance(pconfig.make_figures, str):
        _figures_output = Path(pconfig.make_figures)
        if Path(_figures_output.name) == _figures_output:
            _figures_path = default_path.joinpath(_figures_output).resolve()
        elif _figures_output.is_dir():
            _figures_path = _figures_output.joinpath(default_filename)
        elif _figures_output.parent.is_dir():
            _figures_path = _figures_output
        else:
            raise ValueError(f'Path to {_figures_output} does not exists.')

        pconfig.figures_path = str(_figures_path)
        pconfig.figures_output = True

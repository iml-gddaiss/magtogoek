"""This script contains the functions to process adcp data.

    These functions are called by the app command `process` (magtogoek.app)

    Use the function: magtogoek.config_handler.get_config_taskparser(sensor_type = 'adcp').as_dict() to get a config to
    input to magtogoek.adcp.process.process_adcp_data(config). Replace the following value in the `config` the
    appropriate value:
        -config['INPUT']['input_files']: str or list(str) = 'path/to/file'

Script to process adcp data. # NOTE maybe no up to date
- Load
- Global_attributes
- Quality_Control
- Encoding
- variables attributes
- Make Figure
- Make Logbook
- Export -> .nc or .odf

Notes
-----
-Unspecified attributes fill value is an empty string.
-`magnetic_declination`:
     declination of the magnetic north in `degree east`.
-`sensor_depth`:
     The `sensor_depth` value in the platform file is used to set the netcdf
     global attributes of the same name. However, the `sensor_depth` value in
     the ConfigFile is used to compute the bin depth coordinates.
     If no `sensor_depth` value is set in the Configfile, a value is computed from
     the XducerDepth.
     If no `sensor_depth` value is given in both the ConfigFile and platform file,
     the `sensor_depth` attributes is computed from the adcp `xducer_depth`.
-`chief_scientist`:
      The value in the ConfigFile is used over the one in the platform file.
-`sounding` :
     bt_depth data are used for the `sounding` attributes, taking precedent over the value given in
     the platform file. If the bottom data are shit, set the option keep_bt to False.
-`manufacturer` :
    The manufacturer is automatically added to the dataset by the loader. However, the value given in the platform file
    will overwrite it.



Notes
-----
TODO TEST NAVIGATION FILES ! Seems to be working.
Note DATA_TYPES: Missing for ship adcp. Set to adcp for now
FIXME SOURCE : moored adcp ?
"""

import getpass
import sys
import typing as tp

import click
import numpy as np
import pandas as pd
import xarray as xr
from magtogoek.adcp.loader import load_adcp_binary
from magtogoek.adcp.odf_exporter import make_odf
from magtogoek.adcp.quality_control import (adcp_quality_control,
                                            no_adcp_quality_control)
from magtogoek.tools import (
    rotate_2d_vector, regrid_dataset, _prepare_flags_for_regrid, _new_flags_bin_regrid,
    _new_flags_interp_regrid)
from magtogoek.attributes_formatter import (
    compute_global_attrs, format_variables_names_and_attributes, _add_data_min_max_to_var_attrs)
from magtogoek.navigation import load_navigation
from magtogoek.platforms import _add_platform
from magtogoek.utils import Logger, ensure_list_format, json2dict
from magtogoek.adcp.adcp_plots import make_adcp_figure
from pathlib import Path

l = Logger(level=0)

TERMINAL_WIDTH = 80

STANDARD_ADCP_GLOBAL_ATTRIBUTES = {
    "sensor_type": "adcp",
    "featureType": "timeSeriesProfile",
}
DEFAULT_CONFIG_ATTRIBUTES = {
    "date_created": pd.Timestamp.now().strftime("%Y-%m-%d"),
    "publisher_name": getpass.getuser(),
    "source": "adcp",
}
VARIABLES_TO_DROP = [
    "binary_mask"
]
GLOBAL_ATTRS_TO_DROP = [
    "sensor_type",
    "platform_type",
    "VAR_TO_ADD_SENSOR_TYPE",
    "P01_CODES",
    "xducer_depth",
    "sonar",
    "variables_gen_name",
    "binary_mask_tests",
    "binary_mask_tests_values",
    "bodc_name"
]
CONFIG_GLOBAL_ATTRS_SECTIONS = ["NETCDF_CF", "PROJECT", "CRUISE", "GLOBAL_ATTRIBUTES"]
PLATFORM_TYPES = ["buoy", "mooring", "ship"]
DEFAULT_PLATFORM_TYPE = "buoy"
DATA_TYPES = {"buoy": "madcp", "mooring": "madcp", "ship": "adcp"}
DATA_SUBTYPES = {"buoy": "BUOY", "mooring": "MOORED", "ship": "SHIPBORNE"}

P01_VEL_CODES = dict(
    buoy=dict(
        u="LCEWAP01",
        v="LCNSAP01",
        w="LRZAAP01",
        e="LERRAP01",
        u_QC="LCEWAP01_QC",
        v_QC="LCNSAP01_QC",
        w_QC="LRZAAP01_QC",
    ),
    ship=dict(
        u="LCEWAS01",
        v="LCNSAS01",
        w="LRZAAS01",
        e="LERRAS01",
        u_QC="LCEWAS01_QC",
        v_QC="LCNSAS01_QC",
        w_QC="LRZAAS01_QC",
    ),
)
P01_VEL_CODES["mooring"] = P01_VEL_CODES["buoy"]
P01_CODES = dict(
    time="ELTMEP01",
    depth="PPSAADCP",
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
    vb_vel="LRZUVP01",
    vb_vel_QC="LRZUVP01_QC",
    vb_pg="PCGDAP05",
    vb_cor="CMAGZZ05",
    vb_amp="TNIHCE05",
    lon="ALONZZ01",
    lat="ALATZZ01",
    heading="HEADCM01",
    roll_="ROLLGP01",
    pitch="PTCHGP01",
    u_ship="APEWGP01",
    v_ship="APNSGP01",
    pres="PRESPR01",
    pres_QC="PRESPR01_QC",
    temperature="TEMPPR01",
    temperature_QC="TEMPPR01_QC",
    xducer_depth="ADEPZZ01",
    time_string="DTUT8601",
    bt_depth="BATHDPTH",
)

VAR_TO_ADD_SENSOR_TYPE = ["TEMPPR01", "PRESPR01", "ADEPZZ01", "BATHDPTH"]

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

# filled value used by ODF format
DATE_STRING_FILL_VALUE = "17-NOV-1858 00:00:00.00"
QC_FILL_VALUE = 127
QC_ENCODING = {"dtype": "int8", "_FillValue": QC_FILL_VALUE}

DATA_FILL_VALUE = -9999.0
DATA_ENCODING = {"dtype": "float32", "_FillValue": DATA_FILL_VALUE}


class ProcessConfig:
    sensor_type: str = None
    platform_type: str = None
    input_files: str = None
    platform_file: str = None
    platform_id: str = None
    sensor_id: str = None
    netcdf_output: tp.Union[str, bool] = None
    odf_output: tp.Union[str, bool] = None
    figures_output: tp.Union[str, bool] = None
    yearbase: int = None
    adcp_orientation: str = None
    sonar: str = None
    navigation_file: str = None
    leading_trim: tp.Union[int, str] = None
    trailing_trim: tp.Union[int, str] = None
    sensor_depth: float = None
    depth_range: list = None
    magnetic_declination: float = None
    keep_bt: bool = None
    bad_pressure: bool = None
    start_time: str = None
    time_step: float = None
    quality_control: bool = None
    amplitude_threshold: int = None
    percentgood_threshold: int = None
    correlation_threshold: int = None
    horizontal_velocity_threshold: float = None
    vertical_velocity_threshold: float = None
    error_velocity_threshold: float = None
    sidelobes_correction: bool = None
    bottom_depth: float = None
    pitch_threshold: float = None
    roll_threshold: float = None
    motion_correction_mode: str = None
    merge_output_files: bool = None
    bodc_name: bool = None
    force_platform_metadata: bool = None
    drop_percent_good: bool = None
    drop_correlation: bool = None
    drop_amplitude: bool = None
    make_figures: bool = None
    make_log: bool = None
    odf_data: str = None
    metadata: dict = None
    platform_metadata: dict = None

    drop_empty_attrs: bool = False
    headless: bool = False
    netcdf_path: str = None
    odf_path: str = None
    log_path: str = None
    figures_path: str = None

    grid_depth: str = None
    grid_method: str = None

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

        _outputs_path_handler(self)

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
        if self.platform_file is not None:
            if Path(self.platform_file).is_file():
                self.platform_metadata = _load_platform(self.platform_file, self.platform_id, self.sensor_id)
            else:
                l.warning(f"platform_file, {self.platform_file}, not found")
        elif self.platform_type is not None:
            self.platform_metadata = _default_platform_metadata()
            if self.platform_type in DEFAULT_PLATFORM_TYPE:
                self.platform_metadata["platform"]['platform_type'] = self.platform_type
            else:
                self.platform_metadata["platform"]['platform_type'] = DEFAULT_PLATFORM_TYPE
                l.warning(f"platform_type invalid or no specified. Must be one of {PLATFORM_TYPES}")
                l.warning(f"platform_type set to `{DEFAULT_PLATFORM_TYPE}` for platform_type.")


def process_adcp(config: dict,
                 drop_empty_attrs: bool = False,
                 headless: bool = False):
    """Process adcp data with parameters from a config file.

    Parameters
    ----------
    config :
        Dictionary make from a configfile (see config_handler.load_config).
    drop_empty_attrs :
        If true, all netcdf empty ('') global attributes will be drop from
        the output.
    headless :
        If true, figures are not displayed.

    The actual data processing is carried out by _process_adcp_data.
    """
    pconfig = ProcessConfig(config)
    pconfig.drop_empty_attrs = drop_empty_attrs
    pconfig.headless = headless

    if pconfig.merge_output_files:
        _process_adcp_data(pconfig)
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

            _process_adcp_data(pconfig)


def _process_adcp_data(pconfig: ProcessConfig):
    """Process adcp data

    FIXME EXPLAIN THE PROCESSING WORKFLOW FIXME

    Meanwhile, the code is pretty explicit. Go check it out if need be.

    Notes
    -----
    pconfig.sensor_depth`:
        `sensor_depth` in the platform file is used for the variables attributes. If no
        value is given, it is computed from the XducerDepth. However, the `sensor_depth`
        value in the ConfigFile is used to compute the bin depth coordinates. If no
        `sensor_depth` value is given in both the ConfigFile and platform file, the
        `sensor_depth` attributes is computed from the adcp `Xducer_depth`.
    `fixed_sensor_depth`:
        Set all XducerDepth value to `fixed_sensor_depth`.
    Raises
    ------
    ValueError :
        `platform_type` value in the platform file must be either 'mooring' or 'ship'.

    """
    l.reset()
    # ----------------- #
    # LOADING ADCP DATA #
    # ----------------- #

    dataset = _load_adcp_data(pconfig)

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

    dataset.attrs["data_type"] = DATA_TYPES[pconfig.platform_type]
    dataset.attrs["data_subtype"] = DATA_SUBTYPES[pconfig.platform_type]

    if pconfig.platform_metadata["platform"]["longitude"]:
        dataset.attrs["longitude"] = pconfig.platform_metadata["platform"]["longitude"]
    if pconfig.platform_metadata["platform"]["latitude"]:
        dataset.attrs["latitude"] = pconfig.platform_metadata["platform"]["latitude"]

    compute_global_attrs(dataset)

    if pconfig.platform_metadata["platform"]["platform_type"] in ["mooring", "buoy"]:
        if "bt_depth" in dataset:
            dataset.attrs["sounding"] = np.round(np.median(dataset.bt_depth.data), 2)

    _set_xducer_depth_as_sensor_depth(dataset)

    _set_platform_metadata(dataset, pconfig)

    dataset = dataset.assign_attrs(pconfig.metadata)

    if not dataset.attrs["source"]:
        dataset.attrs["source"] = pconfig.platform_type

    # --------------- #
    # QUALITY CONTROL #
    # --------------- #

    dataset.attrs["logbook"] += l.logbook

    if pconfig.quality_control:
        _quality_control(dataset, pconfig)
    else:
        no_adcp_quality_control(dataset)

    l.reset()

    # ----------------------------------- #
    # CORRECTION FOR MAGNETIC DECLINATION #
    # ----------------------------------- #

    l.section("Data transformation")

    if dataset.attrs['magnetic_declination'] is not None:
        l.log(f"Magnetic declination found in the raw file: {dataset.attrs['magnetic_declination']} degree east.")
    else:
        l.log(f"No magnetic declination found in the raw file.")
    if pconfig.magnetic_declination:
        angle = pconfig.magnetic_declination
        if dataset.attrs["magnetic_declination"]:
            angle = round((pconfig.magnetic_declination - dataset.attrs["magnetic_declination"]), 4)
            l.log(f"An additional correction of {angle} degree east was applied.")
        _apply_magnetic_correction(dataset, angle)
        dataset.attrs["magnetic_declination"] = pconfig.magnetic_declination
        l.log(f"Absolute magnetic declination: {dataset.attrs['magnetic_declination']} degree east.")

    if any(x is True for x in [pconfig.drop_percent_good, pconfig.drop_correlation, pconfig.drop_amplitude]):
        dataset = _drop_beam_data(dataset, pconfig)

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
        **P01_VEL_CODES[pconfig.platform_type],
        **P01_CODES,
    }
    dataset.attrs["variables_gen_name"] = [var for var in dataset.variables]  # For Odf outputs

    l.section("Variables attributes")
    dataset = format_variables_names_and_attributes(dataset)

    # ------------ #
    # MAKE FIGURES #
    # ------------ #
    if pconfig.make_figures:
        if pconfig.headless is True and pconfig.figures_output is False:
            pconfig.figures_output = True
        make_adcp_figure(dataset,
                         flag_thres=2,
                         path=pconfig.figures_path,
                         save=pconfig.figures_output,
                         headless=pconfig.headless)

    dataset["time"].assign_attrs(TIME_ATTRS)

    l.log("Variables attributes added.")

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
    # RE-GRIDDING #
    # ----------- #
    l.section("Post-processing")
    if pconfig.grid_depth != "":
        dataset = _regrid_dataset(dataset, pconfig)

    # ----------- #
    # ODF OUTPUTS #
    # ----------- #

    l.section("Output")
    if pconfig.odf_output is True:
        if pconfig.odf_data is None:
            pconfig.odf_data = 'both'
        odf_data = {'both': ['VEL', 'ANC'], 'vel': ['VEL'], 'anc': ['ANC']}[pconfig.odf_data]
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

    # MAKE_FIG TODO

    click.echo(click.style("=" * TERMINAL_WIDTH, fg="white", bold=True))


def _load_adcp_data(pconfig: ProcessConfig) -> xr.Dataset:
    """
    Load and trim the adcp data into a xarray.Dataset.
    Drops bottom track data if `keep_bt` is False.
    """
    start_time, leading_index = _get_datetime_and_count(pconfig.leading_trim)
    end_time, trailing_index = _get_datetime_and_count(pconfig.trailing_trim)

    dataset = load_adcp_binary(
        filenames=pconfig.input_files,
        yearbase=pconfig.yearbase,
        sonar=pconfig.sonar,
        leading_index=leading_index,
        trailing_index=trailing_index,
        orientation=pconfig.adcp_orientation,
        sensor_depth=pconfig.sensor_depth,
        bad_pressure=pconfig.bad_pressure,
        start_time=pconfig.start_time,
        time_step=pconfig.time_step,
    )

    dataset = cut_bin_depths(dataset, pconfig.depth_range)

    dataset = cut_times(dataset, start_time, end_time)

    l.log(
        (
            f"Bin counts : {len(dataset.depth.data)}, "
            + f"Min depth : {np.round(dataset.depth.min().data, 3)} m, "
            + f"Max depth : {np.round(dataset.depth.max().data, 3)} m, "
            + f"Bin size : {dataset.attrs['bin_size_m']} m"
        )
    )
    l.log(
        (
            f"Ensemble counts : {len(dataset.time.data)}, "
            + f"Start time : {np.datetime_as_string(dataset.time.min().data, unit='s')}, "
            + f"End time : {np.datetime_as_string(dataset.time.max().data, unit='s')}"
        )
    )
    if not pconfig.keep_bt:
        dataset = _drop_bottom_track(dataset)

    return dataset


def _set_platform_metadata(dataset: xr.Dataset, pconfig: ProcessConfig):
    """Add metadata from platform_metadata files to dataset.attrs.

    Values that are dictionary instances are not added.

    Parameters
    ----------
    pconfig
    dataset :
        Dataset to which add the navigation data.
    """
    metadata = {**pconfig.platform_metadata['platform'], **pconfig.platform_metadata[pconfig.sensor_type]}
    metadata['sensor_comments'] = metadata['comments']
    if pconfig.force_platform_metadata:
        for key, value in metadata.items():
            dataset.attrs[key] = value
        if "sensor_depth" in metadata:
            l.log(
                f"`sensor_depth` value ({pconfig.platform_metadata['sensor_depth']} was set by the user."
            )

    else:
        for key, value in metadata.items():
            if key in dataset.attrs:
                if not dataset.attrs[key]:
                    dataset.attrs[key] = value
            else:
                dataset.attrs[key] = value


def _set_xducer_depth_as_sensor_depth(dataset: xr.Dataset):
    """Set xducer_depth value to dataset attributes sensor_depth"""
    if "xducer_depth" in dataset.attrs:  # OCEAN SURVEYOR
        dataset.attrs["sensor_depth"] = dataset.attrs["xducer_depth"]

    if "xducer_depth" in dataset:
        dataset.attrs["sensor_depth"] = np.round(
            np.median(dataset["xducer_depth"].data), 2
        )


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


def _regrid_dataset(dataset: xr.Dataset, pconfig: ProcessConfig) -> xr.Dataset:
    """ Wrapper for regrid_dataset

    Note
    ----
    The `interp` method performs linear interpolation. The `bin` method
    performs averaging of input data strictly within the bin boundaries
    and with equal weights for all data inside each bin.

    """
    # Read new depths
    _new_depths = np.loadtxt(pconfig.grid_depth)

    # Pre-process flags
    for var_ in 'uvw':
        _flag_name = dataset[var_].attrs['ancillary_variables']
        dataset[_flag_name].values = _prepare_flags_for_regrid(dataset[_flag_name].data)

    # Make new quality flags if grid_method is `bin`. Must happen before averaging.
    if pconfig.grid_method == 'bin':
        _new_flags = dict()
        for var_ in 'uvw':
            _flag_name = dataset[var_].attrs['ancillary_variables']
            _new_flags[_flag_name] = _new_flags_bin_regrid(dataset[_flag_name], _new_depths)
        new_flags = xr.Dataset(_new_flags)

    # Apply quality control
    for var_ in 'uvw':
        _flag_name = dataset[var_].attrs['ancillary_variables']
        dataset[var_] = dataset[var_].where(dataset[_flag_name] == 8)

    # Regridding
    msg = f"to grid from file: {pconfig.grid_depth}"
    l.log(f"Regridded dataset with method {pconfig.grid_method} {msg}")
    dataset = regrid_dataset(dataset,
                             grid=_new_depths,
                             dim='depth',
                             method=pconfig.grid_method)

    # Make new flags and replace interpolated/binned values
    for var_ in 'uvw':
        _flag_name = dataset[var_].attrs['ancillary_variables']
        if pconfig.grid_method == 'bin':
            dataset[_flag_name] = new_flags[_flag_name]
        elif pconfig.grid_method == 'interp':
            dataset[_flag_name] = _new_flags_interp_regrid(dataset, var_)

    # Change min and max values
    _add_data_min_max_to_var_attrs(dataset)

    return dataset


def _quality_control(dataset: xr.Dataset, pconfig: ProcessConfig):
    """Carries quality control.

    Wrapper for adcp_quality_control"""

    adcp_quality_control(dataset=dataset,
                         amp_th=pconfig.amplitude_threshold,
                         corr_th=pconfig.correlation_threshold,
                         pg_th=pconfig.percentgood_threshold,
                         roll_th=pconfig.roll_threshold,
                         pitch_th=pconfig.pitch_threshold,
                         horizontal_vel_th=pconfig.horizontal_velocity_threshold,
                         vertical_vel_th=pconfig.vertical_velocity_threshold,
                         error_vel_th=pconfig.error_velocity_threshold,
                         motion_correction_mode=pconfig.motion_correction_mode,
                         sidelobes_correction=pconfig.sidelobes_correction,
                         bottom_depth=pconfig.bottom_depth,
                         bad_pressure=pconfig.bad_pressure)


def _apply_magnetic_correction(dataset: xr.Dataset, magnetic_declination: float):
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


def _get_datetime_and_count(trim_arg: tp.Union[str, int]):
    """Get datetime and count from trim_arg.

    If `trim_arg` is None, returns (None, None)
    If 'T' is a datetime or a count returns (Timestamp(trim_arg), None)
    Else returns (None, int(trim_arg))

    Returns:
    --------
    Timestamp:
        None or pandas.Timestamp
    count:
        None or int

    """
    if trim_arg:
        if isinstance(trim_arg, int):
            return None, trim_arg
        elif not trim_arg.isdecimal():
            try:
                return pd.Timestamp(trim_arg), None
            except ValueError:
                print("Bad datetime format for trim. Use YYYY-MM-DDTHH:MM:SS.ssss")
                print("Process aborted")
                sys.exit()
        else:
            return None, int(trim_arg)
    else:
        return None, None


def _drop_beam_data(dataset: xr.Dataset, pconfig: ProcessConfig):
    """"""
    for var, name, flag in zip(
            ["pg", "corr", "amp"],
            ["percent_good", "correlation", "amplitude"],
            [pconfig.drop_percent_good, pconfig.drop_correlation, pconfig.drop_amplitude]
    ):
        if flag is True:
            for v in [var + i for i in ["", "1", "2", "3", "4"]]:
                if v in dataset:
                    dataset = dataset.drop_vars([v])
            l.log(f"{name} data dropped.")

    return dataset


def _format_data_encoding(dataset: xr.Dataset):
    """Format data encoding with default value in module."""
    l.section("Data Encoding")
    for var in dataset.variables:
        if var == "time":
            dataset.time.encoding = TIME_ENCODING
        elif var == "depth":
            dataset.depth.encoding = DEPTH_ENCODING
        elif "_QC" in var:
            dataset[var].values = dataset[var].values.astype("int8")
            dataset[var].encoding = QC_ENCODING
        elif var == "time_string":
            dataset[var].encoding = TIME_STRING_ENCODING
        else:
            dataset[var].encoding = DATA_ENCODING

    l.log(f"Data _FillValue: {DATA_FILL_VALUE}")
    l.log(f"Ancillary Data _FillValue: {QC_FILL_VALUE}")


def _drop_bottom_track(dataset: xr.Dataset) -> xr.Dataset:
    """Drop `bt_u`, `bt_v`, `bt_w`, `bt_e`, `bt_depth`"""
    for var in ["bt_u", "bt_v", "bt_w", "bt_e", "bt_depth"]:
        if var in dataset:
            dataset = dataset.drop_vars([var])
    return dataset


def cut_bin_depths(
        dataset: xr.Dataset, depth_range: tp.Union[int, float, list] = None
) -> xr.Dataset:
    """
    Return dataset with cut bin depths if the depth_range are not outside the depth span.
    Parameters
    ----------
    dataset :
    depth_range :
        min or (min, max) to be included in the dataset.
        Bin depths outside this range will be cut.

    Returns
    -------
    dataset with depths cut.

    """
    if depth_range:
        if not isinstance(depth_range, (list, tuple)):
            if depth_range > dataset.depth.max():
                l.log(
                    "depth_range value is greater than the maximum bin depth. Depth slicing aborted."
                )
            else:
                dataset = dataset.sel(depth=slice(depth_range, None))
                l.log(f"Bin of depth inferior to {depth_range} m were cut.")
        elif len(depth_range) == 2:
            if dataset.depth[0] > dataset.depth[-1]:
                depth_range.reverse()
            if (
                    depth_range[0] > dataset.depth.max()
                    or depth_range[1] < dataset.depth.min()
            ):
                l.log(
                    "depth_range values are outside the actual depth range. Depth slicing aborted."
                )
            else:
                dataset = dataset.sel(depth=slice(*depth_range))
                l.log(
                    f"Bin of depth inferior to {depth_range[0]} m and superior to {depth_range[1]} m were cut."
                )
        else:
            l.log(
                f"depth_range expects a maximum of 2 values but {len(depth_range)} were given. Depth slicing aborted."
            )
    return dataset


def cut_times(
        dataset: xr.Dataset, start_time: pd.Timestamp = None, end_time: pd.Timestamp = None
) -> xr.Dataset:
    """
    Return a dataset with time cut if they are not outside the dataset time span.

    Parameters
    ----------
    dataset
    start_time :
        minimum time to be included in the dataset.
    end_time :
        maximum time to be included in the dataset.
    Returns
    -------
    dataset with times cut.

    """
    msg = []
    out_off_bound_time = False
    if start_time is not None:
        if start_time > dataset.time.max():
            out_off_bound_time = True
        else:
            msg.append(f"Start={start_time.strftime('%Y-%m-%dT%H:%M:%S')}")
    if end_time is not None:
        if end_time < dataset.time.min():
            out_off_bound_time = True
        else:
            msg.append(f"end={end_time.strftime('%Y-%m-%dT%H:%M:%S')}")
    if out_off_bound_time is True:
        l.warning("Trimming datetimes out of bounds. Time slicing aborted.")
    else:
        dataset = dataset.sel(time=slice(start_time, end_time))
        if len(msg) > 0:
            l.log('Time slicing: ' + ', '.join(msg) + '.')

    return dataset


def _default_platform_metadata() -> dict:
    """Return an empty platform data dictionary"""
    platform_metadata = {'platform': _add_platform(), 'adcp_id': 'ADCP_01'}
    platform_metadata['platform']["platform_type"] = DEFAULT_PLATFORM_TYPE
    platform_metadata['sensors'] = platform_metadata['platform'].pop('sensors')
    platform_metadata['adcp'] = platform_metadata['sensors'].pop('__enter_a_sensor_ID_here')
    platform_metadata['buoy_specs'] = platform_metadata['platform'].pop('buoy_specs')

    return platform_metadata


def _load_platform(platform_file: str, platform_id: str, sensor_id: str) -> tp.Dict:
    """load sensor metadata into dict

    Returns a `flat` dictionary with all the parents metadata
    to `platform.json/platform_id/sensors/sensor_id` and the
    metadata of the `sensor_id.`
    """
    platform_metadata = _default_platform_metadata()
    json_dict = json2dict(platform_file)
    if platform_id in json_dict:
        platform_metadata['platform'].update(json_dict[platform_id])
        if 'buoy_specs' in platform_metadata['platform']:
            platform_metadata['buoy_specs'].update(platform_metadata['platform'].pop('buoy_specs'))
        if 'sensors' in platform_metadata['platform']:
            platform_metadata['sensors'].update(platform_metadata['platform'].pop('sensors'))
            if sensor_id in platform_metadata["sensors"]:
                platform_metadata['adcp_id'] = sensor_id
                platform_metadata['adcp'].update(platform_metadata["sensors"].pop(sensor_id))
            else:
                l.warning(f"{sensor_id} not found in the {platform_id}['sensor'] section of the platform file.")
        else:
            l.warning(f'sensors section missing in the {platform_id} section of the platform file.')
    else:
        l.warning(f"{platform_id} not found in platform file.")
    return platform_metadata


def _outputs_path_handler(pconfig: ProcessConfig):
    """ Figure out the outputs to make and their path.
    """
    input_path = pconfig.input_files[0]
    default_path = Path(input_path).parent
    default_filename = Path(input_path).name

    if not pconfig.odf_output and not pconfig.netcdf_output:
        pconfig.netcdf_output = True

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
        default_filename = netcdf_path.name
        pconfig.netcdf_path = str(netcdf_path)
        pconfig.netcdf_output = True

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

    if isinstance(pconfig.make_figures, bool):
        pconfig.figures_output = False
        pconfig.figures_path = str(default_path.joinpath(default_filename))
    elif isinstance(pconfig.make_figures, str):
        _figures_output = Path(pconfig.make_figures)
        if Path(_figures_output.name) == _figures_output:
            _figures_path = default_path.joinpath(_figures_output).resolve()
        elif _figures_output.is_dir():
            _figures_path = _figures_output
        elif _figures_output.parent.is_dir():
            _figures_path = _figures_output
        else:
            raise ValueError(f'Path to {_figures_output} does not exists.')

        pconfig.figures_path = str(_figures_path)
        pconfig.figures_output = True

    pconfig.log_path = str(default_path.joinpath(default_filename))

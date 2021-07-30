"""
This script has to functions to process and quick process adcp data.
These functions are called by the app command `process` and `quick adcp`.


Script to process adcp data. FIXME

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
Unspecified attributes fill value "N/A".
`magnetic_declination`:
    declination of the magnetic north in `degree east`.

`sensor_depth`:
    `sensor_depth` in the platform file is used for the variables attributes. If no
    value is given, it is computed from the XducerDepth. However, the `sensor_depth`
    value in the ConfigFile is used to compute the bin depth coordinates. If no
    `sensor_depth` value is given in both the ConfigFile and platform file, the
    `sensor_depth` attributes is computed from the adcp `Xducer_depth`.

`chief_scientist`:
     The value in the ConfigFile is used over the one in the platform file.

`sounding` :
    bt_depth data are used for the `sounding` attributes, taking precedent over the value given in
    the platform file. If the bottom data are shit, set the option keep_bt to False.

`manufacturer` :
   The manufactuer is automaticaly added to the dataset by the loader. However, the value given in the platform file will
   overwrite it.

TODO TEST NAVIGATIN FILES !
FIXME DATA_TYPES: Missing for ship adcp

NOTE
TODO add option to force platform file metadata over over those computed from the adcp file.
- Global Attributes Priorities:
  `force_platform` is False True:
      CONFIGFILE > COMPUTED > PLATFORM
  `force_platform` is False False:
      CONFIGFILE > PLATFORM > COMPUTED 



"""

import getpass
import typing as tp
from configparser import ConfigParser

import click
import numpy as np
import pandas as pd
import xarray as xr
from magtogoek.adcp.loader import load_adcp_binary
from magtogoek.adcp.quality_control import (adcp_quality_control,
                                            no_adcp_quality_control)
from magtogoek.adcp.tools import magnetic_to_true
from magtogoek.attributes_formatter import (
    compute_global_attrs, format_variables_names_and_attributes)
from magtogoek.navigation import load_navigation
from magtogoek.tools import get_gps_bearing, vincenty
from magtogoek.utils import Logger, json2dict

l = Logger(level=0)

from pathlib import Path

TERMINAL_WIDTH = 80

STANDARD_ADCP_GLOBAL_ATTRIBUTES = {
    "sensor_type": "adcp",
    "featureType": "timeSeriesProfile",
}

GLOBAL_ATTRS_TO_DROP = [
    "sensor_type",
    "platform_type",
    "VAR_TO_ADD_SENSOR_TYPE",
    "P01_CODES",
    "xducer_depth",
    "sonar",
]


CONFIG_GLOBAL_ATTRS_SECTIONS = ["NETCDF_CF", "PROJECT", "CRUISE", "GLOBAL_ATTRIBUTES"]
PLATFORM_TYPES = ["mooring", "ship"]
DATA_TYPES = {"mooring": "MADCP", "ship": None}
DEFAULT_PLATFORM_TYPE = "mooring"
PLATFORM_FILE_DEFAULT_KEYS = [
    "platform_type",
    "platform_subtype",
    "longitude",
    "latitude",
    "sounding",
    "sensor_depth",
    "serial_number",
    "manufacturer",
    "model",
    "firmware_version",
    "chief_scientist",
    "comments",
]
P01_VEL_CODES = dict(
    mooring=dict(
        u="LCEWAP01",
        v="LCNSAP01",
        w="LRZAAP01",
        e="LERRAP01",
        u_QC="LCEWAP01_QC",
        v_QC="LCNSAP01_QC",
        w_QC="LRZAAP01_QC",
        e_QC="LERRAP01_QC",
    ),
    ship=dict(
        u="LCEWAS01",
        v="LCNSAS01",
        w="LRZAAS01",
        e="LERRAS01",
        u_QC="LCEWAS01_QC",
        v_QC="LCNSAS01_QC",
        w_QC="LRZAAS01_QC",
        e_QC="LERRAS01_QC",
    ),
)
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
    "units": "Seconds since 1970-1-1 00:00:00Z",
    "calendar": "gregorian",
    "_FillValue": None,
}
DEPTH_ENCODING = {"_FillValue": None}

DATA_FILL_VALUE = -9999
DATE_STRING_FILL_VALUE = "17-NOV-1858 00:00:00.00"  # filled value used by ODF format
QC_FILL_VALUE = 127

DATA_DTYPE = "float32"

_drop_none_attrs = False


def process_adcp(config: tp.Type[ConfigParser]):
    """Process adcp data with parameters from a ConfigFile.

    Pipes the params to _to_process_adcp_data which in turn pipes
    it to _process_adcp_data.

    Using `platform_id`, `sensor_id`, the sensor metadata are loaded
    into a dictionnary and pass to _process_adcp_data.

    Notes
    -----
    missing `platform_type` :
        If the platform_type cannot be found, the function automaticaly default to
        `mooring` to set BODC P01 parameter codes.

    See Also
    --------
    _process_adcp_data :
        For the processing workflow.

    """
    params, global_attrs = _get_config(config)

    if isinstance(params["input_files"], str):
        params["input_files"] = list(params["input_files"])

    if len(params["input_files"]) == 0:
        raise ValueError("No adcp file was provided in the configfile.")

    if Path(params["platform_file"]).is_file():
        sensor_metadata = _load_platform(params)
    else:
        l.warning(f"platform_file, {params['platform_file']}, not found")
        sensor_metadata = None
    if not sensor_metadata:
        sensor_metadata = _default_platform()

    _pipe_to_process_adcp_data(params, sensor_metadata, global_attrs)


def quick_process_adcp(params: tp.Dict):
    """Process adcp data with quick_process options(params).

    Pipes the params to _to_process_adcp_data which in turn pipes
    it to _process_adcp_data.

    Using `platform_id`, `sensor_id`, the sensor metadata are loaded
    into a dictionnary and pass to _process_adcp_data.

    Notes
    -----
    missing `platform_type` :
        If the platform_type cannot be found, the function automaticaly default to
        `mooring` to set the correct BODC P01 parameter codes.

    See Also
    --------
    _process_adcp_data :
        For the processing workflow."""

    global _drop_none_attrs
    _drop_none_attrs = True
    global_attrs = {
        "date_created": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "publisher_name": getpass.getuser(),
    }

    sensor_metadata = _default_platform()

    sensor_metadata["platform_type"] = params["platform_type"]

    params["force_platform_metadata"] = False

    _pipe_to_process_adcp_data(params, sensor_metadata, global_attrs)


def _pipe_to_process_adcp_data(params, sensor_metadata, global_attrs):
    """Check if the input_file must be split in mutiple output.

        Looks for `merge_output_files` in the ConfigFile and if False,
    each file in `input_files` is process individually and then call _porcess_adcp_data.
    """
    if not params["merge_output_files"]:
        params["merge"] = True
        for fn, count in zip(params["input_files"], range(len(params["input_files"]))):
            if params["netcdf_output"]:
                params["netcdf_output"] = (
                    str(Path(params["netcdf_output"]).name) + f"_{count}"
                )
            params["input_files"] = fn
            _process_adcp_data(params, sensor_metadata, global_attrs)
            click.echo(click.style("=" * TERMINAL_WIDTH, fg="white", bold=True))
    else:
        _process_adcp_data(params, sensor_metadata, global_attrs)
        click.echo(click.style("=" * TERMINAL_WIDTH, fg="white", bold=True))


def _process_adcp_data(params: tp.Dict, sensor_metadata: tp.Dict, global_attrs):
    """Process adcp data

    FIXME EXPLAIN THE PROCESSING WORKFLOW FIXME

    Meanwhile, the code is pretty explicit. Go check it out if need be.


    Parameters
    ----------
    params :
        Processing parameters from the ConfigFile.

    gloabal_attrs :
        Global attributes parameter from the configFile.

    sensor_metadata :
        Metadata from the platform file.

    Notes
    -----
    `sensor_depth`:
        `sensor_depth` in the platform file is used for the variables attributes. If no
        value is given, it is computed from the XducerDepth. However, the `sensor_depth`
        value in the ConfigFile is used to compute the bin depth coordinates. If no
        `sensor_depth` value is given in both the ConfigFile and platform file, the
        `sensor_depth` attributes is computed from the adcp `Xducer_depth`.
    Raises
    ------
    ValueError :
        `platform_type` value in the platform file must be either 'mooring' or 'ship'.

    """
    l.reset()

    _check_platform_type(sensor_metadata)

    # ----------------- #
    # LOADING ADCP DATA #
    # ----------------- #
    dataset = _load_adcp_data(params)

    # ----------------------------------------- #
    # ADDING THE NAVIGATION DATA TO THE DATASET #
    # ----------------------------------------- #
    if params["navigation_file"]:
        l.section("Navigation data")
        dataset = _load_navigation(dataset, params["navigation_file"])

    # ----------------------------- #
    # ADDING SOME GLOBAL ATTRIBUTES #
    # ----------------------------- #

    l.section("Adding Global Attributes")

    dataset = dataset.assign_attrs(STANDARD_ADCP_GLOBAL_ATTRIBUTES)

    dataset.attrs["data_type"] = DATA_TYPES[sensor_metadata["platform_type"]]

    if sensor_metadata["longitude"]:
        dataset.attrs["longitude"] = sensor_metadata["longitude"]
    if sensor_metadata["latitude"]:
        dataset.attrs["latitude"] = sensor_metadata["latitude"]

    compute_global_attrs(dataset)

    if sensor_metadata["platform_type"] == "mooring":
        if "bt_depth" in dataset:
            dataset.attrs["sounding"] = round(np.median(dataset.bt_depth.data), 2)

    _set_xducer_depth_as_sensor_depth(dataset)

    # setting Metadata from the platform_file
    if params["force_platform_metadata"]:
        for meta in sensor_metadata:
            if sensor_metadata[meta]:
                dataset.attrs[meta] = sensor_metadata[meta]
    else:
        for meta in sensor_metadata:
            if meta in dataset.attrs:
                if not dataset.attrs[meta]:
                    dataset.attrs[meta] = sensor_metadata[meta]
            elif sensor_metadata[meta]:
                dataset.attrs[meta] = sensor_metadata[meta]

    # setting Metadata from the config_files
    dataset = dataset.assign_attrs(global_attrs)

    # ----------------------------------- #
    # CORRECTION FOR MAGNETIC DECLINATION #
    # ----------------------------------- #

    l.section("Data transformation")

    if params["magnetic_declination"]:
        if not dataset.attrs["magnetic_declination"]:
            _magnetnic_correction(dataset, params["magnetic_declination"])
        else:
            additional_correction = round(
                (
                    params["magnetic_declination"]
                    - dataset.attrs["magnetic_declination"]
                ),
                4,
            )
            _magnetnic_correction(
                dataset,
                additional_correction,
            )
            l.log(
                f"""Magnetic declination found in adcp file: {dataset.attrs["magnetic_declination"]} degree east.
An additionnal correction of {additional_correction} degree east was added to have a  {params['magnetic_declination']} degree east correction."""
            )

    else:
        dataset.attrs["magnetic_declination"] = 0
    dataset.attrs["magnetic_declination"] = params["magnetic_declination"]
    dataset.attrs["magnetic_declination_units"] = "degree east"

    # --------------- #
    # QUALITY CONTROL #
    # --------------- #

    dataset.attrs["logbook"] += l.logbook

    if params["quality_control"]:
        _quality_control(dataset, params)
    else:
        no_adcp_quality_control(
            dataset,
        )

    l.reset()

    if any(
        params["drop_" + var] for var in ("percent_good", "correlation", "amplitude")
    ):
        dataset = _drop_beam_data(dataset, params)

    # -------------- #
    # DATA ENCONDING #
    # -------------- #
    _format_data_encoding(dataset)

    # -------------------- #
    # VARIABLES ATTRIBUTES #
    # -------------------- #
    dataset.attrs["VAR_TO_ADD_SENSOR_TYPE"] = VAR_TO_ADD_SENSOR_TYPE

    dataset.attrs["P01_CODES"] = {
        **P01_VEL_CODES[sensor_metadata["platform_type"]],
        **P01_CODES,
    }

    l.section("Variables attributes")
    dataset = format_variables_names_and_attributes(
        dataset, use_bodc_codes=params["bodc_name"]
    )

    dataset["time"].assign_attrs(TIME_ATTRS)

    l.log("Variables attributes added.")

    # ------------------------------------ #
    # FINAL FORMATING OF GLOBAL ATTRIBUTES #
    # ------------------------------------ #

    if "platform_name" in dataset.attrs:
        dataset.attrs["platform"] = dataset.attrs.pop("platform_name")

    if not dataset.attrs["date_created"]:
        dataset.attrs["date_created"] = pd.Timestamp.now().strftime("%Y-%m-%d")

    dataset.attrs["date_modified"] = pd.Timestamp.now().strftime("%Y-%m-%d")

    dataset.attrs["logbook"] += l.logbook

    dataset.attrs["history"] = dataset.attrs["logbook"]
    del dataset.attrs["logbook"]

    for attr in GLOBAL_ATTRS_TO_DROP:
        if attr in dataset.attrs:
            del dataset.attrs[attr]

    for attr in list(dataset.attrs.keys()):
        if not dataset.attrs[attr]:
            if _drop_none_attrs:
                del dataset.attrs[attr]
            else:
                dataset.attrs[attr] = "N/A"

    # ------- #
    # OUTPUTS #
    # ------- #

    # OUTPUT TODO
    l.section("Output")
    if params["odf_output"]:
        odf_output = "TODO"

    export_to_netcdf = (
        not (params["odf_output"] and params["netcdf_output"])
        or params["netcdf_output"]
    )

    if export_to_netcdf:
        if params["netcdf_output"]:
            nc_output = Path(params["netcdf_output"]).with_suffix(".nc")
        else:
            nc_output = Path(params["input_files"][0]).with_suffix(".nc")
        dataset.to_netcdf(nc_output)
        l.log(f"netcdf file made -> {nc_output}")

        log_output = Path(nc_output).with_suffix(".log")
    else:
        log_output = Path(odf_output).with_suffix(".log")

    if params["make_log"]:
        with open(log_output, "w") as log_file:
            log_file.write(dataset.attrs["history"])
            print(f"log file made -> {log_output}")

    # MAKE_FIG TODO


def _load_adcp_data(params: tp.Dict) -> tp.Type[xr.Dataset]:
    """
    Load and trim the adcp data into a xarray.Dataset.
    Drops bottom track data if params `keep_bt` is False.
    """
    start_time, leading_index = _get_datetime_and_count(params["leading_trim"])
    end_time, trailing_index = _get_datetime_and_count(params["trailing_trim"])

    dataset = load_adcp_binary(
        params["input_files"],
        yearbase=params["yearbase"],
        sonar=params["sonar"],
        leading_index=leading_index,
        trailing_index=trailing_index,
        orientation=params["adcp_orientation"],
        sensor_depth=params["sensor_depth"],
    )

    dataset = dataset.sel(time=slice(start_time, end_time))

    if len(dataset.time) == 0:
        l.warning(f"{params['input_files']} time dims is of lenght 0 after slicing.")

    l.log(
        f"Bins count : {len(dataset.depth.data)}, Min depth : {dataset.depth.min().data} m, Max depth : {dataset.depth.max().data} m"
    )
    l.log(
        f"Ensembles count : {len(dataset.time.data)}, Start time : {np.datetime_as_string(dataset.time.min().data, unit='s')}, End time : {np.datetime_as_string(dataset.time.min().data, unit='s')}"
    )

    if not params["keep_bt"]:
        for var in ["bt_u", "bt_v", "bt_w", "bt_e", "bt_depht"]:
            if var in dataset:
                dataset = dataset.drop_vars([var])

    return dataset


def _get_config(config: tp.Type[ConfigParser]):
    """Flattens the config to a unested_dict""" ""
    params = dict()
    global_attrs = dict()
    for section, options in config.items():
        if section in CONFIG_GLOBAL_ATTRS_SECTIONS:
            for option in options:
                global_attrs[option] = config[section][option]
        else:
            for option in options:
                params[option] = config[section][option]

    return params, global_attrs


def _load_platform(params: dict) -> tp.Dict:
    """load sensor metadata into dict

    Returns a `flat` dictionnary with all the parents metadata
    to `platform.json/platform_id/sensors/sensor_id` and the
    metadata of the `sensor_id.`
    """
    sensor_metadata = dict()
    json_dict = json2dict(params["platform_file"])
    if params["platform_id"] in json_dict:
        platform_dict = json_dict[params["platform_id"]]
        if "sensors" in platform_dict:
            if params["sensor_id"] in platform_dict["sensors"]:
                sensor_metadata = platform_dict["sensors"][params["sensor_id"]]
            else:
                l.warning(
                    f"{params['sensor_id']} not found in {params['platform_id']}['sensor'] of the platform file."
                )
        else:
            l.warning("`sensors` section missing from platform file")
        for key in platform_dict.keys():
            if key != "sensors":
                sensor_metadata[key] = platform_dict[key]
    else:
        l.warning(f"{params['platform_id']} not found in platform file.")
        sensor_metadata = None
    return sensor_metadata


def _default_platform() -> dict:
    """Return an empty platform data dictionnary"""
    sensor_metadata = dict()
    for key in PLATFORM_FILE_DEFAULT_KEYS:
        sensor_metadata[key] = None
    return sensor_metadata


def _check_platform_type(sensor_metadata: dict):
    """DEFINED BELOW"""
    if sensor_metadata["platform_type"] not in PLATFORM_TYPES:
        sensor_metadata["platform_type"] = DEFAULT_PLATFORM_TYPE
        l.warning(
            f"platform_file missing or invalid, defaulting to `{DEFAULT_PLATFORM_TYPE}` for platform_type."
        )
        l.warning(f"platform_type invalid. Must be one of {PLATFORM_TYPES}")


_check_platform_type.__doc__ = f"""Check the validity of the `plaform_type`.
    `platform _type` must be one of {PLATFORM_TYPES}.
    `platform_type` defaults to {DEFAULT_PLATFORM_TYPE}"""


def _load_navigation(dataset: tp.Type[xr.Dataset], navigation_files: str):
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
    nav_ds = load_navigation(navigation_files).interp(time=dataset.time)
    dataset = xr.merge((dataset, nav_ds), combine_attrs="no_conflicts")
    return dataset


def _quality_control(dataset: tp.Type[xr.Dataset], params: tp.Dict):
    """Carries quality control.

    Wrapper for adcp_quality_control"""

    adcp_quality_control(
        dataset,
        amp_th=params["amplitude_threshold"],
        corr_th=params["correlation_threshold"],
        pg_th=params["percentgood_threshold"],
        roll_th=params["roll_threshold"],
        pitch_th=params["pitch_threshold"],
        horizontal_vel_th=params["horizontal_velocity_threshold"],
        vertical_vel_th=params["vertical_velocity_threshold"],
        error_vel_th=params["error_velocity_threshold"],
        motion_correction_mode=params["motion_correction_mode"],
        sidelobes_correction=params["sidelobes_correction"],
        bottom_depth=params["bottom_depth"],
    )


def _magnetnic_correction(dataset: tp.Type[xr.Dataset], magnetic_declination: float):
    """Correct for magnetic declination.
    Rotate eastward and northward velocities from magnetic to geographic and
    """

    dataset.u.values, dataset.v.values = magnetic_to_true(
        dataset.u, dataset.v, magnetic_declination
    )
    l.log(f"Velocities transformed to true north and True east.")
    # heading goes from -180 to 180
    if "heading" in dataset:
        dataset.heading.values = (
            dataset.heading.data + 360 + magnetic_declination
        ) % 360 - 180
        l.log(f"Heading transformed to true north.")


def _get_datetime_and_count(trim_arg: str):
    """Get datime and count from trim_arg.

    If `trim_arg` is None, returns (None, None)
    If 'T' is a datetimeor a count returns (Timstamp(trim_arg), None)
    Else returns (None, int(trim_arg))

    Returns:
    --------
    datetime:
        None or pandas.Timstamp
    count:
        None or int

    """
    if trim_arg:
        if "T" in trim_arg:
            return (pd.Timestamp(trim_arg), None)
        else:
            return (None, int(trim_arg))
    else:
        return (None, None)


def _set_xducer_depth_as_sensor_depth(dataset: tp.Type[xr.Dataset]):
    """Set xducer_depth value to dataset attributes sensor_depth"""
    if "xducer_depth" in dataset:
        dataset.attrs["sensor_depth"] = np.median(dataset["xducer_depth"].data)
        l.log("`sensor_depth` correspond to the `xducer_depth` median.")

    if "xducer_depth" in dataset.attrs:
        dataset.attrs["sensor_depth"] = dataset.attrs["xducer_depth"]
        l.log("`sensor_depth` correspond to the `xducer_depth`.")


def _drop_beam_data(dataset: tp.Type[xr.Dataset], params: tp.Dict):
    """check in params if pg, corr and amp are to be dropped
    (drop_pg, drop_corr, drop_amp)

    """
    for var in [
        ("pg", "percent_good"),
        ("corr", "correlation"),
        ("amp", "amplitude"),
    ]:
        if params[f"drop_{var[1]}"]:
            for i in ["", "1", "2", "3", "4"]:
                if var[0] + i in dataset:
                    dataset = dataset.drop_vars([var[0] + i])
            l.log(f"{var[1]} data dropped.")

    return dataset


def _format_data_encoding(dataset: tp.Type[xr.Dataset]):
    """FIXME"""
    l.section("Data Encoding")
    for var in dataset.variables:
        if var == "time":
            dataset.time.encoding = TIME_ENCODING
        elif var == "depth":
            dataset.depth.encoding = DEPTH_ENCODING
        elif "_QC" in var:
            dataset[var].values = dataset[var].values.astype("int8")
            dataset[var].encoding = {"dtype": "int8", "_FillValue": QC_FILL_VALUE}
        if var == "time_string":
            dataset[var].encoding = {
                "dtype": "S1",
            }
        else:
            dataset[var].encoding = {"dtype": DATA_DTYPE, "_FillValue": DATA_FILL_VALUE}

    l.log(f"adcp Data _FillValue: {DATA_FILL_VALUE}")
    l.log(f"Ancillary Data _FillValue: {DATA_FILL_VALUE}")

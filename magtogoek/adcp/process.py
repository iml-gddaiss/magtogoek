"""
FIXME
Script to process adcp data.

- Load
- Global_attributes
- Quality_Control
- Encoding
- variables attributes
- Make Figure
- Make Logbook
- Export -> .nc or .odf
- Ancillary variables names (gen vs bodc)


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
    the platform file. If the bottom data are shit, set the option (not yet implemented) keep_bt to False.

`manufacturer` :
   The manufactuer is automaticaly added to the dataset by the loader. However, the value given in the platform file will
   overwrite it.

FIXME
MISSING METADATA :
    transmit_pulse_length_cm
    pings_per_ensemble


"""

import typing as tp
from configparser import ConfigParser

import numpy as np
import pandas as pd
import xarray as xr
from magtogoek.adcp.loader import load_adcp_binary
from magtogoek.adcp.quality_control import (adcp_quality_control,
                                            no_adcp_quality_control)
from magtogoek.attributes_formatter import (
    format_global_attrs, format_variables_names_and_attributes)
from magtogoek.tools import get_gps_bearing, magnetic_to_true, vincenty
from magtogoek.utils import Logger, json2dict

l = Logger(level=0)

from pathlib import Path

ADCP_GLOBAL_ATTRIBUTES = {"sensor_type": "adcp", "featureType": "timeSeriesProfile"}
GLOBAL_ATTRS_TO_DROP = [
    "sensor_type",
    "platform_type",
    "VAR_TO_ADD_SENSOR_TYPE",
    "P01_CODES",
]

CONFIG_GLOBAL_ATTRS_SECTIONS = ["NETCDF_CF", "PROJECT", "CRUISE", "GLOBAL_ATTRIBUTES"]

PLATFORM_FILE_KEYS = [
    "platform_name",
    "platform_type",
    "longitude",
    "latitude",
    "sounding",
    "sensor_type",
    "sensor_depth",
    "serial_number",
    "manufacturer",
    "model",
    "firmware_version",
    "chief_scientist",
    "description",
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
QC_FILL_VALUE = 127

DATA_DTYPE = "float32"


def process_adcp_config(config: tp.Type[ConfigParser]):
    """Wrap around _process_adcp_data

    Looks for `merge_output_files` in the ConfigFile and if False,
    each file in `input_files` is process individually.

    Notes
    -----

    FIXME put this in the app ?.

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

    if not params["merge_output_files"]:
        params["merge"] = True
        for fn, count in zip(params["input_files"], range(len(params["input_files"]))):
            if params["netcdf_output"]:
                params["netcdf_output"] = (
                    str(Path(params["netcdf_output"]).name) + f"_{count}"
                )
            params["input_files"] = fn

            _process_adcp_data(params, global_attrs)
    else:
        _process_adcp_data(params, global_attrs)


def _process_adcp_data(params: tp.Dict, global_attrs: tp.Dict):
    """Process adcp data

    FIXME EXPLAIN THE PROCESSING WORKFLOW FIXME

    Parameters
    ----------
    params :
        Processing parameters from the ConfigFile.

    gloabal_attrs :
        Global attributes  parameter from the configFile.

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

    if params["platform_file"]:
        sensor_metadata = _load_platform(params)

    else:
        l.warning("platform_file missing, defaulting to `mooring` for platform_type.")
        sensor_metadata["platform_type"] = "mooring"

    if sensor_metadata["platform_type"] not in ["mooring", "ship"]:
        raise ValueError("platform_type invalid. Must be one of `mooring` or `ship`")

    if params["navigation_file"]:
        # This is carried before reading the adcp data in case a error arise reading
        # the  navigation netcdf files.
        nav_ds = xr.open_dataset(params["navigation_file"])
        if "lon" not in nav_ds or "lat" not in nav_ds:
            l.warning("Navigation netcdf file is missing u_ship and v_ship.")
            params["navigation_file"] = None

    # ----------------- #
    # LOADING ADCP DATA #
    # ----------------- #
    dataset = _load_adcp_data(params)

    if not params["keep_bt"]:
        for var in ["bt_u", "bt_v", "bt_w", "bt_e", "bt_depht"]:
            if var in dataset:
                dataset = dataset.drop_vars([var])

    # ----------------------------- #
    # ADDING SOME GLOBAL ATTRIBUTES #
    # ----------------------------- #
    # Chief scientist in the ConfigFile is used over the one in the platform file.
    l.section("Adding Global Attributes")

    dataset = dataset.assign_attrs(ADCP_GLOBAL_ATTRIBUTES)
    dataset = dataset.assign_attrs(sensor_metadata)
    dataset = dataset.assign_attrs(global_attrs)

    format_global_attrs(dataset)
    if "sensor_depth" in dataset.attrs:
        if not dataset.attrs["sensor_depth"]:
            _xducer_depth_as_sensor_depth(dataset)

    # ----------------------------------------- #
    # ADDING THE NAVIGATION DATA TO THE DATASET #
    # ----------------------------------------- #
    if params["navigation_file"]:
        l.section("Navigation data")
        nav_ds = nav_ds.interp(time=dataset.time)
        dataset["lon"] = nav_ds.lon
        dataset["lat"] = nav_ds.lat
        l.log(f"lon and lat data added from {params['navigation_file']}")
        if "u_ship" in nav_ds and "v_ship" in nav_ds:
            dataset["u_ship"] = nav_ds.u_ship
            dataset["v_ship"] = nav_ds.v_ship
            l.log(f"u_ship and v_ship data added from {params['navigation_file']}")

    # ----------------------------------- #
    # CORRECTION FOR MAGNETIC DECLINATION #
    # ----------------------------------- #
    if params["magnetic_declination"]:
        _magnetnic_correction(dataset, params["magnetic_declination"])
        dataset.attrs["magnetic_delination"] = (
            str(params["magnetic_declination"]) + " degree east"
        )
    else:
        dataset.attrs["magnetic_delination"] = "No correction carried out."

    # --------------- #
    # QUALITY CONTROL #
    # --------------- #
    if params["quality_control"]:
        _quality_control(dataset, params)
    else:
        no_adcp_quality_control(
            dataset,
        )

    dataset = _drop_beam_data(dataset, params)

    # -------------- #
    # DATA ENCONDING #
    # -------------- #
    _format_data_encoding(dataset)

    # -------------------- #
    # VARIABLES ATTRIBUTES #
    # -------------------- #
    dataset.attrs["VAR_TO_ADD_SENSOR_TYPE"] = VAR_TO_ADD_SENSOR_TYPE

    if not dataset.attrs["platform_type"]:
        dataset.attrs["platform_type"] = "mooring"
        l.log("Platform type defaulted to `mooring` for BODC velocity variables name")

    dataset.attrs["P01_CODES"] = {
        **P01_VEL_CODES[dataset.attrs["platform_type"]],
        **P01_CODES,
    }

    l.section("Variables attributes")
    dataset = format_variables_names_and_attributes(
        dataset, use_bodc_codes=params["bodc_name"]
    )

    dataset["time"].assign_attrs(TIME_ATTRS)

    l.log("variables attributes added.")

    # ------------------------------------ #
    # FINAL FORMATING OF GLOBAL ATTRIBUTES #
    # ------------------------------------ #

    dataset.attrs["platform"] = dataset.attrs.pop("platform_name")

    for attrs in GLOBAL_ATTRS_TO_DROP:
        if attrs in dataset.attrs:
            del dataset.attrs[attrs]

    # ------- #
    # OUTPUTS #
    # ------- #
    # Clearing some gloabal attributes
    if not dataset.attrs["date_created"]:
        dataset.attrs["date_created"] = pd.Timestamp.now().strftime("%Y-%m-%d")

    dataset.attrs["date_modified"] = pd.Timestamp.now().strftime("%Y-%m-%d")

    dataset.attrs["logbook"] += l.logbook
    dataset.attrs["history"] = dataset.attrs["logbook"]

    for attr in dataset.attrs:
        if not dataset.attrs[attr]:
            dataset.attrs[attr] = "N/A"

    del dataset.attrs["logbook"]
    if "xducer_depth" in dataset.attrs:
        del dataset.attrs["xducer_depth"]
    del dataset.attrs["sonar"]

    l.section("Output")
    # OUTPUT TODO to_ODF

    nc_output = Path(params["netcdf_output"]).with_suffix(".nc")
    dataset.to_netcdf(nc_output)
    l.log(f"netcdf file made -> {nc_output}")

    log_output = Path(params["netcdf_output"]).with_suffix(".log")  # TODO better

    if params["make_log"]:
        with open(log_output, "w") as log_file:
            log_file.write(dataset.history)
            print(f"log file made -> {log_output}")

    # MAKE_FIG TODO


def _load_adcp_data(params: tp.Dict) -> tp.Type[xr.Dataset]:
    """
    Load an trim the adcp data.
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
        for key in ["platform_name", "platform_type"]:
            if key in platform_dict:
                sensor_metadata[key] = platform_dict[key]
        if "sensors" in platform_dict:
            if params["sensor_id"] in platform_dict["sensors"]:
                sensor_metadata = {
                    **sensor_metadata,
                    **platform_dict["sensors"][params["sensor_id"]],
                }
            else:
                l.warning(
                    f"{params['sensor_id']} not found in {params['platform_id']}['sensor'] of the platform file."
                )
        else:
            l.warning("`sensors` section missing from platform file")

        # Adding the keys with None Value if missing.
        for key in sensor_metadata:
            if key not in PLATFORM_FILE_KEYS:
                sensor_metadata[key] = None

    else:
        l.warning(f"{params['platform_id']} not found in platform file")
        sensor_metadata = None

    return sensor_metadata


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
    """Correct for magnetic declination and adds `magnetic_declination`
    to dataset attributes."""

    if "lon" in dataset and "lat" in dataset:
        dataset.lon.values, dataset.lat.values = magnetic_to_true(
            dataset.lon, dataset.lat, magnetic_declination
        )
        l.log(f"Coordinates transformed to true North and True East.")

    if "heading" in dataset:
        dataset.heading.values = dataset.heading.data - magnetic_declination
        l.log(f"Heading transformed to true North.")


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


def _xducer_depth_as_sensor_depth(dataset: tp.Type[xr.Dataset]):
    """Set xducer_depth value to dataset attributes sensor_depth"""
    if not dataset.attrs["sensor_depth"]:
        if "xducer_depth" in dataset:
            dataset.attrs["sensor_depth"] = np.median(dataset["xducer_depth"].data)

        if "xducer_depth" in dataset.attrs:
            dataset.attrs["sensor_depth"] = dataset.attrs["xducer_depth"]


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
        elif var != "time_string":
            dataset[var].encoding = {"dtype": DATA_DTYPE, "_FillValue": DATA_FILL_VALUE}

    l.log(f"adcp Data _FillValue: {DATA_FILL_VALUE}")
    l.log(f"Ancillary Data _FillValue: {DATA_FILL_VALUE}")

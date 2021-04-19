"""
Script to process adcp data.

- Load
- Quality_Control
- MetaData
- Export -> .nc or .odf
- Ancillary variables names (gen vs bodc)
"""
import os
import typing as tp
from configparser import ConfigParser

import numpy as np
import pandas as pd
import xarray as xr
from magtogoek.adcp.loader import load_adcp_binary
from magtogoek.adcp.quality_control import (adcp_quality_control,
                                            no_adcp_quality_control)
from magtogoek.bin.configfile import get_config_default
from magtogoek.metadata.variable_attrs import add_dataset_variables_attributes
from magtogoek.tools import get_gps_bearing, magnetic_to_true, vincenty
from magtogoek.utils import Logger, json2dict
from pandas import Timestamp

l = Logger(level=0)

from pathlib import Path

CONFIG_GLOBAL_ATTRS_SECTIONS = ["NETCDF_CF", "PROJECT", "CRUISE", "GLOBAL_ATTRIBUTES"]

SDN_FILE_PATH = os.path.join(os.path.dirname(__file__), "../files/sdn.json")

P01_VEL_NAMES = dict(
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
P01_NAMES = dict(
    time="ELTMEP01",
    depth="PPSAADCP",
    pg="PCGDAP01",
    pg1="PCGDAP00",
    pg2="PCGDAP02",
    pg3="PCGDAP03",
    pg4="PCGDAP04",
    cor1="CMAGZZ01",
    cor2="CMAGZZ02",
    cor3="CMAGZZ03",
    cor4="CMAGZZ04",
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


SENSOR_TYPE_ATTRS = ["TEMPPR01", "PRESPR01", "ADEPZZ01", "BATHDPTH"]

XDUCER_DEPTH_ATTRS = {"ADEPZZ01": "Transducer depth"}

TIME_ATTRS = {"cf_role": "profil_id"}  # standard_name

TIME_ENCODING = {
    "units": "Seconds since 1970-1-1 00:00:00Z",
    "calendar": "gregorian",
    "_FillValue": None,
}
DEPTH_ENCODING = {"_FillValue": None}

FILL_VALUE = -9999
DTYPE = "float32"


def process_adcp(config: tp.Type[ConfigParser]):
    """FIXME"""
    l.reset()

    params, global_attrs = _load_config(config)

    sensor_meta = None
    if params["platform_file"]:
        sensor_meta = _load_platform(params)

    dataset = _load_adcp_data(params)

    if params["magnetic_declination"]:
        _magnetnic_correction(dataset, params["magnetic_declination"])

    if params["navigation_file"]:
        # TODO load navigation dataset
        nav = xr.open_dataset(params["navigation_file"])
        # Add u_ship and v_ship to dataset
        pass

    _quality_control_flags(dataset, params)

    _drop_beam_data(dataset, params)

    _format_data_encoding(dataset)

    dataset.attrs["platform_type"] = sensor_meta["platform_type"]
    _format_variables_attributes(dataset, bodc_name=params["bodc_name"])

    # _add_gloabal_attrs()

    # Add platform sensor_depth to metadata. expected_sensor_depth ?


def _load_adcp_data(params: tp.Dict) -> tp.Tpye[xr.Dataset]:
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

    return dataset


def _magnetnic_correction(dataset: tp.Type[xr.Dataset], magnetic_declination: float):
    """Correct for magnetic declination and adds `magnetic_declination`
    to dataset attributes."""

    dataset.lon.values, dataset.lat.values = magnetic_to_true(
        dataset.lon, dataset.lat, magnetic_declination
    )
    dataset.attrs["magnetic_delination"] = magnetic_declination


def _load_config(config: tp.Type[ConfigParser]):
    """Flattens the config to a unested_dict""" ""
    params = dict()
    global_attrs = dict()
    for section, options in config.items():
        if section in CONFIG_GLOBAL_ATTRS_SECTIONS:
            for option in options:
                gloabal_attrs[option] = config[section][option]
        else:
            for option in options:
                params[option] = config[section][option]

    return params, global_attrs


def _load_platform(params: dict) -> tp.Dict:
    """load platform metadata for sensor into dict"""
    sensor_meta = dict()
    p = json2dict(params["platform_file"])
    if params["platform_id"] in p:
        platform = p[params["platform_id"]]
        for key in ["platform_name", "platform_type"]:
            if key in params:
                sensor_meta[key] = platform[key]

        if params["sensor_id"] in platform:
            sensor_meta = {**params, **platform["sensor_id"]}
        else:
            l.warning(
                "f{params['sensor_id']} of f{params['platform_id']}not found in platform file"
            )
            sensor = None
    else:
        l.warning(f"{params['platform_id']} not found in platform file")
        platform = None

    if params["platform_type"] not in ["mooring", "ship"]:
        raise ValueError("platform_type invalid. Must be one of `mooring` or `ship`")

    return sensor_meta


def _quality_control_flags(dataset: tp.Type[xr.Dataset], params: tp.Dict):
    """Carries quality control if `params['quality_control]` is True else
    adds flags of value 0.

    Calls adcp_quality_control or no_adcp_quality_control"""
    if params["quality_control"]:
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
    else:
        no_adcp_quality_control(
            dataset,
        )


def _format_data_encoding(dataset: tp.Type[xr.Dataset]):
    """FIXME"""
    for var in dataset.variables:
        if var == "time":
            dataset.time.encoding = TIME_ENCODING
        elif var == "depth":
            dataset.depth.encoding = DEPTH_ENCODING
        elif "_QC" in var:
            dataset[var].values = dataset[var].values.astype("int8")
            dataset[var].encoding = {"dtype": "int8", "_FillValue": 0}
        elif var != "time_string":
            dataset[var].encoding = {"dtype": DTYPE, "_FillValue": FILL_VALUE}


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
            return (Timestamp(trim_arg), None)
        else:
            return (None, int(trim_arg))
    else:
        return (None, None)


def _drop_beam_data(dataset: tp.Type[xr.Dataset], params: tp.Dict):
    """FIXME"""
    for var in [
        ("pg", "percent_good"),
        ("corr", "correlation"),
        ("amp", "amplitude"),
    ]:
        if var[0] in dataset and params[f"drop_{var[1]}"]:
            dataset = dataset.drop_vars([var[0]])
            l.log(f"var[1] data dropped.")


def _format_variables_attributes(dataset: tp.Type[xr.Dataset], bodc_name: bool):
    """Format variables names and attributes"""
    dataset.time.attrs["cf_role"] = "profil_id"

    for var in dataset.variables:
        dataset[var].attrs["generic_name"] = var

    for var in SENSOR_TYPE_ATTRS:
        if var in dataset:
            dataset[var].attrs["sensor_type"] = "adcp"

    dataset = _convert_variables_names(dataset)

    add_dataset_variables_attributes(dataset, json2dict(SDN_FILE_PATH))

    if not bodc_name:
        dataset = _convert_variables_names(dataset, convert_back_to_generic=True)

    _add_sensor_depth(dataset)


def _convert_variables_names(
    dataset: tp.Type[xr.Dataset], convert_back_to_generic: bool = False
):
    """Convert variable and coords names.

    From generic to BODC P01 names or BODC P01 to generic if
    `convert_to_generic` is True.

    Parameters
    ----------
    dataset :
        ...
    convert_to_generic:
       converts from bodc to generitc.
    """
    if dataset.attrs["platform_type"]:
        p01_names = {**P01_VEL_NAMES[dataset.attrs["platform_type"]], **P01_NAMES}
    else:
        p01_names = {**P01_VEL_NAMES["mooring"], **P01_NAMES}
        l.log("Platform type defaulted to `mooring` for BODC velocity variables name")

    if convert_back_to_generic:
        p01_names = dict((item, key) for key, item in p01_names.items())

    print(p01_names)
    for key in tuple(p01_names.keys()):
        if key not in dataset:
            del p01_names[key]

    dataset = dataset.rename(p01_names)

    return dataset


def _add_sensor_depth(dataset: tp.Type[xr.Dataset]):
    """FIXME"""
    sensor_depth = ""
    if "xducer_depth" in dataset:
        sensor_depth = dataset["xducer_depth"].median()

    if "xducer_depth" in dataset.attrs:
        sensor_depth = dataset.attrs["xducer_depth"]

    for var in dataset.variables:
        if dataset[var].attrs["params_type"] == "adcp":
            dataset[var].attrs["sensor_depth"] = sensor_depth

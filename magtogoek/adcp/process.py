"""
Script to process adcp data.

- Load
- Quality_Control
- MetaData
- Export -> .nc or .odf
"""
import typing as tp
from configparser import ConfigParser

import numpy as np
import pandas as pd
import xarray as xr
from magtogoek.adcp.loader import load_adcp_binary
from magtogoek.adcp.quality_control import (adcp_quality_control,
                                            no_adcp_quality_control)
from magtogoek.bin.configfile import get_config_default
from magtogoek.tools import get_gps_bearing, magnetic_to_true, vincenty
from magtogoek.utils import Logger, json2dict
from pandas import Timestamp

l = Logger(level=0)

from pathlib import Path

CONFIG_GLOBAL_ATTRS = ["NETCDF_CF", "PROJECT", "CRUISE", "GLOBAL_ATTRIBUTES"]


def process_adcp(config: tp.Type[ConfigParser]):
    """FIXME"""
    l.reset()

    params, global_attrs = _load_config(config)

    if params["platform_file"]:
        _load_platform(params)

    dataset = _load_adcp_data(params)

    if params["magnetic_declination"]:
        _magnetnic_correction(dataset, params["magnetic_declination"])

    _quality_control_flags(dataset, params)


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
        if section in CONFIG_GLOBAL_ATTRS:
            for option in options:
                gloabal_attrs[option] = config[section][option]
        else:
            for option in options:
                params[option] = config[section][option]

    return params, global_attrs


def _load_platform(params: dict):
    """load platform metadata into params
    Chief Scientist in configfile overwrites the one in platform sensor.
    """
    p = json2dict(params["platform_file"])
    if params["platform_id"] in p:
        platform = p[params["platform_id"]]
        for key in ["platform_name", "platform_type"]:
            if key in params:
                params[key] = platform[key]

        if params["sensor_id"] in platform:
            sensor = platform["sensor_id"]
            if params["chief_scientist"]:
                del sensor["chief_scientist"]
            params = {**params, **sensor}

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

    return platform, sensor


def _add_sensor_attributes(dataset: tp.Type[xr.Dataset], params: dict):
    """FIXME"""
    if params["params_depth"] == "":

        if "xducer_depth" in dataset:
            params["params_depth"] == dataset["xducer_depth"].median()

        if "xducer_depth" in dataset.attrs:
            params["params_depth"] == dataset.attrs["xducer_depth"]

        for var in dataset.variables:
            if dataset[var].attrs["params_type"] == "adcp":
                dataset[var].attrs = {
                    "serial_number": params["serial_number"],
                    "params_depth": params["params_depth"],
                }


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

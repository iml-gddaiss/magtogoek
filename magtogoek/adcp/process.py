"""
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
from magtogoek.tools import get_gps_bearing, magnetic_to_true, vincenty
from magtogoek.utils import Logger, json2dict

l = Logger(level=0)

from pathlib import Path

CONFIG_GLOBAL_ATTRS_SECTIONS = ["NETCDF_CF", "PROJECT", "CRUISE", "GLOBAL_ATTRIBUTES"]

SDN_FILE_PATH = os.path.join(os.path.dirname(__file__), "../files/sdn.json")

PLATFORM_FILE_KEYS = [
    "platform_name",
    "platform_type",
    "sensor_type",
    "sensor_depth",
    "serial_number",
    "manufacturer",
    "model",
    "firmware_version",
    "chief_scientist",
    "description",
]
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

LONG_NAME_ATTRS = {"ADEPZZ01": "transducer depth"}

TIME_ATTRS = {"cf_role": "profil_id"}

TIME_ENCODING = {
    "units": "Seconds since 1970-1-1 00:00:00Z",
    "calendar": "gregorian",
    "_FillValue": None,
}
DEPTH_ENCODING = {"_FillValue": None}

FILL_VALUE = -9999
DTYPE = "float32"


def process_adcp_config(config: tp.Type[ConfigParser]):
    """Wrap around _process_adcp_data

    Looks for `merge` value and if False, process each files one by one.

    See Also
    --------
    _process_adcp_data :
        For the processing workflow.


    """
    params, global_attrs = _load_config(config)

    if not params["merge_output_files"]:
        params["merge"] = True
        for fn, count in zip(params["input_files"], range(len(params["input_files"]))):
            if params["netcdf_output"]:
                params["netcdf_output"] = (
                    Path(params["netcdf_output"]).with_suffix("") + f"_{count}"
                )
            params["input_files"] = list(fn)

            _process_adcp_data(params, global_attrs)
    else:
        _process_adcp_data(params, global_attrs)


def _process_adcp_data(params: tp.Dict, global_attrs: tp.Dict):
    """Process adcp data

    EXPLAIN THE PROCESSING WORKFLOW

    Notes
    -----
    If `sensor_depth` value is present in the platform.json file, it is used
    for the `sensor_depth` attributes but not for processing. Otherwise,
    `sensor_depth` is computed from xducer_depth.
    """
    l.reset()

    if params["platform_type"] not in ["mooring", "ship"]:
        raise ValueError("platform_type invalid. Must be one of `mooring` or `ship`")

    if params["navigation_file"]:
        # This is carried before reading the adcp data in case a error arise reading the netcdf.
        nav_ds = xr.open_dataset(params["navigation_file"])
        if "u_ship" not in nav_ds or "v_ship" not in nav_ds:
            l.warning("Navigation netcdf file is missing u_ship and v_ship.")
            params["navigation_file"] = None

    dataset = _load_adcp_data(params)
    dataset.attrs = global_attrs

    _geospatial_global_attrs(dataset)
    _time_global_attrs(dataset)

    if params["navigation_file"]:
        nav_ds = nav_ds.interp(time=dataset.time)
        dataset["u_ship"] = nav_ds.u_ship
        dataset["v_ship"] = nav_ds.v_ship

    if params["platform_file"]:
        dataset.attrs = _load_platform(params)

    if not dataset.attrs["sensor_depth"]:
        _xducer_depth_as_sensor_depth(dataset)

    # DO global attributes here ?

    if params["magnetic_declination"]:
        _magnetnic_correction(dataset, params["magnetic_declination"])
        dataset.attrs["magnetic_delination"] = params["magnetic_declination"]

    if params["quality_control"]:
        _quality_control(dataset, params)
    else:
        no_adcp_quality_control(
            dataset,
        )

    _drop_beam_data(dataset, params)

    _format_data_encoding(dataset)

    dataset = _format_variables_names_and_attributes(
        dataset, bodc_name=params["bodc_name"]
    )

    if not dataset.attrs["date_created"]:
        dataset.attrs["date_created"] = pd.Timestamp.now().strftime("%Y-%m-%d")

    dataset.logbook += l.logbook
    # OUTPUT
    dataset.to_netcdf(params["netcdf_output"])

    # MAKE_LOG

    # MAKE_FIG


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
    sensor_metadata = dict()
    p = json2dict(params["platform_file"])
    if params["platform_id"] in p:
        platform = p[params["platform_id"]]
        for key in ["platform_name", "platform_type"]:
            if key in platform:
                sensor_metadata[key] = platform[key]

        if params["sensor_id"] in platform:
            sensor_metadata = {**params, **platform["sensor_id"]}
        else:
            l.warning(
                "f{params['sensor_id']} of f{params['platform_id']}not found in platform file"
            )

        # Adding the keys iwht None Value if missing.
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


def _magnetnic_correction(dataset: tp.Type[xr.Dataset], magnetic_declination: float):
    """Correct for magnetic declination and adds `magnetic_declination`
    to dataset attributes."""

    dataset.lon.values, dataset.lat.values = magnetic_to_true(
        dataset.lon, dataset.lat, magnetic_declination
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
            return (pd.Timestamp(trim_arg), None)
        else:
            return (None, int(trim_arg))
    else:
        return (None, None)


def _xducer_depth_as_sensor_depth(dataset: tp.Type[xr.Dataset]):
    """Set xducer_depth value to dataset attributes sensor_depth"""
    if not dataset.attrs["sensor_depth"]:
        if "xducer_depth" in dataset:
            dataset.attrs["sensor_depth"] = dataset["xducer_depth"].median()

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
        if var[0] in dataset and params[f"drop_{var[1]}"]:
            dataset = dataset.drop_vars([var[0]])
            l.log(f"var[1] data dropped.")


def _format_variables_names_and_attributes(
    dataset: tp.Type[xr.Dataset], bodc_name: bool
) -> tp.Type[xr.Dataset]:
    """Format variables names and attributes

    Returns dataset with variables attributes set.

    Convert variables names to BODC and then adds CF and SeaDataNet attributes
    to variables.

    Parameters
    ----------

    """
    dataset.time.attrs["cf_role"] = "profil_id"

    for var in dataset.variables:
        dataset[var].attrs["generic_name"] = var

    for var in SENSOR_TYPE_ATTRS:
        if var in dataset:
            dataset[var].attrs["sensor_type"] = "adcp"

    dataset = _convert_variables_names(dataset)

    _add_sdn_and_cf_var_attrs(dataset, json2dict(SDN_FILE_PATH))

    if not bodc_name:
        dataset = _convert_variables_names(dataset, convert_back_to_generic=True)

    _add_sensor_depth_to_var_attrs(dataset)
    _add_data_min_max_to_var_attrs(dataset)
    if dataset.attrs["serial_number"]:
        _add_sensor_serial_to_var_attrs(dataset)

    _add_ancillary_variables_to_var_attrs(dataset)
    _add_names_to_QC_var_attrs(dataset)

    return dataset


def _convert_variables_names(
    dataset: tp.Type[xr.Dataset], convert_back_to_generic: bool = False
):
    """Convert variable and coords names.

    From generic to BODC P01 names or from BODC P01 to generic names if
    `convert_back_to_generic` is True.

    Parameters
    ----------
    dataset :
        FIXME
    convert_to_generic:
       converts from bodc to generitc.
    Notes
    -----
    Conveting names is used to add the conventionned attributes to variables.
    """
    if dataset.attrs["platform_type"]:
        p01_names = {**P01_VEL_NAMES[dataset.attrs["platform_type"]], **P01_NAMES}
    else:
        p01_names = {**P01_VEL_NAMES["mooring"], **P01_NAMES}
        l.log("Platform type defaulted to `mooring` for BODC velocity variables name")

    if convert_back_to_generic:
        # mapping key and value and value to key
        p01_names = dict((value, key) for key, value in p01_names.items())

    for key in tuple(p01_names.keys()):
        if key not in dataset:
            del p01_names[key]

    dataset = dataset.rename(p01_names)

    return dataset


def _add_sdn_and_cf_var_attrs(dataset: tp.Type[xr.Dataset], sdn: tp.Dict) -> None:
    """add sdn (sea data net) attributes.

    Parameters
    ----------
    sdn :
        sdn is a dictionnary with the P01 variable Code as `key` and dictionnary
    of attributes as `value`. The dictionnary is saved as a json file in
    magtogoek/files/sdn.json

    Notes
    -----
    SeaDataNet attributes include:
     -'standard_name'
     -'units'
     -'long_name'
     -'ancillary_variables'
     -'sdn_parameter_urn'
     -'sdn_parameter_name'
     -'sdn_uom_urn'
     -'sdn_uom_name'
     -'legacy_GF3_code'

    """
    variables = set(dataset.variables).intersection(set(sdn.keys()))
    for var in variables:
        dataset[var].attrs = sdn[var]


def _add_data_min_max_to_var_attrs(dataset):
    """adds data max and min to variables except ancillary and coords variables)"""
    for var in set(dataset.variables).difference(set(dataset.coords)):
        if "_QC" not in var:
            if dataset[var].dtype == float:
                dataset[var].attrs["data_max"] = dataset[var].max().values
                dataset[var].attrs["data_min"] = dataset[var].min().values


def _add_sensor_depth_to_var_attrs(dataset: tp.Type[xr.Dataset]):
    """Add sensor depth to variables using XducerDepth."""
    for var in dataset.variables:
        if dataset[var].attrs["sensor_type"] == "adcp":
            dataset[var].attrs["sensor_depth"] = dataset["sensor_depth"]


def _add_sensor_serial_to_var_attrs(dataset: tp.Type[xr.Dataset]):
    """Add sensor serial number `dataset['serial_number'] to variables using XducerDepth."""
    for var in dataset.variables:
        if dataset[var].attrs["sensor_type"] == "adcp":
            dataset[var].attrs["serial_number"] = dataset["serial_number"]


def _add_ancillary_variables_to_var_attrs(dataset: tp.Type[xr.Dataset]):
    """add accillary_variables to variables attributes

    Looks for `_QC` variable names and adds 'ancillary_variables` attributes
    to the corresponding variables.
    """
    for var in list(dataset.variables):
        if "_QC" in var:
            dataset[var.split("_")[0]].attrs["ancillary_variables"] = var


def _add_names_to_QC_var_attrs(dataset: tp.Type[xr.Dataset]) -> None:
    """add long_name and standard_name to QualityControl `_QC` variables."""
    for var in list(dataset.variables):
        if "_QC" in var:
            dataset[var].attrs["long_name"] = f"Quality flag for {var.split('_')[0]}"
            dataset[var].attrs[
                "standard_name"
            ] = f"Quality flag for {var.split('_')[0]}"


def _time_global_attrs(dataset: tp.Type[xr.Dataset]):
    """
    Notes
    -----
    Attributes added :
     -time_coverage_start
     -time_coverage_end
     -time_coverage_duration
     -time_coverage_duration_units (days)
    """
    dataset.attrs["time_coverage_start"] = str(
        dataset.time.data[0].astype("datetime64[s]")
    )
    dataset.attrs["time_coverage_end"] = str(
        dataset.time.data[-1].astype("datetime64[s]")
    )
    number_day = np.round(
        (dataset.time[-1].data - dataset.time.data[0]).astype(float)
        / (1e9 * 60 * 60 * 24),
        2,
    )

    dataset.attrs["time_coverage_duration"] = number_day
    dataset.attrs["time_coverage_duration_units"] = "days"


def _geospatial_global_attrs(dataset: tp.Type[xr.Dataset]):
    """Compute and add geospatial global attributes to dataset.

    If `lon` and `lon` are variables in the dataset, lat/lon
    min and max are compute from them. If `lon` and `lat`
    are not present, the values are taken form the `longitude` and
    `latitude` dataset attributes.

    The 'longitude' and 'latitude' attributes shoud previously be
    taken from the platform file attributes

    Notes
    -----
    Attributes added :
     -sounding
     -geospatial_lat_min
     -geospatial_lat_max
     -geospatial_lat_units
     -geospatial_lon_min
     -geospatial_lon_max
     -geospatial_lon_units
     -geospatial_vertical_min
     -geospatial_vertical_max
     -geospatial_vertical_positive
     -geospatial_vertical_units
    """

    if dataset.attrs["platform_type"] != "ship":
        if "bt_depth" in dataset:
            dataset.attrs["sounding"] = dataset.bt_depth.median()

    if "lat" in dataset:
        dataset.attrs["geospatial_lat_min"] = dataset.lat.min()
        dataset.attrs["geospatial_lat_max"] = dataset.lat.max()
        dataset.attrs["geospatial_lat_units"] = "degrees north"
    elif dataset.attrs["longitude"]:
        dataset.attrs["geospatial_lat_min"] = dataset.attrs["longitude"]
        dataset.attrs["geospatial_lat_max"] = dataset.attrs["longitude"]
        dataset.attrs["geospatial_lat_units"] = "degrees north"

    if "lon" in dataset:
        dataset.attrs["geospatial_lon_min"] = dataset.lon.min()
        dataset.attrs["geospatial_lon_max"] = dataset.lon.max()
        dataset.attrs["geospatial_lon_units"] = "degrees east"
    elif dataset.attrs["latitude"]:
        dataset.attrs["geospatial_lon_min"] = dataset.attrs["latitude"]
        dataset.attrs["geospatial_lon_max"] = dataset.attrs["latitude"]
        dataset.attrs["geospatial_lon_units"] = "degrees east"

    dataset.attrs["geospatial_vertical_min"] = dataset.depth.min()
    dataset.attrs["geospatial_vertical_max"] = dataset.depth.max()
    dataset.attrs["geospatial_vertical_positive"] = "down"
    dataset.attrs["geospatial_vertical_units"] = "meters"

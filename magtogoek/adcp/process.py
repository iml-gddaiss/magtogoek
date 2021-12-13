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

TODO TEST NAVIGATION FILES !
Note DATA_TYPES: Missing for ship adcp. Set to adcp for now
FIXME SOURCE : moored adcp ?

Notes
-----
Should be a class
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
from magtogoek.adcp.tools import rotate_2d_vector
from magtogoek.attributes_formatter import (
    compute_global_attrs, format_variables_names_and_attributes)
from magtogoek.navigation import load_navigation
from magtogoek.utils import Logger, json2dict, format_str2list
from magtogoek.platforms import _add_platform

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
    "variables_gen_name",
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

DATE_STRING_FILL_VALUE = "17-NOV-1858 00:00:00.00"  # filled value used by ODF format
QC_FILL_VALUE = 127
QC_ENCODING = {"dtype": "int8", "_FillValue": QC_FILL_VALUE}

DATA_FILL_VALUE = -9999.0
DATA_ENCODING = {"dtype": "float32", "_FillValue": DATA_FILL_VALUE}


def process_adcp(config: dict):
    """Process adcp data with parameters from a ConfigFile.

    Pipes the params to _to_process_adcp_data which in turn pipes
    it to _process_adcp_data.

    Using `platform_id`, `sensor_id`, the sensor metadata are loaded
    into a dictionary and pass to _process_adcp_data.

    Notes
    -----
    missing `platform_type` :
        If the platform_type cannot be found, the function automatically default to
        `mooring` to set BODC P01 parameter codes.

    See Also
    --------
    _process_adcp_data :
        For the processing workflow.

    """
    params, config_attrs = _get_config(config)

    params["input_files"] = format_str2list(params["input_files"])

    if len(params["input_files"]) == 0:
        raise ValueError("No adcp file was provided in the configfile.")

    platform_metadata = _default_platform()
    if params["platform_file"]:
        if Path(params["platform_file"]).is_file():
            platform_metadata = _load_platform(params)
        else:
            l.warning(f"platform_file, {params['platform_file']}, not found")
    else:
        if params["platform_type"]:
            platform_metadata["platform"]['platform_type'] = params["platform_type"]
    _pipe_to_process_adcp_data(params, platform_metadata, config_attrs)


def quick_process_adcp(params: tp.Dict):
    """Process adcp data with quick_process options(params).

    Pipes the params to _to_process_adcp_data which in turn pipes
    it to _process_adcp_data.

    Notes
    -----
    missing `platform_type` :
        If the platform_type cannot be found, the function automatically default to
        `mooring` to set the correct BODC P01 parameter codes.

    See Also
    --------
    _process_adcp_data :
        For the processing workflow."""

    config_attrs = _get_default_config_attrs()
    platform_metadata = _default_platform()

    platform_metadata['platform']["platform_type"] = params["platform_type"]

    params["force_platform_metadata"] = False
    if params["odf_output"] in [1, "true", "True", 't', "T"]:
        params["odf_output"] = True

    _pipe_to_process_adcp_data(
        params, platform_metadata, config_attrs, drop_empty_attrs=True
    )


def _pipe_to_process_adcp_data(
        params, platform_metadata, config_attrs, drop_empty_attrs=False
):
    """Check if the input_file must be split in multiple output.

        Looks for `merge_output_files` in the ConfigFile and if False,
    each file in `input_files` is process individually and then call _process_adcp_data.
    """

    if not params["merge_output_files"]:
        netcdf_output = params["netcdf_output"]
        input_files = params["input_files"]
        for filename, count in zip(input_files, range(len(input_files))):
            if netcdf_output:
                if isinstance(netcdf_output, bool):
                    params["netcdf_output"] = filename
                else:
                    params["netcdf_output"] = Path(netcdf_output).absolute().resolve()
                    if params["netcdf_output"].is_dir():
                        params["netcdf_output"] = str(params["netcdf_output"].joinpath(filename))
                    else:
                        params["netcdf_output"] = str(params["netcdf_output"].with_suffix("")) + f"_{count}"
            params["input_files"] = [filename]

            _process_adcp_data(params, platform_metadata, config_attrs, drop_empty_attrs)
    else:
        _process_adcp_data(params, platform_metadata, config_attrs)


def _process_adcp_data(
        params: tp.Dict, platform_metadata: tp.Dict, config_attrs, drop_empty_attrs=False
):
    """Process adcp data

    FIXME EXPLAIN THE PROCESSING WORKFLOW FIXME

    Meanwhile, the code is pretty explicit. Go check it out if need be.


    Parameters
    ----------
    params :
        Processing parameters from the ConfigFile.

    config_attrs :
        Global attributes parameter from the configFile.

    platform_metadata :
        Metadata from the platform file.

    Notes
    -----
    `sensor_depth`:
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

    _check_platform_type(platform_metadata)
    platform_type = platform_metadata['platform']['platform_type']

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

    dataset = dataset.assign_attrs(STANDARD_ADCP_GLOBAL_ATTRIBUTES)

    dataset.attrs["data_type"] = DATA_TYPES[platform_type]
    dataset.attrs["data_subtype"] = DATA_SUBTYPES[platform_type]

    if platform_metadata['platform']["longitude"]:
        dataset.attrs["longitude"] = platform_metadata['platform']["longitude"]
    if platform_metadata['platform']["latitude"]:
        dataset.attrs["latitude"] = platform_metadata['platform']["latitude"]

    compute_global_attrs(dataset)

    if platform_metadata['platform']["platform_type"] in ["mooring", "buoy"]:
        if "bt_depth" in dataset:
            dataset.attrs["sounding"] = np.round(np.median(dataset.bt_depth.data), 2)

    # if not params["force_platform_metadata"]: # Note Probably useless.
    _set_xducer_depth_as_sensor_depth(dataset)

    # setting Metadata from the platform_file
    _set_platform_metadata(dataset, platform_metadata, 'adcp', params["force_platform_metadata"])

    # setting Metadata from the config_files
    dataset = dataset.assign_attrs(config_attrs)

    if not dataset.attrs["source"]:
        dataset.attrs["source"] = platform_type

    # ----------------------------------- #
    # CORRECTION FOR MAGNETIC DECLINATION #
    # ----------------------------------- #

    l.section("Data transformation")

    if dataset.attrs['magnetic_declination'] is not None:
        l.log(f"Magnetic declination found in the raw file: {dataset.attrs['magnetic_declination']} degree east.")
    else:
        l.log(f"No magnetic declination found in the raw file.")
    if params["magnetic_declination"]:
        angle = params["magnetic_declination"]
        if dataset.attrs["magnetic_declination"]:
            angle = round((params["magnetic_declination"] - dataset.attrs["magnetic_declination"]), 4)
            l.log(f"An additional correction of {angle} degree east was applied.")
        _apply_magnetic_correction(dataset, angle)
        dataset.attrs["magnetic_declination"] = params["magnetic_declination"]
        l.log(f"Absolute magnetic declination: {dataset.attrs['magnetic_declination']} degree east.")

    # --------------- #
    # QUALITY CONTROL #
    # --------------- #

    dataset.attrs["logbook"] += l.logbook

    if params["quality_control"]:
        _quality_control(dataset, params)
    else:
        no_adcp_quality_control(dataset, )

    l.reset()

    if any(
            params["drop_" + var] for var in ("percent_good", "correlation", "amplitude")
    ):
        dataset = _drop_beam_data(dataset, params)

    # ------------- #
    # DATA ENCODING #
    # ------------- #
    _format_data_encoding(dataset)

    # -------------------- #
    # VARIABLES ATTRIBUTES #
    # -------------------- #
    dataset.attrs["VAR_TO_ADD_SENSOR_TYPE"] = VAR_TO_ADD_SENSOR_TYPE
    dataset.attrs["P01_CODES"] = {
        **P01_VEL_CODES[platform_type],
        **P01_CODES,
    }
    dataset.attrs['variables_gen_name'] = [var for var in dataset.variables]

    l.section("Variables attributes")
    dataset = format_variables_names_and_attributes(
        dataset, use_bodc_codes=params["bodc_name"]
    )

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
    # ODF OUTPUTS #
    # ----------- #
    netcdf_path, odf_path, log_path = _make_outputs(params['input_files'][0],
                                                    params['odf_output'],
                                                    params['netcdf_output'])

    l.section("Output")
    if odf_path:
        if params['odf_data'] is None:
            params['odf_data'] = 'both'
        odf_data = {'both': ['VEL', 'ANC'], 'vel': ['VEL'], 'anc': ['ANC']}[params['odf_data']]
        for qualifier in odf_data:
            _ = make_odf(
                dataset=dataset,
                platform_metadata=platform_metadata,
                config_attrs=config_attrs,
                bodc_name=params['bodc_name'],
                event_qualifier2=qualifier,
                output_path=odf_path,
            )

    # --------------------------------------- #
    # FORMATTING GLOBAL ATTRIBUTES FOR OUTPUT #
    # --------------------------------------- #
    for attr in GLOBAL_ATTRS_TO_DROP:
        if attr in dataset.attrs:
            del dataset.attrs[attr]

    for attr in list(dataset.attrs.keys()):
        if not dataset.attrs[attr]:
            if drop_empty_attrs:
                del dataset.attrs[attr]
            else:
                dataset.attrs[attr] = ""

    # ---------- #
    # NC OUTPUTS #
    # ---------- #
    if not isinstance(netcdf_path, bool):
        netcdf_path = Path(netcdf_path).with_suffix('.nc')
        dataset.to_netcdf(netcdf_path)
        l.log(f"netcdf file made -> {netcdf_path}")

    if params["make_log"]:
        log_path = Path(log_path).with_suffix(".log")
        with open(log_path, "w") as log_file:
            log_file.write(dataset.attrs["history"])
            print(f"log file made -> {log_path.resolve()}")

    # MAKE_FIG TODO

    click.echo(click.style("=" * TERMINAL_WIDTH, fg="white", bold=True))


def _load_adcp_data(params: tp.Dict) -> xr.Dataset:
    """
    Load and trim the adcp data into a xarray.Dataset.
    Drops bottom track data if params `keep_bt` is False.
    """
    start_time, leading_index = _get_datetime_and_count(params["leading_trim"])
    end_time, trailing_index = _get_datetime_and_count(params["trailing_trim"])

    dataset = load_adcp_binary(
        filenames=params["input_files"],
        yearbase=params["yearbase"],
        sonar=params["sonar"],
        leading_index=leading_index,
        trailing_index=trailing_index,
        orientation=params["adcp_orientation"],
        sensor_depth=params["sensor_depth"],
        bad_pressure=params["bad_pressure"],
        start_time=params["start_time"],
        time_step=params["time_step"],
    )

    dataset = cut_bin_depths(dataset, params["depth_range"])

    dataset = cut_times(dataset, start_time, end_time)

    l.log(
        (
                f"Bins count : {len(dataset.depth.data)}, "
                + f"Min depth : {np.round(dataset.depth.min().data, 3)} m, "
                + f"Max depth : {np.round(dataset.depth.max().data, 3)} m"
        )
    )
    l.log(
        (
                f"Ensembles count : {len(dataset.time.data)}, "
                + f"Start time : {np.datetime_as_string(dataset.time.min().data, unit='s')}, "
                + f"End time : {np.datetime_as_string(dataset.time.max().data, unit='s')}"
        )
    )
    if not params["keep_bt"]:
        dataset = _drop_bottom_track(dataset)

    return dataset


def _get_config(config: dict) -> tp.Tuple[dict, dict]:
    """Split and flattens the config in two untested dictionary"""
    params = dict()
    config_attrs = dict()
    for section, options in config.items():
        if section in CONFIG_GLOBAL_ATTRS_SECTIONS:
            for option in options:
                config_attrs[option] = config[section][option]
        else:
            for option in options:
                params[option] = config[section][option]

    return params, config_attrs


def _get_default_config_attrs():
    """Return default config_attrs()"""
    return {
        "date_created": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "publisher_name": getpass.getuser(),
        "source": "adcp",
    }


def _load_platform(params: dict) -> tp.Dict:
    """load sensor metadata into dict

    Returns a `flat` dictionary with all the parents metadata
    to `platform.json/platform_id/sensors/sensor_id` and the
    metadata of the `sensor_id.`

    """
    platform_metadata = _default_platform()
    json_dict = json2dict(params["platform_file"])
    if params["platform_id"] in json_dict:
        platform_metadata['platform'].update(json_dict[params["platform_id"]])
        if 'buoy_specs' in platform_metadata['platform']:
            platform_metadata['buoy_specs'].update(platform_metadata['platform'].pop('buoy_specs'))
        if 'sensors' in platform_metadata['platform']:
            platform_metadata['sensors'].update(platform_metadata['platform'].pop('sensors'))
            if params["sensor_id"] in platform_metadata["sensors"]:
                platform_metadata['adcp_id'] = params["sensor_id"]
                platform_metadata['adcp'].update(platform_metadata["sensors"].pop(params["sensor_id"]))
            else:
                l.warning(
                    f"{params['sensor_id']} not found in the {params['platform_id']}['sensor'] section "
                    f"of the platform file."
                )
        else:
            l.warning(
                f"sensors section missing in the {params['platform_id']} section of the platform file."
            )
    else:
        l.warning(f"{params['platform_id']} not found in platform file.")

    return platform_metadata


def _default_platform() -> dict:
    """Return an empty platform data dictionary"""
    platform_metadata = {'platform': _add_platform(), 'adcp_id': 'ADCP_01'}
    platform_metadata['platform']["platform_type"] = DEFAULT_PLATFORM_TYPE
    platform_metadata['sensors'] = platform_metadata['platform'].pop('sensors')
    platform_metadata['adcp'] = platform_metadata['sensors'].pop('__enter_a_sensor_ID_here')
    platform_metadata['buoy_specs'] = platform_metadata['platform'].pop('buoy_specs')

    return platform_metadata


def _check_platform_type(platform_metadata: dict):
    """DEFINED BELOW"""
    if platform_metadata['platform']["platform_type"] not in PLATFORM_TYPES:
        platform_metadata['platform']["platform_type"] = DEFAULT_PLATFORM_TYPE
        l.warning(
            f"platform_file missing or invalid, defaulting to `{DEFAULT_PLATFORM_TYPE}` for platform_type."
        )
        l.warning(f"platform_type invalid. Must be one of {PLATFORM_TYPES}")


_check_platform_type.__doc__ = f"""Check if the `platform_type` is valid.
    `platform _type` must be one of {PLATFORM_TYPES}.
    `platform_type` defaults to {DEFAULT_PLATFORM_TYPE} if the one given is invalid."""


def _set_xducer_depth_as_sensor_depth(dataset: xr.Dataset):
    """Set xducer_depth value to dataset attributes sensor_depth"""
    if "xducer_depth" in dataset.attrs:  # OCEAN SURVEYOR
        dataset.attrs["sensor_depth"] = dataset.attrs["xducer_depth"]

    if "xducer_depth" in dataset:
        dataset.attrs["sensor_depth"] = np.round(
            np.median(dataset["xducer_depth"].data), 2
        )


def _set_platform_metadata(
        dataset: xr.Dataset,
        platform_metadata: tp.Dict[str, dict],
        sensor: str,
        force_platform_metadata: bool = False,
):
    """Add metadata from platform_metadata files to dataset.attrs.

    Values that are dictionary instances are not added.

    Parameters
    ----------
    dataset :
        Dataset to which add the navigation data.
    platform_metadata :
        metadata returned by  _load_platform
    force_platform_metadata :
        If `True`, metadata from sensor_metadata overwrite those already present in dataset.attrs
    """
    metadata = {**platform_metadata['platform'], **platform_metadata[sensor]}
    metadata['sensor_comments'] = metadata['comments']
    if force_platform_metadata:
        for key, value in metadata.items():
            dataset.attrs[key] = value
        if "sensor_depth" in metadata:
            l.log(
                f"`sensor_depth` value ({platform_metadata['sensor_depth']} was set by the user."
            )

    else:
        for key, value in metadata.items():
            if key in dataset.attrs:
                if not dataset.attrs[key]:
                    dataset.attrs[key] = value
            else:
                dataset.attrs[key] = value


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
    nav_ds = load_navigation(navigation_files).interp(time=dataset.time)
    for var in ['lon', 'lat', 'u_ship', 'v_ship']:
        if var in nav_ds:
            dataset[var] = nav_ds[var]
            if var == "lat":
                l.log('Platform GPS data loaded.')
            if var == "v_ship":
                l.log('Platform velocity data loaded.')
    nav_ds.close()

    return dataset


def _quality_control(dataset: xr.Dataset, params: tp.Dict):
    """Carries quality control.

    Wrapper for adcp_quality_control"""

    adcp_quality_control(dataset=dataset, amp_th=params["amplitude_threshold"], corr_th=params["correlation_threshold"],
                         pg_th=params["percentgood_threshold"], roll_th=params["roll_threshold"],
                         pitch_th=params["pitch_threshold"], horizontal_vel_th=params["horizontal_velocity_threshold"],
                         vertical_vel_th=params["vertical_velocity_threshold"],
                         error_vel_th=params["error_velocity_threshold"],
                         motion_correction_mode=params["motion_correction_mode"],
                         sidelobes_correction=params["sidelobes_correction"], bottom_depth=params["bottom_depth"])


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
    if all(v in dataset for v in ['bt_u', 'bt_v']):
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


def _get_datetime_and_count(trim_arg: str):
    """Get datetime and count from trim_arg.

    If `trim_arg` is None, returns (None, None)
    If 'T' is a datetime or a count returns (Timestamp(trim_arg), None)
    Else returns (None, int(trim_arg))

    Returns:
    --------
    datetime:
        None or pandas.Timestamp
    count:
        None or int

    """
    if trim_arg:
        if not trim_arg.isdecimal():
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


def _drop_beam_data(dataset: xr.Dataset, params: tp.Dict):
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
    "Drop `bt_u`, `bt_v`, `bt_w`, `bt_e`, `bt_depth`"
    for var in ["bt_u", "bt_v", "bt_w", "bt_e", "bt_depth"]:
        if var in dataset:
            dataset = dataset.drop_vars([var])
    return dataset


def cut_bin_depths(
        dataset: xr.Dataset,
        depth_range: tp.Union[int, float, list] = None
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
                    "depth_range value is greater than the maximum bin depth. Depth slicing aborded."
                )
            else:
                dataset = dataset.sel(depth=slice(depth_range, None))
                l.log(f"Bin of depth inferior to {depth_range} m were cut.")
        elif len(depth_range) == 2:
            if dataset.depth[0] > dataset.depth[-1]:
                depth_range.reverse()
            if depth_range[0] > dataset.depth.max() or depth_range[1] < dataset.depth.min():
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


def cut_times(dataset: xr.Dataset,
              start_time: str = None,
              end_time: str = None) -> xr.Dataset:
    """
    Return a dataset with time cut if they are not outside the dataset time span.

    Parameters
    ----------
    dataset
    start_time :
        minimum time to be included in the dataset.
    end_time
        maximum time to be included in the dataset.
    Returns
    -------
    dataset with times cut.

    """
    out_off_bound_time = False
    if start_time is not None:
        if start_time > dataset.time.max():
            out_off_bound_time = True
    if end_time is not None:
        if end_time < dataset.time.min():
            out_off_bound_time = True
    if out_off_bound_time is True:
        l.warning("Trimming datetimes out of bounds. Time slicing aborted.")
    else:
        dataset = dataset.sel(time=slice(start_time, end_time))

    return dataset


def _make_outputs(input_path: str,
                  odf_output: tp.Union[bool, str],
                  netcdf_output: tp.Union[bool, str]) -> tp.Tuple[tp.Union[bool, str], tp.Union[bool, str], str]:
    """

    Parameters
    ----------
    odf_output
    netcdf_output

    Returns
    -------

    """
    default_path = Path(input_path).parent
    default_filename = Path(input_path).name

    if not odf_output and not netcdf_output:
        netcdf_output = True

    netcdf_path = False
    if isinstance(netcdf_output, bool):
        if netcdf_output is True:
            netcdf_path = default_path.joinpath(default_filename)
    elif isinstance(netcdf_output, str):
        netcdf_output = Path(netcdf_output)
        if Path(netcdf_output.name) == netcdf_output:
            netcdf_path = default_path.joinpath(netcdf_output).resolve()
        elif netcdf_output.absolute().is_dir():
            netcdf_path = netcdf_output.joinpath(default_filename)
        elif netcdf_output.parent.is_dir():
            netcdf_path = netcdf_output
        default_path = netcdf_path.parent
        default_filename = netcdf_path.name
        netcdf_path = str(netcdf_path)
        netcdf_output = True

    odf_path = False
    if isinstance(odf_output, bool):
        if odf_output is True:
            odf_path = default_path
    elif isinstance(odf_output, str):
        odf_output = Path(odf_output)
        if Path(odf_output.name) == odf_output:
            odf_path = default_path.joinpath(odf_output).resolve()
        elif odf_output.is_dir():
            odf_path = odf_output
        elif odf_output.parent.is_dir():
            odf_path = odf_output
        if not netcdf_output:
            default_path = odf_path.parent
            default_filename = odf_path.stem
        odf_path = str(odf_path)

    log_path = str(default_path.joinpath(default_filename))

    return netcdf_path, odf_path, log_path

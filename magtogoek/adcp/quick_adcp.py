"""
Constains functions to quickly process adcp data.

Notes
-----
  - No BODC names for bottom_depth
  - Turns this into an object maybe ?
"""
import os
import typing as tp
from pathlib import Path

import xarray as xr
from magtogoek.adcp.loader import load_adcp_binary
from magtogoek.adcp.quality_control import (adcp_quality_control,
                                            no_adcp_quality_control)
from magtogoek.metadata.variable_attrs import add_dataset_variables_attributes
from magtogoek.tools import magnetic_to_true
from magtogoek.utils import Logger, json2dict
from pandas import Timestamp

l = Logger(level=0)

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
    # time="ELTMEP01",
    # depth="PPSAADCP",
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
    #    bt_depth="sounding", TODO and sounding median() for gloabal attrs
)


SENSOR_TYPE_ATTRS = ["TEMPPR01", "PRESPR01", "ADEPZZ01"]

XDUCER_DEPTH_ATTRS = {"ADEPZZ01": "Transducer depth"}

BT_DEPTH_ATTRS = dict(units="m", long_name="Water depth", generic_name="bt_depth")

TIME_ATTRS = {"cf_role": "profil_id"}  # standard_name

DEPTH_attrs = {
    "positive": "down",
    "units": "meters",
}  # standard_name, long_name bin depth below surface

TIME_ENCODING = {
    "units": "Seconds since 1970-1-1 00:00:00Z",
    "calendar": "gregorian",
    "_FillValue": None,
}
DEPTH_ENCODING = {"_FillValue": None}

FILL_VALUE = -9999
DTYPE = "float32"


def quick_process_adcp(
    input_files: str, sonar: str, yearbase: int, params: tp.Dict = None
):
    """TODO
    Parameters:
    -----------
    TODO

    """
    l.reset()

    if params["platform_type"] not in ["mooring", "ship"]:
        raise ValueError("platform_type invalid. Must be one of `mooring` or `ship`")

    # Ensemble slicing (index and time)
    start_time, leading_index = get_datetime_and_count(params["leading_trim"])
    end_time, trailing_index = get_datetime_and_count(params["trailing_trim"])

    if not params["merge_output_files"]:
        params["merge"] = True
        for fn, count in zip(input_files, range(len(input_files))):
            if params["netcdf_output"]:
                params["netcdf_output"] = (
                    Path(params["netcdf_output"]).with_suffix("") + f"_{count}"
                )

            quick_process_adcp(list(fn), sonar, yearbase, params)
    else:

        sensor_depth = None
        if params["sensor_depth"]:
            sensor_depth = params["sensor_depth"]

        ### LOADING DATA ###
        # - this include triming by indexing.
        dataset = load_adcp_binary(
            input_files,
            yearbase=yearbase,
            sonar=sonar,
            leading_index=leading_index,
            trailing_index=trailing_index,
            orientation=params["adcp_orientation"],
            sensor_depth=sensor_depth,
        )

        ### SLICING DATASET WITH DATETIME ###
        dataset = dataset.sel(time=slice(start_time, end_time))

        if len(dataset.time) == 0:
            l.warning(f"{input_files} time dims is of lenght 0 after slicing.")

        ### MAGNETIC DECLINATION ###
        # TODO add to grloaBL ATTRs (MAGNETIC_DECLINATION)
        if params["magnetic_declination"]:
            dataset.lon.values, dataset.lat.values = magnetic_to_true(
                dataset.lon, dataset.lat, params["magnetic_declination"]
            )

        # QUALITY CONTROL
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

        ### DROPING PG, CORR, AMP ###
        for var in [
            ("pg", "percent_good"),
            ("corr", "correlation"),
            ("amp", "amplitude"),
        ]:
            if var[0] in dataset and params[f"drop_{var[1]}"]:
                dataset = dataset.drop_vars([var[0]])

        ### ENCODING TO SEPARATE IN AN OTHER FUNCTIONS/SCRIPT ###
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

        ###### DATA FORMATING #####
        if "bt_depth" in dataset:
            dataset.bt_depth.attrs = BT_DEPTH_ATTRS

        if params["platform_type"]:
            dataset.attrs["platform_type"] = params["platform_type"]

        _format_variables_attributes(dataset, params["bodc_name"])

        if params["make_figures"]:
            print("make fig not implemented yet")

        # Updateting logbook
        dataset.attrs["logbook"] += l.logbook

        # Exporting to odf TODO
        if params["odf_output"]:
            if params["make_logbook"]:
                pass
            # export_to_odf(dataset, Path(params[odf_output]).with_suffix(".odf"))
            pass
            print("ODF not implemented yet. Defaulting to necdf output.")
            params["odf_output"] = False

        # Exporting to netcdf
        export_nc = (
            not (params["odf_output"] and params["netcdf_output"])
            or params["netcdf_output"]
        )

        if export_nc:
            if params["netcdf_output"]:
                netcdf_output = Path(params["netcdf_output"]).with_suffix(".nc")
            else:
                netcdf_output = Path(input_files[0]).with_suffix(".nc")
            dataset.to_netcdf(netcdf_output)
            print(f"netcdf file made -> {netcdf_output}")
            if params["make_log"]:
                with open(netcdf_output.with_suffix(".log"), "w") as log_file:
                    log_file.write(dataset.logbook)
                    print(f"log file made -> {netcdf_output.with_suffix('.log')}")


def _format_variables_attributes(dataset: tp.Type[xr.Dataset], bodc_name: bool):
    """Format variables names and attributes"""
    for var in dataset.variables:
        if var not in ["depth", "time"]:
            dataset[var].attrs["generic_name"] = var

    dataset.depth.attrs = {"units": "meters"}  # DO ADD COORDS ATTRS

    for var in SENSOR_TYPE_ATTRS:
        if var in dataset:
            dataset[var].attrs["sensor_type"] = "adcp"

    for var in dataset.variables:
        if "sensor_type" in dataset[var].attrs:
            if dataset[var].attrs["sensor_type"] == "adcp":
                dataset[var].attrs["sensor_depth"] = "TODO"

    dataset = _convert_variables_names(dataset)

    add_dataset_variables_attributes(dataset, json2dict(SDN_FILE_PATH))

    if not bodc_name:
        dataset = _convert_variables_names(dataset, convert_to_generic=True)


def _convert_variables_names(
    dataset: tp.Type[xr.Dataset], convert_to_generic: bool = False
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

    if convert_to_generic:
        p01_names = dict((item, key) for key, item in p01_names.items())

    print(p01_names)
    for key in tuple(p01_names.keys()):
        if key not in dataset:
            del p01_names[key]

    dataset = dataset.rename(p01_names)

    return dataset


def get_datetime_and_count(trim_arg: str):
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

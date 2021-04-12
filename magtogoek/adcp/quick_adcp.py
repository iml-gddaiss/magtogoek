"""
Constains functions to quickly process adcp data.
"""
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

P01_VEL_NAMES = dict(
    mooring=dict(u="LCEWAP01", v="LCNSAP01", w="LRZAAP01", e="LERRAP01"),
    ship=dict(u="LCEWAS01", v="LCNSAS01", w="LRZAAS01", e="LERRAS01"),
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
    temperature="TEMPPR01",
    xducer_depth="ADEPZZ01",
    time_string="DTUT8601",
)

SDN_FILE_PATH = "./magtogoek/files/sdn.json"

BT_DEPTH_ATTRS = dict(units="m", long_name="Water depth", generic_name="bt_depth")


def quick_process_adcp(
    input_files: str, sonar: str, yearbase: int, params: tp.Dict = None
):
    """TODO
    Parameters:
    -----------
    TODO

    """

    l.reset()

    if params["platform_type"] and params["platform"] not in ["mooring", "ship"]:
        raise ValueError("platform_type invalid. Must be one of `mooring` or `ship`")

    # get_time_slicing
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

        # Loading
        dataset = load_adcp_binary(
            input_files,
            yearbase=yearbase,
            sonar=sonar,
            leading_index=leading_index,
            trailing_index=trailing_index,
            orientation=params["adcp_orientation"],
            sensor_depth=sensor_depth,
        )

        # Slicing with time
        dataset = dataset.sel(time=slice(start_time, end_time))

        if len(dataset.time) == 0:
            l.warning(f"{input_files} time dims is of lenght 0 after slicing.")

        if params["magnetic_declination"]:
            dataset.lon.values, dataset.lat.values = magnetic_to_true(
                dataset.lon, dataset.lat, params["magnetic_declination"]
            )

        # Quality Control
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

        for var in [
            ("pg", "percent_good"),
            ("corr", "correlation"),
            ("amp", "amplitude"),
        ]:
            if var[0] in dataset and params[f"drop_{var[1]}"]:
                dataset = dataset.drop_vars([var[0]])

        # platform file
        sensor = None
        platform = None
        platform_type = None
        platform_file = params["platform"][0]
        platform_id = params["platform"][1]
        instrument_id = params["platform"][2]
        if platform_file and platform_id and instrument_id:
            platform = json2dict(platform_file)[platform_id]
            platform_type = platform["platform_type"]
            sensor = platform["sensor_id"]

        if params["platform_type"]:
            platform_type = platform_type["platform_type"]

        _generic_to_P01_varname(dataset, platform_type)

        add_dataset_variables_attributes(dataset, json2dict(SDN_FILE_PATH))

        if params["make_fig"]:
            print("make fig not implemented yet")

        # Updateting logbook
        dataset.attrs["logbook"] += l.logbook

        # Exporting to odf
        if params["odf_output"]:
            if params["make_logbook"]:

                pass
            # export2odf(dataset, Path(params[odf_output]).with_suffix(".odf"))
            pass

        # Exporting to netcdf
        if params["netcdf_output"]:
            netcdf_output = Path(params["netcdf_output"]).with_suffix(".nc")
        else:
            netcdf_output = Path(input_files[0]).with_suffix(".nc")

        export_nc = (
            not (params["odf_output"] and params["netcdf_output"])
            or params["netcdf_output"]
        )

        if export_nc:
            dataset.to_netcdf(netcdf_output)
            print(f"netcdf file made -> {netcdf_output}")
            if params["make_log"]:
                with open(netcdf_output.with_suffix(".log"), "w") as log_file:
                    log_file.write(dataset.logbook)
                    print(f"log file made -> {netcdf_output.with_suffix('.log')}")


def _generic_to_P01_varname(dataset: tp.Type[xr.Dataset], platform_type: str):
    """FIXME"""
    if platform_type:
        p01_names = {**P01_VEL_NAMES[platform_type], **P01_NAMES}
    else:
        p01_names = {**P01_VEL_NAMES["ship"], **P01_NAMES}
        l.log("Platform type defaulted to `ship` for BODC velocity varibles name")

    for key in list(p01_names.keys()):
        if key not in dataset:
            del p01_names[key]
    dataset.rename(p01_names)


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

"""
Constains functions to quickly process adcp data.
"""
import typing as tp
from pathlib import Path

from magtogoek.adcp.loader import load_adcp_binary
from magtogoek.adcp.quality_control import (adcp_quality_control,
                                            no_adcp_quality_control)
from magtogoek.utils import Logger
from pandas import Timestamp

l = Logger(level=0)

BODC_VEL_NAMES = dict(
    buoy=[],
    mooring=["LCEWAP01", "LCNSAP01", "LRZAAP01", "LERRAP01"],
    ship=[]
    # LRZUVP01 vertical beam (moored, boy, ship ?)
)


def quick_process_adcp(
    input_files: str, sonar: str, yearbase: int, params: tp.Dict = None
):
    """TODO
    Parameters:
    -----------
    TODO

    """
    # get_time_slicing
    start_time, leading_index = get_datetime_and_count(params["leading_trim"])
    end_time, trailing_index = get_datetime_and_count(params["trailing_trim"])

    l.reset()

    if not params["merge_output_files"]:
        params["merge"] = True
        for fn, count in zip(input_files, range(len(input_files))):
            if params["netcdf_output"]:
                params["netcdf_output"] = (
                    Path(params["netcdf_output"]).with_suffix("") + f"_{count}"
                )

            quick_process_adcp(list(fn), sonar, yearbase, params)
    else:
        # Loading
        dataset = load_adcp_binary(
            input_files,
            yearbase=yearbase,
            sonar=sonar,
            leading_index=leading_index,
            trailing_index=trailing_index,
            orientation=params["adcp_orientation"],
        )
        # Time Slicing
        dataset = dataset.sel(time=slice(start_time, end_time))

        if len(dataset.time) == 0:
            l.warning(f"{input_files} time dims is of lenght 0 after slicing.")

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

        # Platform file
        # Add metadata, (buoy, mooring, ship, drift)

        if params["make_figure"]:
            print("make fig not implemented yet")
            pass

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


def get_datetime_and_count(trim_arg: str):
    """Check if trim_arg is a datetime or a count.

    Returns (Timstamp(trim_arg), None) or (None, int(trim_arg)) or (None,None)

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

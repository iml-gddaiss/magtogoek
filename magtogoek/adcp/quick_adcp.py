"""
Constains functions to quickly process adcp data.
"""
import typing as tp
from pathlib import Path

from magtogoek.adcp.loader import load_adcp_binary
from magtogoek.utils import Logger
from pandas import Timestamp


def quick_process_adcp(
    input_files: str, sonar: str, yearbase: int, params: tp.Dict = None
):
    """TODO
    Parameters:
    -----------
    TODO

    """
    start_time, leading_index = is_datetime_or_count(params["leading_trim"])
    end_time, trailing_index = is_datetime_or_count(params["trailing_trim"])

    l = Logger()

    if params["merge"]:
        # Loading
        ds = load_adcp_binary(
            input_files,
            yearbase=yearbase,
            sonar=sonar,
            leading_index=leading_index,
            trailing_index=trailing_index,
            orientation=params["adcp_orientation"],
        )
        # Time Slicing
        ds = ds.sel(time=slice(start_time, end_time))

        if len(ds.time) == 0:
            l.warning(f"{input_files} time dims is of lenght 0 after slicing.")

        # Quality Control
        if params["qc"]:
            pass

        # Updateting logbook
        ds.attrs["logbook"] += l.logbook

        # Exporting to netcdf
        if params["netcdf_output"]:
            netcdf_output = Path(params["netcdf_output"]).with_suffix(".nc")
        else:
            netcdf_output = Path(input_files[0]).with_suffix(".nc")

        # Exporting to odf
        if params["odf_output"]:
            pass

        ds.to_netcdf(netcdf_output)
        print(f"netcdf file made -> {netcdf_output}")
    else:
        params["merge"] = True
        for fn, count in zip(input_files, range(len(input_files))):
            if params["netcdf_output"]:
                params["netcdf_output"] = Path(params["netcdf_output"]).with_suffix(
                    f"_{count}.nc"
                )

            quick_process_adcp(list(fn), sonar, yearbase, params)


def is_datetime_or_count(trim_arg: str):
    """Check if trim_arg is a datetime or a count.

    Returns (Timstamp(trim_arg), None) or (None, int(trim_arg))

    Returns:
    --------
    datetime:
        None or pandas.Timstamp
    count:
        None or int

    """
    datetime, count = (
        (Timestamp(trim_arg), None) if "T" in trim_arg else (None, int(trim_arg))
    )

    return datetime, count

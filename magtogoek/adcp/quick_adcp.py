"""
Constains functions to quickly process adcp data.
"""
import typing as tp

from magtogoek.adcp.loader import load_adcp_binary
from magtogoek.utils import Logger, validate_filename
from pandas import Timestamp


def quick_adcp(input_files: str, sonar: str, yearbase: int, params: tp.Dict = None):
    """TODO
    Parameters:
    -----------
    TODO

    """
    leading_index, trailing_index = None, None
    start_time, end_time = None, None

    netcdf_output = params["netcdf_output"] = None
    if params["start_time"]:
        if "T" in params["start_time"]:
            start_time = Timestamp(params["start_time"])
        else:
            leading_index = int(params["start_time"])

    if params["end_time"]:
        if "T" in params["end_time"]:
            end_time = Timestamp(params["end_time"])
        else:
            trailing_index = int(params["end_time"])

    if params["merge"]:
        ds = load_adcp_binary(
            input_files,
            yearbase=yearbase,
            sonar=sonar,
            leading_index=leading_index,
            trailing_index=trailing_index,
        )
        l = Logger(ds.logbook)

        ds = ds.sel(time=slice(start_time, end_time))

        if len(ds.time) == 0:
            l.warning(f"{netcdf_output} time dims is of lenght 0 after slicing.")

        ds.attrs["logbook"] = l.logbook
        if params["netcdf_output"]:
            netcdf_output = validate_filename(params["netcdf_output"], ext=".nc")
        else:
            netcdf_output = input_files[0].split(".")[0] + ".nc"

        ds.to_netcdf(netcdf_output)
        print(f"netcdf file made -> {netcdf_output}")
    else:
        for fn, count in zip(input_files, range(len(input_files))):
            ds = load_adcp_binary(
                fn,
                yearbase=yearbase,
                sonar=sonar,
                leading_index=leading_index,
                trailing_index=trailing_index,
            )

            l = Logger(ds.logbook)

            ds = ds.sel(time=slice(start_time, end_time))

            if params["netcdf_output"]:
                netcdf_output = validate_filename(params["netcdf_output"], ext=".nc")
                netcdf_output = netcdf_output.split(".nc")[0] + "_" + str(count) + ".nc"
            else:
                netcdf_output = fn.split(".")[0] + ".nc"

            if len(ds.time) == 0:
                l.warning(f"{netcdf_output} time dims is of lenght 0 after slicing.")
                ds.attrs["logbook"] = l.logbook

            ds.to_netcdf(netcdf_output)
            print(f"netcdf file made -> {netcdf_output}")

"""
author: Jérôme Guay
date: Feb. 22, 2021
based in part  on: https://github.com/jeanlucshaw/adcp2nc/
                   https://github.com/hhourston/pycurrents_ADCP_processign

This script contains functions to read adcp files and load them in xarray.Dataset.
There is two loader; one for Teldyne RDI files and one for Rowtech files.

(NOT WORKING)Rowtech files can also be exporter directly to Teledyne `PD0` file formats and be proecess
 by the RDI loader. Testing still need to be done with the Rowtech `PD0` format
and the RDI loader.

The RDI loader uses CODAS Multiread reader from the pycurrent pacakge. The Multiread
reader supports .000, .ENX, .ENS, .LTA and .STA binary files.

-Sentinel V encoding is not fully supported. ID 0x7000 to 0x7004 will be printed.

Summary of load_rdi_binary() function:
parameters: sonar ('wh', 'sv', 'os'), yearbase, adcp_orientation 'up' or 'down',
            sensor_depth, motion_correction `True` or `False`.
-: First, the loader look into all the FixedLeader of each pings to look for
   invalid configuration in the SysCfg and rise Warning if one is founrd. 
-: If sonar is "os", the loader assumes that`dep` (depth vector coordinate)
   in the RDI file is relative to the sea surface. It also assumes that no
   pressure data is available.
-: If sonar is "wh" or "sv", the loader assumes that `dep` is relative the the
   transducer and uses `XducerDepth` to compute the depth
   vector relative to the surface.
-: If the coordsystem is `beam`, velocity data are transform to the `earth`
   coordinate system. Except for the fifth Beam of `SV` sonar.
-: In `earth` or `xyz` coordinate, only `PercentGood4` is return as `pg` to
   apply threshold to the 4 beam solution. If the data is in `beam` coordinate,
   the average of the 4 beam percent good is computed and returned.
-: If the bottrack values are all 0, they are removed from the ouput dataset.
-: For `os` sonar, the loader looks for navigation data. None are return if
   they are not found.
-: Uses the `sensor_depth` to compare it with `XducerDepth` (transducer depth)
   in the data file.

The RTI loader is stil in the making.
The RDI loader still need to be tested for sw_pd0

See Also
--------
   * pycurrents.adcp.rdiraw.Multiread

Note
----
"""
import logging
import typing as tp
from pathlib import Path

import click
import numpy as np
import pandas as pd
import xarray as xr
from magtogoek.adcp.utils import *
from nptyping import NDArray
from pycurrents.adcp import rdiraw, transform
from pycurrents.adcp.rdiraw import Bunch, Multiread, rawfile

# This is to prevent pycurrents from printing error.
logging.getLogger(rdiraw.__name__).setLevel("CRITICAL")


class CoordinateSystemError(Exception):
    pass


def load_rdi_binary(
    filenames: tp.Tuple[str, tp.List[str]],
    sonar: str,
    yearbase: int,
    orientation: str,
    sensor_depth: float = None,
    silent: bool = False,
):
    """Load RDI adcp data.

    Return a dataset with the ADCP data loaded.

    Parameters
    ----------
    filenames:
        Path/to/files
    sonar:
        Type of sonar (`os`, `wh`, `sv`, `sw_pd0`) #TODO SEAWATCH
    yearbase:
        year that the sampling begun.
    orientation:
        Adcp orientation. Either `up` or `down`
    sensor_depth:
        Depth of the ADCP. Use to compare with XducerDeppth median
    silent:
       Silence the log prints if True
    Returns
    -------
        Dataset with the loaded adcp data

    """
    l = Logger()
    l.silence(silent)

    l.section("Loading RDI", t=True)
    if isinstance(filenames, list):
        filenames.sort()
        l.log(
            "Files:"
            + "      ".join([p.name + "\n" for p in list(map(Path, filenames))])
        )
    else:
        l.log(f"File: {Path(filenames).name}")

    sw_flag = False
    if sonar == "sw_pd0":
        sonar = "wh"
        sw_flag = True
        l.log("Loading SW PD0 files")

    if sonar == "sv":
        l.log(
            [
                "WARNING: (from pycurrents) The SV support is under development.  Missing features:",
                "        - The 0x7000-0x7004 IDs are not being parsed and stored.",
                "        - The `Fixed Leader` can change within a file",
                "        - See pycurrents.adcp.rdiraw module for for information",
            ]
        )

    # ------------------------------ #
    # Reading the files FixedLeaders #
    # ------------------------------ #
    fl = read_fixed_leader(filenames=filenames, sonar=sonar, yearbase=yearbase)
    if (fl["SysCfg"] == 2 ** 16 - 1).any():
        nbad = np.sum((fl["SysCfg"] == 2 ** 16 - 1))
        l.log(
            f"WARNING: Invalide configuration, msb=`11111111` and lsb=`11111111`, found in the SysCfg of {nbad} FixedLeader "
        )

    # ------------------------ #
    # Reading the data file(s) #
    # ------------------------ #
    data = Multiread(fnames=filenames, sonar=sonar, yearbase=yearbase).read()

    # ---------------------------- #
    # Convert `dday` to datetime64 #
    # ---------------------------- #
    bad_time = False
    if (data.dday < 0).any() or (np.diff(data.dday) < 0).any():
        bad_time = True
        l.log(
            [
                f"WARNING: The `dday` vector either contains negative values or is not monotonically increasing."
                f"WARNING: Time was replaced by a default datetime vector: 1 second timestep since {yearbase}"
            ]
        )
        time, time_string = dday_to_datetime64(
            np.arange(len(data.dday)) / (3600 * 24), yearbase
        )
    else:
        time, time_string = dday_to_datetime64(data.dday, yearbase)

    # ----------------------------------------------------------- #
    # Convert depth relative to the ADCP to depth below surface   #
    # ----------------------------------------------------------- #
    if (
        data.sonar.model != "os"
    ):  # We assume that for OceanSurveillor dep output are depth below surface.
        XducerDepth = np.median(data.XducerDepth)
        if sensor_depth is not None:
            l.log(
                f"The difference between `sensor_depth` and `XDucerDepth` is {abs(sensor_depth - XducerDepth)} m"
            )
        if orientation == "down":
            depth = XducerDepth + data.dep
        else:
            depth = XducerDepth - data.dep

    # --------------------- #
    # Initating the dataset #
    # --------------------- #
    ds = init_dataset(time, data.dep, sonar=data.sonar.model)

    # --------------------------------------- #
    # Dealing with the coordinates system     #
    # --------------------------------------- #
    original_coordsystem = data.trans["coordsystem"]
    if original_coordsystem != "earth":
        l.log(f"The velocity data are in {data.trans['coordsystem']} coordinate")

        coordsystem2earth(data=data, orientation=orientation)

        if data.trans["coordsystem"] == "xyz":
            l.log(
                "WARNING: Roll, Pitch or Heading seems to be missing from the data file."
            )
        l.log(f"The velocity data were transformed to {data.trans['coordsystem']}")

    # --------------------------- #
    # Loading the transducer data #
    # --------------------------- #

    # Set velocity values of -32768.0 to nans, since -32768.0 is the automatic fill_value for pycurrents
    data.vel.data[data.vel.data == -32768.0] = np.nan

    ds["u"].values = np.asarray(data.vel.data[:, :, 0].T)
    ds["v"].values = np.asarray(data.vel.data[:, :, 1].T)
    ds["w"].values = np.asarray(data.vel.data[:, :, 2].T)
    ds["e"].values = np.asarray(data.vel.data[:, :, 3].T)

    if data.sonar.model == "sv":
        data.vbvel.data[data.vbvel.data == -32768.0] = np.nan

        ds["vb_vel"].values = np.asarray(data.vbvel.T)
        # ds["vb_pg"].values = np.asarray(data.vb_pg.T)
        ds["vb_corr"].values = np.asarray(data.VBCorrelation.T)
        ds["vb_amp"].values = np.asarray(data.VBIntensity.T)
        l.log("Data from the Sentinel V fifth beam loaded.")

    if not (data.bt_vel.data == 0).all():
        ds["bt_u"].values = np.asarray(data.bt_vel.data[:, 0])
        ds["bt_v"].values = np.asarray(data.bt_vel.data[:, 1])
        ds["bt_w"].values = np.asarray(data.bt_vel.data[:, 2])
        ds["bt_e"].values = np.asarray(data.bt_vel.data[:, 3])
        ds["bt_depth"].values = np.asarray(np.nanmean(data.bt_depth.data, axis=-1))
        l.log("Bottom track data loaded")
    else:
        ds = ds.drop_vars(names=["bt_u", "bt_v", "bt_w", "bt_e", "bt_depth"])
        l.log(
            "Bottom track values were all `0` and so they were dropped from the ouput."
        )

    if original_coordsystem == "beam":
        # For `sv` model, pg was not present in the pycurrents output. This is to prevent further Error.
        try:
            ds["pg"].values = np.asarray(np.mean(data.pg.data, axis=2).T)
            l.log(
                "Percent good was computed by averaging each beam PercentGood. The raw data were in beam coordinate."
            )
        except AttributeError:
            l.log("WARNING: Percent good was not retrieve from the dataset.")
    else:
        ds["pg"].values = np.asarray(data.pg4.T)

    for i in range(1, 5):
        ds[f"corr{i}"].values = np.asarray(data[f"cor{i}"].T)
        ds[f"amp{i}"].values = np.asarray(data[f"amp{i}"].T)

    # ------------------ #
    # Loading depth data #
    # ------------------ #

    # For `wh` and `sv`, XducerDepth varies over times but is a constant for `os`.
    if data.sonar.model != "os":
        ds["xducer_depth"].values = np.asarray(data.XducerDepth)
    else:
        ds = ds.drop_vars(names=["xducer_depth"])
        XducerDepth = data.XducerDepth[0]

    ds.attrs["_vartmp_XducerDepth"] = XducerDepth

    # --------------------------- #
    # Loading the naviagtion data #
    # --------------------------- #
    if "rawnav" in data:
        ds["lon"].values = np.array(data["rawnav"]["Lon1_BAM4"] * 180.0 / 2 ** 31)
        ds["lat"].values = np.array(data["rawnav"]["Lat1_BAM4"] * 180.0 / 2 ** 31)
        l.log(" Navigation (GPS) data loaded.")
    else:
        ds = ds.drop_vars(names=["lon", "lat"])

    # -------------------------------------------- #
    # Quick checkup and loading of other variables #
    # -------------------------------------------- #
    # For `wh` and `sv` the pressure is added if available.
    if data.sonar.model != "os":
        if (data.VL["Pressure"] == 0).all():
            ds = ds.drop_vars(["pres"])
            l.log("Pressure data unavailable")
        else:
            ds["pres"].values = data.VL["Pressure"] / 1000  # decapascal to decibar
    else:
        ds = ds.drop_vars(["pres"])

    if (data.heading == 0).all() or (np.diff(data.heading) == 0).all():
        l.log("WARNING: Heading data are either all 0, or not variying.")
    if (data.roll == 0).all() or (np.diff(data.roll) == 0).all():
        l.log("WARNING: Roll data are either all 0, or not variying.")
    if (data.pitch == 0).all() or (np.diff(data.pitch) == 0).all():
        l.log("WARNING: Pitch data are either all 0, or not variying.")
    if (data.temperature == 0).all() or (np.diff(data.temperature) == 0).all():
        l.log("WARNING: Temperature data are either all 0, or not variying.")

    ds["heading"].values = np.asarray(data.heading)
    ds["roll_"].values = np.asarray(data.roll)
    ds["pitch"].values = np.asarray(data.pitch)
    ds["temp"].values = np.asarray(data.temperature)

    ds["time_string"].values = time_string
    if bad_time is True:
        ds["dday"] = (["time"], data.dday)

    if orientation == "up":
        ds.sortby("depth")

    ds.attrs["coordsystem"] = data.trans["coordsystem"]

    # Attributes
    ds.attrs["beam_angle"] = data.sysconfig["angle"]
    ds.attrs["ping_frequency"] = data.sysconfig["kHz"] * 1000
    ds.attrs["bin_size"] = data.CellSize
    ds.attrs["orientation"] = orientation

    l.log(f"File(s) loaded with {l.w_count} warnings")
    ds.attrs["logbook"] = l.logbook

    return ds, fl


def init_dataset(time: NDArray, depth: NDArray, sonar: str = None):
    """Make a default dataset for adcp.

    Return a default dataset with empty DataArray.

    Initialize a DataArrays for a fifth beam data if `sonar` == "sv".

    Parameters
    ----------
    time:
        vector of datetime64[]

    depth:
        vector of [float/int]

    sonar:
        Type of sonar. (`wh`, `sv`, etc).
    """

    data_vars = {
        "u": (["depth", "time"], nans(depth.shape + time.shape)),
        "v": (["depth", "time"], nans(depth.shape + time.shape)),
        "w": (["depth", "time"], nans(depth.shape + time.shape)),
        "e": (["depth", "time"], nans(depth.shape + time.shape)),
        "pg": (["depth", "time"], nans(depth.shape + time.shape)),
        "amp1": (["depth", "time"], nans(depth.shape + time.shape)),
        "amp2": (["depth", "time"], nans(depth.shape + time.shape)),
        "amp3": (["depth", "time"], nans(depth.shape + time.shape)),
        "amp4": (["depth", "time"], nans(depth.shape + time.shape)),
        "corr1": (["depth", "time"], nans(depth.shape + time.shape)),
        "corr2": (["depth", "time"], nans(depth.shape + time.shape)),
        "corr3": (["depth", "time"], nans(depth.shape + time.shape)),
        "corr4": (["depth", "time"], nans(depth.shape + time.shape)),
        "lon": (["time"], nans(time.shape)),
        "lat": (["time"], nans(time.shape)),
        "roll_": (["time"], nans(time.shape)),
        "pitch": (["time"], nans(time.shape)),
        "heading": (["time"], nans(time.shape)),
        # "uship": (["time"], nans(time.shape)),
        # "vship": (["time"], nans(time.shape)),
        "bt_u": (["time"], nans(time.shape)),
        "bt_v": (["time"], nans(time.shape)),
        "bt_w": (["time"], nans(time.shape)),
        "bt_e": (["time"], nans(time.shape)),
        "bt_depth": (["time"], nans(time.shape)),
        "xducer_depth": (["time"], nans(time.shape)),
        "temp": (["time"], nans(time.shape)),
        "pres": (["time"], nans(time.shape)),
        "time_string": (["time"], nans(time.shape)),
    }

    if sonar == "sv":
        data_vars = {
            **data_vars,
            "vb_vel": (["depth", "time"], nans((depth.shape + time.shape))),
            "vb_amp": (["depth", "time"], nans((depth.shape + time.shape))),
            "vb_corr": (["depth", "time"], nans((depth.shape + time.shape))),
            # "vb_pg": (["depth", "time"], nans((depth.shape + time.shape))), missing
        }

    dataset = xr.Dataset(
        data_vars=data_vars,
        coords={"depth": (["depth"], depth), "time": (["time"], time)},
    )

    return dataset


def coordsystem2earth(data: tp.Type[Bunch], orientation: str):
    """Transforms beam and xyz coordinates to enu coordinates

    NOTE: not properly tested. But it should work.

    Replace the values of data.vel, data.bt_vel with East, North and Up velocities
    and the velocity error for 4 beams ADCP. UHDAS transform functions are used to
    transform for beam coordinates and xyz to east-north-up (enu). which uses a
    three-beam solution by faking a fourth beam.

    Also change the values of of `coordinates` and `tilts` in data.trans.

    beam coordinates : Velocity measured along beam axis.
    xyz corrdinates : Velocity in a cartesian coordinate system in the ADCP frame of refence.
    enu coordinates : East North Up measured using the heading, pitch, roll of the ADCP.

    Parameters
    ----------
    data:
        Multiread.read()

    orientation:
        adcp orientation. Either `up` or `down`.

    Errors:
    -------
    ValueError :
        coordinates system no recognized.
    """

    if data.trans.coordsystem not in ["beam", "xyz"]:
        CoordinateSystemError(
            f"coordsystem value of {data.sysconfig.coordsystem} not recognized. Conversion to enu not available."
        )
    beam_pattern = "convex" if data.sysconfig.convex else "concave"
    xyze, xyze_bt = data.vel.data, data.bt_vel.data

    if data.trans.coordsystem == "beam":
        trans = transform.Transform(angle=data.sysconfig.angle, geometry=beam_pattern)
        xyze = trans.beam_to_xyz(data.vel.data)
        bt_xyze = trans.beam_to_xyz(data.bt_vel.data)

    if (data.heading == 0).all() or (data.roll == 0).all() or (data.pitch == 0).all():
        data.trans["coordsystem"] = "xyz"

        for i in range(4):
            data.vel.data[:, :, i] = np.round(xyze[:, :, i], decimals=3)
            data.bt_vel.data[:, i] = np.round(bt_xyze[:, i], decimals=3)
    else:
        enu = transform.rdi_xyz_enu(
            xyze,
            data.heading,
            data.pitch,
            data.roll,
            orientation=orientation,
        )
        bt_enu = transform.rdi_xyz_enu(
            bt_xyze,
            data.heading,
            data.pitch,
            data.roll,
            orientation=orientation,
        )
        data.trans["coordsystem"] = "earth"

        for i in range(4):
            data.vel.data[:, :, i] = np.round(enu[:, :, i], decimals=3)
            data.bt_vel.data[:, i] = np.round(bt_enu[:, i], decimals=3)


def read_fixed_leader(
    filenames: tp.Tuple[str, tp.List[str]], sonar: str, yearbase: int
):
    """Read Teledyne RDI binary FixedLeader.

    Using: rawfile().read() to get the FixedLeader for all  pings.

    Parameters
    ----------
    fnames :
        File(s) to read.
    sonar :
        sonar type passed to pycurrents.Multiread.
        ('nb', 'bb', 'wh', 'sv', or 'os')
    yearbase :
        start year of the sampling.

    Returns
    -------
    fixed_leader:
        ADCP data from rawfile.read() with the .

    Notes:
    ------
    Althought the fixed_leader is supposed to be fixed, there is occurence
    of change in the fixed_leader of some ping. A check up of some
    the fixed_leader parameters is done in the  processing.
    """
    # uses rawfile() to get the FixedLeader.
    if isinstance(filenames, list):
        fixed_leader = np.concatenate(
            [
                rawfile(fname=fname, sonar=sonar, yearbase=yearbase)
                .read(varlist=["FixedLeader"])
                .raw.FixedLeader
                for fname in filenames
            ]
        )
    else:
        fixed_leader = (
            rawfile(fname=filenames, sonar=sonar, yearbase=yearbase)
            .read(varlist=["FixedLeader"])
            .raw.FixedLeader
        )

    return fixed_leader


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    ios_path = (
        "/home/jeromejguay/ImlSpace/Projects/"
        + "pycurrents_ADCP_processing/sample_data/"
    )
    ios_fns = [
        "a1_20050503_20050504_0221m.000",
        "a1_20160713_20170513_0480m.000",
        "eh2_20060530_20060717_0007m.000",
    ]

    sillex_path = "/media/jeromejguay/5df6ae8c-2af4-4e5b-a1e0-a560a316bde3/home/jeromejguay/WorkSpace_2019/Data/Raw/ADCP/"
    sillex_fns = [
        "COR1805-ADCP-150kHz009_000001",
        "COR1805-ADCP-150kHz009_000002",
    ]

    v50exp = (
        "/media/jeromejguay/Bruno/TREX2020/V50/TREX2020_V50_20200911T121242_003_*.ENX"
    )
    v100file = (
        "/media/jeromejguay/Bruno/TREX2020/V100/TREX2020_V100_20200911T115335.pd0"
    )

    pd0_sw_path = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/sw_300_4beam_20deg_piston.pd0"
    ens_sw_path = (
        "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/rowetech_seawatch.ens"
    )

    # files = [sillex_path + fn for fn in sillex_fns]
    # sonar = "os"
    # enr = load_rdi_binary(
    #    [f + ".ENR" for f in files], sonar=sonar, yearbase=2018, orientation="down"
    # )
    # ens = load_rdi_binary(
    #    [f + ".ENS" for f in files], sonar=sonar, yearbase=2018, orientation="down"
    # )
    # enx = load_rdi_binary(
    #    [f + ".ENX" for f in files], sonar=sonar, yearbase=2018, orientation="down"
    # )

    # sonar = "wh"
    # ios0 = load_rdi_binary(
    #    ios_path + ios_fns[0], sonar=sonar, yearbase=2005, orientation="down"
    # )
    # ios1 = load_rdi_binary(
    #    ios_path + ios_fns[1], sonar=sonar, yearbase=2016, orientation="down"
    # )
    # ios2 = load_rdi_binary(
    #    ios_path + ios_fns[2], sonar=sonar, yearbase=2006, orientation="down"
    # )

    # v50path = Path(v50exp)
    # v50files = list(map(str, v50path.parent.glob(v50path.name)))
    # sonar = "sv"

    # v50 = load_rdi_binary(v50files, sonar=sonar, yearbase=2020, orientation="down")

    #    v100 = load_rdi_binary(v100file, sonar=sonar, yearbase=2020, orientation="down")

    sw = load_rdi_binary(ens_sw_path, sonar="sw_pd0", yearbase=2020, orientation="down")

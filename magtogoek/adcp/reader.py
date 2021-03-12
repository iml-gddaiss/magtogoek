"""
author: Jérôme Guay
date: Feb. 22, 2021
based-on: https://github.com/jeanlucshaw/adcp2nc/
          and https://github.com/hhourston/pycurrents_ADCP_processign

This script contains functions to read adcp files and load them in xarray.Dataset.
There is two loader; one for Teldyne RDI files and one for Rowtech files. Rowtech
files can also be exporter directly to Teledyne .P01 file formats and be proecess
 by the RDI loader. Testing still need to be done with the Rowtech P01 format
and the RDI loader.

The RDI loader uses CODAS Multiread reader from the pycurrent pacakge. The Multiread
reader supports .000, .ENX, .ENS, .LTA and .STA binary files. However, the ouput
from Multiread is then process by the loader and testing is style ongoing for some
of the file formats, but it should work just fine.

Summary of load_rdi_binary() function:
parameters: sonar ('wh', 'sv', 'os'), yearbase, adcp_orientation 'up' or 'down',
            sensor_depth, motion_correction `True` or `False`.
-: First, the loader look into all the FixedLeader of each pings to look for
   inconsistancy/variability in the SysCfg.
-: Uses the `sensor_depth` to compare it with `XducerDepth` (transducer depth)
   in the data file. If a significant difference is found (+/- 5 m), `sensor_depth`
   will be used for further computation.
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

The RTI loader is stil in the making.

See Also
--------
   * pycurrents.adcp.rdiraw.Multiread

Note
----
"""
import typing as tp
from pathlib import Path

import click
import numpy as np
import pandas as pd
import xarray as xr
from nptyping import NDArray
from pycurrents.adcp import transform
from pycurrents.adcp.rdiraw import Bunch, Multiread, rawfile


class Logger:
    def __init__(self, logbook=""):
        self.logbook = "" + logbook
        self.w_count = 0

    def __repr__(self):
        return self.logbook

    def section(self, msg, t=False):
        time = "" if t is False else " " + self.timestamp()
        self.logbook += "[" + msg + "]" + time + "\n"
        print(msg)

    def log(self, msg, t=False, w=False):
        if "WARNING:" in msg:
            click.echo(click.style("WARNING:", fg="yellow") + msg[8:])
            self.w_count += 1
        else:
            msg = msg if w is False else msg + " " + str(self.w_count) + " Warnings"
            print(msg)
        msg = msg if t is False else self.timestamp() + " " + msg
        self.logbook += "  -" + msg + "\n"

    @staticmethod
    def timestamp():
        return "(" + pd.Timestamp.now().strftime("%Y-%m-%d %Hh%M:%S") + ")"


def load_rdi_binary(
    filenames: tp.Tuple[str, tp.List[str]],
    sonar: str,
    yearbase: int,
    orientation: str,
    sensor_depth: float = None,
):
    """FIXME
    TODO PARSING MULTIPLE FILES"""
    l = Logger()
    l.section("Loading RDI", t=True)
    if isinstance(filenames, list):
        l.log("Files:\n" + "      \n".join(map(Path, filenames).name))
    else:
        l.log(f"File: {Path(filenames).name}")

    fl_flag = 0
    fl = read_fixed_leader(filenames, sonar=sonar, yearbase=yearbase)
    ### --- En faire une fonction --- ###
    for name in fl.dtype.names:
        if np.unique(fl[name]).size > 1:
            l.log(f"WARNING: Problem detected in the fixed leader with {name}")
            fl_flag += 1

    eturn_counts = False
    ### --- Fin de la fonction --- ###

    # read binary data. TODO Check in fixed_leader for change. (BUGS)
    data = Multiread(fnames=filenames, sonar=sonar, yearbase=yearbase).read()

    ### --- Dealing with the times --- ###

    if fl_flag == 0:
        # convert dday to datatime64[s] and to formated time string.
        time, time_string = dday_to_datetime64(data.dday, yearbase)
    else:
        l.log(f"WARNING: There was {fl_flag} errors in the fixed leader.")
        l.log(f"WARNING: Time coordinate made from -> [1,2,3,4...,len(dday)] in days")
        time, time_string = dday_to_datetime64(np.arange(len(data.dday)), yearbase)

    ### --- Dealing with the depth --- ###

    # convert depth relative to the ADCP to depth below surface
    if data.sonar.model != "os":  # assuming OS sonar output depth below surface.
        if sensor_depth is not None:
            XducerDepth = _xducer_depth_check(data, sensor_depth, logger=l)
            if orientation == "down":
                depth = XducerDepth + data.dep
            else:
                depth = XducerDepth - data.dep
        else:
            l.log(
                (
                    "WARNING: a sensor depth was not provided. Required for `wh` and `sv`"
                    " Thus no correction was done to the depth coordinate"
                )
            )
            depth = data.dep

    ### --- Initating the dataset --- ###
    ds = init_dataset(time, data.dep)

    ### --- Dealing with the coordinates system --- ###
    # Check coordinate system and transform to earth if need.
    if data.trans["coordsystem"] != "earth":
        l.log(f"WARNING: Velocities are in {data.trans['coordsystem']} coordinate")
        l.log("WARNING: Coordinate system transformation was not tested")

        coordsystem2earth(data=data, orientation=orientation)

        l.log("The velocities were transformed to ENU (earth coordinate)")
        l.log("PercentGood was computed from the beam PercentGoods")

        percent_good = np.asarray(np.mean(data.pg.data, axis=2).T)
    else:
        percent_good = np.asarray(data.pg4.T)

    ### --- Loading the date in the dataset --- ###
    ds["u"].values = np.asarray(data.vel.data[:, :, 0].T)
    ds["v"].values = np.asarray(data.vel.data[:, :, 1].T)
    ds["w"].values = np.asarray(data.vel.data[:, :, 2].T)
    ds["e"].values = np.asarray(data.vel.data[:, :, 3].T)

    if data.sonar.model == "sv":
        ds["v_vel"] = np.asarray(data.vb_vel.T)
        ds["v_pg"] = np.asarray(data.vb_pg.T)
        ds["v_corr"] = np.asarray(data.vb_cor.T)
        ds["v_amp"] = np.asarray(data.vb_amp.T)

    # If no bottom track data, drop variables (for loop)
    if not (data.bt_vel.data == 0).all():
        ds["bt_u"].values = np.asarray(data.bt_vel.data[:, 0])
        ds["bt_v"].values = np.asarray(data.bt_vel.data[:, 1])
        ds["bt_w"].values = np.asarray(data.bt_vel.data[:, 2])
        ds["bt_e"].values = np.asarray(data.bt_vel.data[:, 3])
        ds["bt_depth"].values = np.asarray(np.nanmean(data.bt_depth.data, axis=-1))
    else:
        ds = ds.drop_vars(names=["bt_u", "bt_v", "bt_w", "bt_e", "bt_depth"])
        l.log(
            "Bottom track values were all `0` and so they were dropped from the ouput."
        )

    ds["pg"].values = percent_good
    for i in range(1, 5):
        ds[f"corr{i}"].values = np.asarray(data[f"cor{i}"].T)
        ds[f"amp{i}"].values = np.asarray(data[f"amp{i}"].T)

    # for `wh` and `os` xducer_depht varies over times.
    if data.sonar.model != "os":
        ds["xducer_depth"].values = np.asarray(data.XducerDepth)

    else:
        # for `os`, XducerDepth is inputed by the user.
        ds = ds.drop_vars(names=["xducer_depth"])
        XducerDepth = data.XducerDepth[0]

    ds.attrs["_vartmp_XducerDepth"] = XducerDepth

    # Add Navigation data for `os`if available.
    if data.sonar.model == "os":
        if "rawnav" in data:
            ds["lon"].values = np.array(data["rawnav"]["Lon1_BAM4"] * 180.0 / 2 ** 31)
            ds["lat"].values = np.array(data["rawnav"]["Lat1_BAM4"] * 180.0 / 2 ** 31)
        else:
            l.log("Rawnav (GPS data) was found in the binary file")
            ds = ds.drop_vars(names=["lon", "lat"])
    else:
        ds = ds.drop_vars(names=["lon", "lat"])

    # add the pressure if available for `wh` and `sv`.
    if data.sonar.model != "os":
        ds["pres"].values = data.VL["Pressure"]
        if (ds["pres"].values == 0).all():
            l.log(
                "Pressure values were all `0` and so they are dropped from the ouput."
            )
            ds = ds.drop_vars(["pres"])
    else:
        ds = ds.drop_vars(["pres"])

    ds["heading"].values = np.asarray(data.heading)
    ds["roll_"].values = np.asarray(data.roll)
    ds["pitch"].values = np.asarray(data.pitch)
    ds["temp"].values = np.asarray(data.temperature)
    ds["time_string"].values = time_string

    if fl_flag != 0:
        ds["dday"] = (["T"], data.dday)

    ds.sortby("depth")

    ds.attrs["coordsytem"] = data.trans["coordsystem"]
    #             'ping_frequency': '',
    #             'beam_angle': '',
    #             'bin_size': '',
    #             'orientation': '',
    #             'instrument_serial': '',

    l.log("Data loaded with", t=True, w=True)
    ds.attrs["_vartmp_logbook"] = l.logbook

    return ds, data, fl


def init_dataset(time: NDArray, depth: NDArray, sonar: str = None):
    """
    parameters
    ----------
    time:
        vector of datetime64[]

    depth:
        vector of [float/int]
    """

    # Moored P01 only
    data_vars = {
        "u": (["Z", "T"], nans(depth.shape + time.shape)),
        "v": (["Z", "T"], nans(depth.shape + time.shape)),
        "w": (["Z", "T"], nans(depth.shape + time.shape)),
        "e": (["Z", "T"], nans(depth.shape + time.shape)),
        "pg": (["Z", "T"], nans(depth.shape + time.shape)),
        "amp1": (["Z", "T"], nans(depth.shape + time.shape)),
        "amp2": (["Z", "T"], nans(depth.shape + time.shape)),
        "amp3": (["Z", "T"], nans(depth.shape + time.shape)),
        "amp4": (["Z", "T"], nans(depth.shape + time.shape)),
        "corr1": (["Z", "T"], nans(depth.shape + time.shape)),
        "corr2": (["Z", "T"], nans(depth.shape + time.shape)),
        "corr3": (["Z", "T"], nans(depth.shape + time.shape)),
        "corr4": (["Z", "T"], nans(depth.shape + time.shape)),
        "lon": (["T"], nans(time.shape)),
        "lat": (["T"], nans(time.shape)),
        "roll_": (["T"], nans(time.shape)),
        "pitch": (["T"], nans(time.shape)),
        "heading": (["T"], nans(time.shape)),
        # "uship": (["T"], nans(time.shape)),
        # "vship": (["T"], nans(time.shape)),
        "bt_u": (["T"], nans(time.shape)),
        "bt_v": (["T"], nans(time.shape)),
        "bt_w": (["T"], nans(time.shape)),
        "bt_e": (["T"], nans(time.shape)),
        "bt_depth": (["T"], nans(time.shape)),
        "xducer_depth": (["T"], nans(time.shape)),
        "temp": (["T"], nans(time.shape)),
        "pres": (["T"], nans(time.shape)),
        "time_string": (["T"], nans(time.shape)),
    }

    if sonar == "sv":
        data_vars = {
            **data_vars,
            "v_vel": (["Z", "T"], nans((depth.shape + time.shape))),
            "v_amp": (["Z", "T"], nans((depth.shape + time.shape))),
            "v_cor": (["Z", "T"], nans((depth.shape + time.shape))),
            "v_pg": (["Z", "T"], nans((depth.shape + time.shape))),
        }

    dataset = xr.Dataset(
        data_vars=data_vars,
        coords={"depth": (["Z"], depth), "time": (["T"], time)},
    )

    return dataset


def magnetic_to_true(dataset: tp.Type[xr.Dataset]):
    """Covert coordiniates from magnetic to true(geographic).

    The coordinates needs to be in decimal degrees and in a East(x)-North(y)
    frame of reference. The coordinates are rotated from magnetics to true
    using the `magnectic_declination` angle which need to be  measured in
    the geographic frame of reference in decimal degrees.

    [east_true,  = [[np.cos(x), -np.sin(x)]   [magnetic_east,
    north_true]     [np.sin(x), np.cos(x)]] *  magnetic_north]


    Parameters
    ----------
    dataset :
        dataset with variable lon: East coordinates measured by the ADCP.
        dataset with variable lat: North coordinates measured by the ADCP.
        dataset with attrs magnetic_declination.
    """

    def R(angle):
        return [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]

    angle_rad = -np.radians(dataset.attrs["magnetic_declination"])
    dataset.lon.values, dataset.lat.values = np.split(
        np.dot(R(angle_rad), [dataset.lon, dataset.lat]), 2
    )


def dday_to_datetime64(dday, yearbase):
    """Convert time recorded time to pandas time (np.datetime64[s]).

    Replace time coordinates with datetime64 in strftime='%Y-%m-%d %H:%M:%S'
    Add `time_string` variables to dataset (strftime='%Y-%m-%d %H:%M:%S')

    Parameters
    ----------
    dataset:
       FIXME
    """
    start_time = pd.Timestamp(str(yearbase) + "-01-01")
    time = np.array(
        pd.to_datetime(dday, unit="D", origin=start_time, utc=True).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        dtype="datetime64[s]",
    )
    time_string = time.astype(str)

    return time, time_string


def coordsystem2earth(data: tp.Type[Bunch], orientation: str):
    """Transforms beam and xyz coordinates to enu coordinates

    NOTE: not properly tested. Modified from pycurrents_ADCP_processing.

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

    if data.trans.coordsystem not in ["beam", "xyze"]:
        ValueError(
            f"coordsystem value of {data.sysconfig.coordsystem} not recognized. Conversion to enu not available."
        )
    beam_pattern = "convex" if data.sysconfig.convex else "concave"
    xyze, xyze_bt = data.vel.data, data.bt_vel.data

    if data.trans.coordsystem == "beam":
        trans = transform.Transform(angle=data.sysconfig.angle, geometry=beam_pattern)
        xyze = trans.beam_to_xyz(data.vel.data)
        bt_xyze = trans.beam_to_xyz(data.bt_vel.data)

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

    for i in range(4):
        data.vel.data[:, :, i] = np.round(enu[:, :, i], decimals=3)
        data.bt_vel.data[:, i] = np.round(bt_enu[:, i], decimals=3)
        data.trans["coordinate"] = "earth"
        data.trans["tilts"] = True


def _xducer_depth_check(data, sensor_depth, logger):
    """FIXME"""
    if abs(np.nanmedian(data.XducerDepth) - sensor_depth) > 5:
        logger.log(
            (
                "WARNING: The diffenrece between XducerDepth median and the provided sensor depth is greater than 5 m. ",
                "The provided sensor depth will be used for processing instead of XducerDepth",
            )
        )
        logger.log(
            f"\n  Sensor depth = {sensor_depth} m, XducerDepth = {np.nanmedian(data.XducerDepth)} m"
        )

        XducerDepth = sensor_depth

    elif abs(np.nanmean(data.XducerDepth) - sensor_depth) > 5:
        logger.log(
            "WARNING: The diffenrece between XducerDepth mean and the provided sensor depth is greater than 5 m. "
        )
        logger.log(
            f"\n  Sensor depth = {sensor_depth} m, XducerDepth = {np.nanmean(data.XducerDepth)} m"
        )
        XducerDepth = np.nanmean(
            data.XducerDepth[abs(data.XducerDepth - sensor_depth) > 5]
        )
        logger.log(
            f"The XducerDepth mean was computed with the dubious depth discarted"
        )
        logger.log(f"\n  XducerDepth mean = {XducerDepth} m")

    else:
        XducerDepth = np.nanmean(data.XducerDepth)
        logger.log("Depth below surface computed using  the XducerDepth averaged depth")

        return XducerDepth


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
                rawfile(fname=fname, sonar=sonar, yearbase=yearbase).read(
                    varlist=["FixedLeader"]
                )
                for fname in filenames
            ]
        ).raw.FixedLeader
    else:
        fixed_leader = (
            rawfile(fname=filenames, sonar=sonar, yearbase=yearbase)
            .read(varlist=["FixedLeader"])
            .raw.FixedLeader
        )

    return fixed_leader


def nans(shape: tp.Tuple[list, tuple, NDArray]) -> NDArray:
    """return array of nan of shape `shape`"""
    return np.full(shape, np.nan)


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    ios_path = (
        "/home/jeromejguay/ImlSpace/Projects/"
        + "pycurrents_ADCP_processing/"
        + "sample_data/a1_20050503_20050504_0221m.000"
    )

    path = "/media/jeromejguay/5df6ae8c-2af4-4e5b-a1e0-a560a316bde3/home/jeromejguay/WorkSpace_2019/Data/Raw/ADCP/COR1805-ADCP-150kHz009_000001"
    sonar = "os"
    # enr = load_rdi_binary(path + ".ENR", sonar=sonar, yearbase=2018, orientation="down")
    # ens = load_rdi_binary(path + ".ENS", sonar=sonar, yearbase=2018, orientation="down")
    # enx = load_rdi_binary(path + ".ENX", sonar=sonar, yearbase=2018, orientation="down")
    # sta = load_rdi_binary(path + ".STA", sonar=sonar, yearbase=2018, orientation="down")

    ios = load_rdi_binary(
        ios_path, sonar=sonar, yearbase=2020, orientation="down"
    )  # .00

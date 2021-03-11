"""
author: Jérôme Guay
date: Feb. 22, 2021
based-on: https://github.com/jeanlucshaw/adcp2nc/
          and https://github.com/hhourston/pycurrents_ADCP_processign

This script contains functions to read adcp data
and to load them in xarray.Dataset.
CODAS Multiread class is used pycurrents package
is used to read RDI file formats.
(OS, WH, SV)

Accepted files are:
-Teledyne RDI .000.(
TODO .ENX, .ENS .LTA, .STA)
-Rowetch files: (seawatch TODO)

See Also
--------
   * pycurrents.adcp.rdiraw.Multiread

Note
----
  Beam coordinates: Not supported for now.
  SV: Nothing no rotation is carried for beam coordinates.
  NOTE need to add sonar
"""
import xarray as xr
import numpy as np
import pandas as pd
import typing as tp
from nptyping import NDArray
from pycurrents.adcp.rdiraw import Multiread, rawfile, Bunch
import pycurrents.adcp.transform as transform


class Logger:
    def __init__(self, logbook=""):
        self.logbook = "" + logbook

    def __repr__(self):
        return self.logbook

    def section(self, msg, t=False):
        time = "" if t is False else " " + self.timestamp()
        self.logbook += "[" + msg + "]" + time + "\n"
        print(msg)

    def log(self, msg, t=False):
        msg = msg if t is False else self.timestamp() + " " + msg
        self.logbook += "  -" + msg + "\n"
        print(msg)

    @staticmethod
    def timestamp():
        return "(" + pd.Timestamp.now().strftime("%Y-%m-%d %Hh%M:%S") + ")"


def load_rdi_binary(
    filenames: tp.Tuple[str, tp.List[str]],
    sonar: str,
    yearbase: int,
    adcp_orientation: str,  # TODO add options for None computing average orientation from FL,
    sensor_depth: float = None,
    magnetic_declination: float = None,
    #    max_depth:float=0
):
    """FIXME"""
    # =============================#
    # globad attrs for processing  #
    # adcp_orientation             #
    # coordsystem                  #
    # yearbase                     #
    # sonar                        #
    # =============================#

    l = Logger()
    l.section("Reading RDI file", t=True)

    # read binary data. TODO Check in fixed_leader for change. (BUGS)
    data = Multiread(fnames=filenames, sonar=sonar, yearbase=yearbase).read()
    fl = read_fixed_leader(filenames=filenames, sonar=sonar, yearbase=yearbase)

    # convert dday to datatime64[s] and to formated time string.
    time, time_string = _dday_to_datetime64(data.dday, yearbase)
    depth = data.dep

    ## distance from adcp to depth below surface
    # TRIMING FIRST XducerDepth needs to be trim FIRST TODO (if OS: else)
    XducerDepth = data.Xducer

    if data.sonar.model != "os":  # assuming OS sonar output depth.
        if adcp_orientation == "down":
            depth = np.nanmean(data.XducerDepth) + data.dep
        else:
            depth = np.nanmean(data.XducerDepth) - data.dep
        l.log("Depth below surface computed using  XducerDepth.")

    # Init dataset
    ds = init_dataset(time, data.dep)

    # Check coordinate system and transform to earth if need.
    if data.trans["coordsystem"] != "earth":
        l.log(f"WARNING: Velocities are in {data.trans['coordsystem']} coordinate")
        l.log(f"WARNING: Coordinate system transformation was not tested")
        enu = coordsystem2earth(data=data, orientation=adcp_orientation)
        l.log(f"Velocities were rotated from to earth coordinate")

    # If no bottom track data, drop variables (for loop)
    if not (data.bt_vel.data == 0).all():
        ds["bt_u"].values = -data.bt_vel.data[:, 0]
        ds["bt_v"].values = -data.bt_vel.data[:, 1]
        ds["bt_w"].values = -data.bt_vel.data[:, 2]
        ds["bt_e"].values = data.bt_vel.data[:, 3]
        ds["bt_depth"].values = np.nanmean(data.bt_depth.data, axis=-1)
        for i in range(1, 5):
            ds["bt_corr{i}"].values = np.asarray(data["bt_corr{i}"].T)
    else:
        ds = ds.drop_vars(names=["bt_u", "bt_v", "bt_w", "bt_e", "bt_depth"])  # e_bt

    # Add GPS data
    #    if GPS_data:
    if "rawnav" in data:  # if data.sonar.model = "os"
        ds["lon"].values = np.array(data["rawnav"]["Lon1_BAM4"] * 180.0 / 2 ** 31)
        ds["lat"].values = np.array(data["rawnav"]["Lat1_BAM4"] * 180.0 / 2 ** 31)
    else:
        ds = ds.drop_vars(names=["lon", "lat"])

    # Ocean Surveillor don't record pressure.
    if data.sonar.model != "os":
        ds["pres"].values = data.VL["Pressure"]
    else:
        ds = ds.drop_vars(["Pressure"])

    for i in range(1, 5):
        ds["corr{i}"].values = np.asarray(data["corr{i}"].T)
        ds["amp{i}"].values = np.asarray(data["amp{i}"].T)

    ds["intr_dep"].values = np.asarray(data.XducerDepth)
    ds["heading"].values = np.asarray(data.heading)
    ds["roll_"].values = np.asarray(data.roll)
    ds["pitch"].values = np.asarray(data.pitch)
    ds["temp"].values = np.asarray(data.temperature)
    ds["time_string"].values = time_string

    ds.sortby(depth)

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
        "uship": (["T"], nans(time.shape)),
        "vship": (["T"], nans(time.shape)),
        "bt_u": (["T"], nans(time.shape)),
        "bt_v": (["T"], nans(time.shape)),
        "bt_w": (["T"], nans(time.shape)),
        "bt_e": (["T"], nans(time.shape)),
        "bt_pg": (["T"], nans(time.shape)),
        "bt_corr1": (["Z", "T"], nans(time.shape)),
        "bt_corr2": (["Z", "T"], nans(time.shape)),
        "bt_corr3": (["Z", "T"], nans(time.shape)),
        "bt_corr4": (["Z", "T"], nans(time.shape)),
        "bt_depth": (["T"], nans(time.shape)),
        "xducer_dep": (["T"], nans(time.shape)),
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


def _dday_to_datetime64(dday, yearbase):
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


def coordsystem2earth(data: tp.Type[Bunch], orientation: str) -> tp.Dict[str, NDArray]:
    """Transforms beam and xyz coordinates to enu coordinates

    NOTE: not properly tested. Modified from pycurrents_ADCP_processing.

    Returns East, North and Up velocities and the velocity error for 4 beams
    ADCP. UHDAS transform functions are used to transform for beam coordinates
    and xyz to east-north-up (enu). which uses a three-beam solution by faking
    a fourth beam.

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

    fn_raw = (
        "/home/jeromejguay/ImlSpace/Projects/"
        + "pycurrents_ADCP_processing/"
        + "sample_data/a1_20050503_20050504_0221m.000"
    )

    path = "/media/jeromejguay/5df6ae8c-2af4-4e5b-a1e0-a560a316bde3/home/jeromejguay/WorkSpace_2019/Data/Raw/ADCP/COR1805-ADCP-150kHz009_000001"
    file_type = [".ENR", ".ENS", ".ENX", ".LTA", ".STA"]

    sonar = "os"
    data = Multiread(path + ".ENS", sonar=sonar).read()
    data0 = coordsystem2earth(data, orientation="down")
    data1 = Multiread(path + ".ENX", sonar=sonar).read()

    data2 = Multiread(fn_raw, sonar=sonar).read()

sysconf_keys = (
    "FWV",
    "FWR",
    "SysCfg",
    "RealSimFlag",
    "LagLength",
    "NBeams",
    "NCells",
    "NPings",
    "CellSize",
    "Blank",
    "SPM",
    "LowCorrThresh",
    "NCodeReps",
    "PGMin",
    "EVMax",
    "TPP_min",
    "TPP_sec",
    "TPP_hun",
    "EX",
    "EA",
    "EV",
    "EZ",
    "SA",
    "Bin1Dist",
    "Pulse",
    "RL0",
    "RL1",
    "WA",
    "spare3",
    "TransLag",
    "CPU_SN",
    "WB",
    "CQ",
)

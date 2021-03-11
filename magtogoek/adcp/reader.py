"""
author: Jérôme Guay
date: Feb. 22, 2021
based-on: https://github.com/jeanlucshaw/adcp2nc/
          and https://github.com/hhourston/pycurrents_ADCP_processign

This script contains functions to read adcp data
and to load them in xarray.Dataset.
CODAS Multiread class is used pycurrents package
is used to read RDI file formats.

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


class logger:
    def __init__(self):
        self.log = ""

    def __repr__(self):
        print(self.log)

    def log(self, msg):
        self.log += msg + "\n"
        print(msg)


def load_rdi_binary(
    filenames: tp.Tuple[str, tp.List[str]],
    sonar: str,
    yearbase: int,
    adcp_orientation: str,  # TODO add options for None computing average orientation from FL,
    sensor_depth: float = None,
    magnetic_declination: float = None,
    min_depth: float = 0,
):
    """FIXME"""
    # =============================#
    # globad attrs for processing  #
    # adcp_orientation             #
    # coordsystem                  #
    # magnetic_declination         #
    # yearbase                     #
    # sonar                        #
    # =============================#

    l = logger()

    # read binary data. TODO Check in fixed_leader for change. (BUGS)
    data = Multiread(fnames=filenames, sonar=sonar, yearbase=yearbase).read()
    fl = read_fixed_leader(filenames=filenames, sonar=sonar, yearbase=yearbase)

    # convert dday to datatime64[s] and to formated time string.
    time, time_string = convert_time(data.dday, yearbase)
    depth = data.dep

    ### NOTE Je crois que l'ajustement est déja fait. ###
    # if adcp_orientation == "down":
    #    depth = data.dep + np.nanmean(data.XducerDepth)  # depth of the bins
    # else:
    #    depth = np.nanmean(data.XducerDepth) - data.dep  # depth of the bins

    # Init dataset
    ds = init_dataset(time, data.dep)

    # Check coordinate system and transform to earth if need.
    if data.trans["coordsystem"] != "earth":
        l.log(f"WARNING: Velocities are in {data.trans['coordsystem']} coordinate")
        l.log(f"WARNING: Coordinate system transformation was not tested")
        enu = coordsystem2earth(data=data, orientation=adcp_orientation)
        l.log(f"Velocities were rotated from to earth coordinate")

    # If no bottom track data, drop variables
    if not (data.bt_vel.data == 0).all():
        ds["u_bt"].values = -data.bt_vel.data[:, 0]
        ds["v_bt"].values = -data.bt_vel.data[:, 1]
        ds["w_bt"].values = -data.bt_vel.data[:, 2]
        #        ds["e_bt"].values = data.bt_vel.data[:, 3]
        ds["range_bt"].values = np.nanmean(data.bt_depth.data, axis=-1)
    else:
        ds = ds.drop_vars(names=["u_bt", "v_bt", "w_bt", "range_bt"])  # e_bt

    ds["corr"].values = np.asarray(np.mean(data.cor, axis=2).T)
    ds["amp"].values = np.asarray(np.mean(data.amp, axis=2).T)

    # Add GPS data
    #    if GPS_data:
    if sonar == "os":  # try or other if
        ds["lon"].values = np.array(data["rawnav"]["Lon1_BAM4"] * 180.0 / 2 ** 31)
        ds["lat"].values = np.array(data["rawnav"]["Lat1_BAM4"] * 180.0 / 2 ** 31)
    #    else:
    #        ds = ds.drop_vasr(names=["lon","lat"])

    # Remove data shallower than min depth
    if min_depth > 0:
        selected = data.XducerDepth >= min_depth
        ds = ds.sel(time=selected)
    ds["intr_dep"].values = np.asarray(data.XducerDepth)
    ds["heading"].values = np.asarray(data.heading)
    ds["roll_"].values = np.asarray(data.roll)
    ds["pitch"].values = np.asarray(data.pitch)
    ds["temp"].values = np.asarray(data.temperature)
    ds["time_string"].values = time_string

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

    data_vars = {
        "u": (["Z", "T"], nans(depth.shape + time.shape), {"P01": "LCEWAP01"}),
        "v": (["Z", "T"], nans(depth.shape + time.shape), {"P01": "LCNSAP01"}),
        "w": (["Z", "T"], nans(depth.shape + time.shape), {"P01": "LRZAAP01"}),
        "e": (["Z", "T"], nans(depth.shape + time.shape), {"P01": "LERRAP01"}),
        "pg": (["Z", "T"], nans(depth.shape + time.shape), {"P01": "PCGDAP01"}),
        "amp1": (["Z", "T"], nans(depth.shape + time.shape), {"P01": "TNIHCE01"}),
        "amp2": (["Z", "T"], nans(depth.shape + time.shape), {"P01": "TNIHCE02"}),
        "amp3": (["Z", "T"], nans(depth.shape + time.shape), {"P01": "TNIHCE03"}),
        "amp4": (["Z", "T"], nans(depth.shape + time.shape), {"P01": "TNIHCE04"}),
        "corr1": (["Z", "T"], nans(depth.shape + time.shape), {"P01": "CMAGZZ01"}),
        "corr2": (["Z", "T"], nans(depth.shape + time.shape), {"P01": "CMAGZZ02"}),
        "corr3": (["Z", "T"], nans(depth.shape + time.shape), {"P01": "CMAGZZ03"}),
        "corr4": (["Z", "T"], nans(depth.shape + time.shape), {"P01": "CMAGZZ04"}),
        "lon": (["T"], nans(time.shape), {"P01": "ALONZZ01"}),
        "lat": (["T"], nans(time.shape), {"P01": "ALATZZ01"}),
        "roll_": (["T"], nans(time.shape), {"P01": "ROLLGP01"}),
        "pitch": (["T"], nans(time.shape), {"P01": "PTCHGP01"}),
        "heading": (["T"], nans(time.shape), {"P01": "HEADCM01"}),
        "uship": (["T"], nans(time.shape), {"P01": "APEWGP01"}),
        "vship": (["T"], nans(time.shape), {"P01": "APNSGP01"}),
        "u_bt": (["T"], nans(time.shape), {"P01": "APNSBT01"}),  # - bt
        "v_bt": (["T"], nans(time.shape), {"P01": "APEWBT01"}),  # - bt
        "w_bt": (["T"], nans(time.shape), {"P01": "APZABT01"}),  # - bt
        "e_bt": (["T"], nans(time.shape), {"P01": "APERBT01"}),  # - bt
        "range_bt": (["T"], nans(time.shape)),
        "temp": (["T"], nans(time.shape), {"P01": "TEMPPR01"}),
        "sea_height": (["T"], nans(time.shape), {"P01": "DISTRAN"}),
        "time_string": (["T"], nans(time.shape), {"P01": "DTUT8601"}),
    }

    if sonar == "sv":
        data_vars = {
            **data_vars,
            "v_vel": (["Z", "T"], nans((depth.shape, time.shape)), {"P01": "LRZUVP01"}),
            "v_amp": (["Z", "T"], nans((depth.shape, time.shape)), {"P01": "TNIHCE05"}),
            "v_cor": (["Z", "T"], nans((depth.shape, time.shape)), {"P01": "CMAGZZ05"}),
            "v_pg": (["Z", "T"], nans((depth.shape, time.shape)), {"P01": "PCGDAP05"}),
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


def convert_time(dday, yearbase):
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

    beam_pattern = "convex" if data.sysconfig.convex else "concave"

    if data.trans.coordsystem == "beam":
        trans = transform.Transform(angle=data.sysconfig.angle, geometry=beam_pattern)
        xyze = trans.beam_to_xyz(data.vel.data)
        enu = transform.rdi_xyz_enu(
            xyze,
            data.heading,
            data.pitch,
            data.roll,
            orientation=orientation,
        )
        xyze_bt = trans.beam_to_xyz(data.bt_vel.data)
        bt_enu = transform.rdi_xyz_enu(
            xyze,
            data.heading,
            data.pitch,
            data.roll,
            orientation=orientation,
        )
    elif data.trans.coordsystem == "xyz":
        enu = transform.rdi_xyz_enu(
            data.vel.data,
            data.heading,
            data.pitch,
            data.roll,
            orientation=orientation,
        )
        bt_enu = transform.rdi_xyz_enu(
            data.bt_vel.data,
            data.heading,
            data.pitch,
            data.roll,
            orientation=orientation,
        )

    else:
        ValueError(
            f"coordsystem value of {data.sysconfig.coordsystem} not recognized. Conversion to enu not available."
        )

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

    path = "/media/jeromejguay/5df6ae8c-2af4-4e5b-a1e0-a560a316bde3/home/jeromejguay/WorkSpace_2019/Data/Raw/ADCP/COR1805-ADCP-150kHz009"
    file_type = [".ENR", ".ENS", ".ENX", ".LTA", ".STA"]

    ds, data, fl = load_rdi_binary(
        path + file_type[2], "os", 2018, adcp_orientation="down", sensor_depth=0
    )

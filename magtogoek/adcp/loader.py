"""
author: Jérôme Guay
date: Feb. 22, 2021
based in part  on: https://github.com/jeanlucshaw/adcp2nc/
                   https://github.com/hhourston/pycurrents_ADCP_processign


This script contains functions to read adcp files and load them in xarray.Dataset.

RDI data are read using CODAS Multiread reader from the pycurrent pacakge. The Multiread
reader supports .000, .ENX, .ENS, .LTA and .STA binary files.
- sonar: 'wh', 'sv', 'os'.
- Sentinel V encoding is not fully supported by pycurrent.

RTI data re read using Magtogoek rti_reader built from rti_python tools by RoweTech.
- sonar: 'sw'
- Rowtech files can also be exporter directly to Teledyne `PD0` formats and read by pycurrnets
using 'sw_pd0' for sonar.

Notes:
-----
- Orientation is taken from the first profile of the first file if not no value is pass.
- We assume that the `dep` from OS  already is the bin depth below surface.
- pd0 Fixed_Leader are know to have invalid configuration. msb=`11111111` and lsb=`11111111`. The
file will be processed but a warning will be raised. The cause was not investigated.
See Also
--------
   * pycurrents.adcp.rdiraw.Multiread
   * rti_python

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
from magtogoek.adcp.rti_reader import RtiReader
from magtogoek.adcp.utils import dday_to_datetime64
from magtogoek.utils import Logger, get_files_from_expresion, nans
from nptyping import NDArray
from pycurrents.adcp import rdiraw, transform
from pycurrents.adcp.rdiraw import Bunch, Multiread, rawfile

# This is to prevent pycurrents from printing warnings.
logging.getLogger(rdiraw.__name__).setLevel("CRITICAL")

VEL_FILL_VALUE = -32768.0


class FilesFormatError(Exception):
    pass


class InvalidSonarError(Exception):
    pass


def load_adcp_binary(
    filenames: tp.Tuple[str, tp.List[str]],
    sonar: str,
    yearbase: int,
    orientation: str = None,
    sensor_depth: float = None,
    leading_index: int = None,
    trailing_index: int = None,
):
    """Load RDI and RTI adcp data.

    Return a dataset with the ADCP data loaded.

    Notes:
    -----
    Orientation is taken from the first profile of the first file
    if not no value is pass.

    Parameters
    ----------
    filenames:
        Path/to/files
    sonar:
        Type of sonar (`os`, `wh`, `sv`, `sw`, `sw_pd0`)
    yearbase:
        year that the sampling begun.
    orientation:
        Adcp orientation. Either `up` or `down`. Will overwrite the value
        of the binary file.
    sensor_depth:
        Depth of the ADCP. Use to compare with XducerDeppth median
    Returns
    -------
        Dataset with the loaded adcp data

    """
    l = Logger(level=0)
    l.section("Loading adcp data", t=True)

    filenames = get_files_from_expresion(filenames)

    if sonar == "sv":
        l.warning(
            """(from pycurrents)
- The SV support is under development.  Missing features:
- The 0x7000-0x7004 IDs are not being parsed and stored.
- The `Fixed Leader` can change within a file
- See pycurrents.adcp.rdiraw module for for information"""
        )

    # ------------------------ #
    # Reading the data file(s) #
    # ------------------------ #
    if sonar == "sw":
        l.log(
            "RTI ens files:\n-"
            + "\n-".join([p.name for p in list(map(Path, filenames))])
        )
        data = RtiReader(filenames=filenames).read(
            start_index=leading_index, stop_index=trailing_index
        )
    elif sonar in ["wh", "sv", "os", "sw_pd0"]:
        if sonar == "sw_pd0":
            sonar = "wh"
            l.log(
                "RTI pd0 files:\n-"
                + "\n-".join([p.name for p in list(map(Path, filenames))])
            )
        else:
            l.log(
                "RDI pd0 files:\n-"
                + "\n-".join([p.name for p in list(map(Path, filenames))])
            )
        if trailing_index:
            trailing_index = -trailing_index

        try:
            data = Multiread(fnames=filenames, sonar=sonar, yearbase=yearbase).read(
                start=leading_index, stop=trailing_index
            )
        except RuntimeError:
            raise FilesFormatError("Not RDI pd0 file format.")

        # Reading the files FixedLeaders to check for invalid config.
        invalid_config_count = check_PD0_invalid_config(
            filenames=filenames,
            sonar=sonar,
            yearbase=yearbase,
            leading_index=leading_index,
            trailing_index=trailing_index,
        )
        if invalid_config_count:
            l.warning(
                f"Invalide configuration, msb=`11111111` and lsb=`11111111`, found in the SysCfg of {invalid_config_count} FixedLeader."
            )

    else:
        raise InvalidSonarError(
            f"{sonar} is not a valid. Valid sonar: `os`, `wh`, `sv`, `sw`, `sw_pd0` "
        )

    # -------------------- #
    # Compares orientation #
    # -------------------- #
    if not orientation:
        orientation = "up" if data.sysconfig["up"] else "down"
    else:
        if orientation != ("up" if data.sysconfig["up"] else "down"):
            l.warning(
                "The adcp orientation does not match the one found in the binary files."
            )
    # ---------------------------- #
    # Convert `dday` to datetime64 #
    # ---------------------------- #
    bad_dday = False
    if (data.dday < 0).any() or (np.diff(data.dday) < 0).any():
        bad_dday = True
        l.warning(
            [
                f"The `dday` vector contains either negative values or is not monotonically increasing."
                f"Time was replaced by a default datetime vector: len(dday) with a 1 second time step since {yearbase}-1-1 00:00:00"
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
    if sonar != "os":
        XducerDepth = np.median(data.XducerDepth)
        if sensor_depth:
            l.log(
                f"The difference between `sensor_depth` and `XDucerDepth` is {abs(sensor_depth - XducerDepth)} m"
            )
        if orientation == "down":
            depth = XducerDepth + data.dep
        else:
            depth = XducerDepth - data.dep
    else:
        XducerDepth = data.XducerDepth[0]
        depth = data.dep

    if (depth < 0).all():
        l.warning("Bin depths are all negative, ADCP orientation is probably wrong.")

    # --------------------- #
    # Initating the dataset #
    # --------------------- #
    ds = xr.Dataset(coords={"depth": depth, "time": time})

    # --------------------------------------- #
    # Dealing with the coordinates system     #
    # --------------------------------------- #
    original_coordsystem = data.trans["coordsystem"]
    if original_coordsystem != "earth":
        l.log(f"The velocity data are in {data.trans['coordsystem']} coordinate")

        coordsystem2earth(data=data, orientation=orientation)

        if data.trans["coordsystem"] == "xyz":
            l.warning("Roll, Pitch or Heading seems to be missing from the data file.")
        l.log(f"The velocity data were transformed to {data.trans['coordsystem']}")

    # --------------------------- #
    # Loading the transducer data #
    # --------------------------- #

    data.vel[data.vel == VEL_FILL_VALUE] = np.nan  # fill

    ds["u"] = (["depth", "time"], np.asarray(data.vel[:, :, 0].T))
    ds["v"] = (["depth", "time"], np.asarray(data.vel[:, :, 1].T))
    ds["w"] = (["depth", "time"], np.asarray(data.vel[:, :, 2].T))
    ds["e"] = (["depth", "time"], np.asarray(data.vel[:, :, 3].T))

    if sonar == "sv":
        data.vbvel[data.vbvel == VEL_FILL_VALUE] = np.nan
        ds["vb_vel"] = (["depth", "time"], np.asarray(data.vbvel.T))
        ds["vb_corr"] = (["depth", "time"], np.asarray(data.VBCorrelation.T))
        ds["vb_amp"] = (["depth", "time"], np.asarray(data.VBIntensity.T))
        if "VBPercentGood" in data:
            ds["vb_pg"] = (["depth", "time"], np.asarray(data.VBPercentGood.T))
        l.log("Data from the Sentinel V fifth beam loaded.")

    if "bt_vel" in data:
        if not (data.bt_vel == 0).all():
            data.bt_vel[data.bt_vel == VEL_FILL_VALUE] = np.nan
            ds["bt_u"] = (["time"], np.asarray(data.bt_vel[:, 0]))
            ds["bt_v"] = (["time"], np.asarray(data.bt_vel[:, 1]))
            ds["bt_w"] = (["time"], np.asarray(data.bt_vel[:, 2]))
            ds["bt_e"] = (["time"], np.asarray(data.bt_vel[:, 3]))
            l.log("Bottom track data loaded")
        else:
            l.log(
                "Bottom track values were all `0` and so they were dropped from the ouput."
            )

    if "bt_depth" in data:
        if not (data.bt_depth == 0).all():
            ds["bt_depth"] = (
                ["time"],
                np.asarray(np.nanmean(data.bt_depth, axis=-1)),
            )
            l.log("Bottom range data loaded")
        else:
            l.log(
                "Bottom depth values were all `0` and so they were dropped from the ouput."
            )

    if "pg" in data:
        if original_coordsystem == "beam":
            ds["pg"] = (["depth", "time"], np.asarray(np.mean(data.pg, axis=2).T))
            l.log(
                "Percent good was computed by averaging each beam PercentGood. The raw data were in beam coordinate."
            )
        else:
            ds["pg"] = (["depth", "time"], np.asarray(data.pg4.T))
    else:
        l.warning("Percent good was not retrieve from the dataset.")

    if "cor1" in data:
        for i in range(1, 5):
            ds[f"corr{i}"] = (["depth", "time"], np.asarray(data[f"cor{i}"].T))
    if "amp1" in data:
        for i in range(1, 5):
            ds[f"amp{i}"] = (["depth", "time"], np.asarray(data[f"amp{i}"].T))

    # ------------------ #
    # Loading depth data #
    # ------------------ #

    # For `wh`, `sv` and `sw` XducerDepth varies over times but is constant for `os`.
    if sonar != "os":
        ds["xducer_depth"] = (["time"], np.asarray(data.XducerDepth))

    ds.attrs["_vartmp_XducerDepth"] = XducerDepth

    # --------------------------- #
    # Loading the naviagtion data #
    # --------------------------- #
    if "rawnav" in data:
        ds["lon"] = (["time"], np.array(data["rawnav"]["Lon1_BAM4"] * 180.0 / 2 ** 31))
        ds["lat"] = (["time"], np.array(data["rawnav"]["Lat1_BAM4"] * 180.0 / 2 ** 31))
        l.log("Navigation (GPS) data loaded.")

    # -------------------------------------------- #
    # Quick checkup and loading of other variables #
    # -------------------------------------------- #
    # For `wh`, `sv` and `sw` the pressure is added if available.
    if "Pressure" in data.VL.dtype.names:
        if not (data.VL["Pressure"] == 0).all():
            ds["pres"] = (["time"], data.VL["Pressure"] / 1000)  # decapascal to decibar
        else:
            l.log("Pressure data unavailable")

    if "heading" in data:
        if (data.heading == 0).all() or (np.diff(data.heading) == 0).all():
            l.warning("Heading data are either all 0, or not variying.")
        else:
            ds["heading"] = (["time"], np.asarray(data.heading))
    if "roll" in data:
        if (data.roll == 0).all() or (np.diff(data.roll) == 0).all():
            l.warning("Roll data are either all 0, or not variying.")
        else:
            ds["roll_"] = (["time"], np.asarray(data.roll))
    if "pitch" in data:
        if (data.pitch == 0).all() or (np.diff(data.pitch) == 0).all():
            l.warning("Pitch data are either all 0, or not variying.")
        else:
            ds["pitch"] = (["time"], np.asarray(data.pitch))
    if "temperature" in data:
        if (data.temperature == 0).all() or (np.diff(data.temperature) == 0).all():
            l.warning("Temperature data are either all 0, or not variying.")
        else:
            ds["temperature"] = (["time"], np.asarray(data.temperature))

    # ------------------------------- #
    # Load time string or dday if bad #
    # ------------------------------- #
    if bad_dday:
        ds["dday"] = (["time"], np.asarray(data.dday))
    else:
        ds["time_string"] = (["time"], time_string)

    if orientation == "up":
        ds.sortby("depth")

    # -------------- #
    # Add attributes #
    # -------------- #
    sonar_names = dict(
        wh="WorhHorse", sv="SentinelV", os="OceanSurveyor", sw="SeaWATCH"
    )
    ds.attrs["sonar"] = sonar_names[sonar]
    ds.attrs["coordsystem"] = data.trans["coordsystem"]
    ds.attrs["beam_angle"] = data.sysconfig["angle"]
    ds.attrs["transducer_frequency"] = data.sysconfig["kHz"] * 1000
    ds.attrs["bin_size"] = data.CellSize
    ds.attrs["orientation"] = orientation

    l.log(f"File(s) loaded with {l.w_count} warnings")
    ds.attrs["logbook"] = l.logbook

    return ds


def init_dataset(time: NDArray, depth: NDArray):
    """Make a default dataset for adcp.

    Parameters
    ----------
    time:
        vector of datetime64[]

    depth:
        vector of [float/int]
    """

    dataset = xr.Dataset(
        data_vars={},
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

    Also change the values of of `coordinates` in data.trans.

    beam coordinates : Velocity measured along beam axis.
    xyz corrdinates : Velocity in a cartesian coordinate system in the ADCP frame of refence.
    enu coordinates : East North Up measured using the heading, pitch, roll of the ADCP.

    Parameters
    ----------
    data:
        pycurrents.adcp.rdiraw.Bunche object containing: vel[time, depth, beams], bt_vel[time, beams],
        heading, roll, pitch sysconfig.convex, sysconfig.angle  and trans.coordsytem.

    orientation:
        adcp orientation. Either `up` or `down`.

    Errors:
    -------
    ValueError :
        coordinates system no recognized.

    Notes:
    ------
    Move the prints outside
    """

    if data.trans.coordsystem not in ["beam", "xyz"]:
        print(
            f"Coordsystem value of {data.sysconfig.coordsystem} not recognized. Conversion to enu not available."
        )

    beam_pattern = "convex" if data.sysconfig.convex else "concave"

    xyze, xyze_bt = data.vel.data, data.bt_vel.data

    if data.trans.coordsystem == "beam":
        if data.sysconfig.angle:
            trans = transform.Transform(
                angle=data.sysconfig.angle, geometry=beam_pattern
            )
            xyze = trans.beam_to_xyz(data.vel.data)
            bt_xyze = trans.beam_to_xyz(data.bt_vel.data)
        else:
            print("Beam angle missing. Could not convert from beam coordinate.")

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


def check_PD0_invalid_config(
    filenames: tp.Tuple[str, tp.List[str]],
    sonar: str,
    yearbase: int,
    leading_index: int = None,
    trailing_index: int = None,
) -> tp.Tuple[int, None]:
    """Read Teledyne RDI binary FixedLeader and check for invalid config.

    Invalid config -> msb=`11111111` and lsb=`11111111`
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
    bad_cfg_count:
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

    syscfg = fixed_leader["SysCfg"][leading_index:trailing_index]
    invalid_cfg_count = None
    if (syscfg == 2 ** 16 - 1).any():
        invalid_cfg_count = np.sum((syscfg == 2 ** 16 - 1))

    return invalid_cfg_count


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    # ios_path = (
    #      "/home/jeromejguay/ImlSpace/Projects/"
    #       + "pycurrents_ADCP_processing/sample_data/"
    #    )
    # ios_fns = [
    #      "a1_20050503_20050504_0221m.000",
    #       "a1_20160713_20170513_0480m.000",
    #        "eh2_20060530_20060717_0007m.000",
    #  ]
    #   sillex_path = "/media/jeromejguay/5df6ae8c-2af4-4e5b-a1e0-a560a316bde3/home/jeromejguay/WorkSpace_2019/Data/Raw/ADCP/"
    #    sillex_fns = [
    # "COR1805-ADCP-150kHz009_000001",
    # "COR1805-ADCP-150kHz009_000002",
    # ]

    v50exp = (
        "/media/jeromejguay/Bruno/TREX2020/V50/TREX2020_V50_20200911T121242_003_*.ENX"
    )
    # v100file = (
    #    "/media/jeromejguay/Bruno/TREX2020/V100/TREX2020_V100_20200911T115335.pd0"
    #  )

    pd0_sw_path = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/sw_300_4beam_20deg_piston.pd0"
    ens_sw_path = (
        "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/rowetech_seawatch.ens"
    )

    #  files = [sillex_path + fn for fn in sillex_fns]
    # sonar = "os"
    #  enr = load_adcp_binary(
    #       [f + ".ENR" for f in files], sonar=sonar, yearbase=2018, orientation="down"
    #    )
    # ens = load_adcp_binary(
    #      [f + ".ENS" for f in files], sonar=sonar, yearbase=2018, orientation="down"
    #   )
    #    enx = load_adcp_binary(
    # [f + ".ENX" for f in files], sonar=sonar, yearbase=2018, orientation="down"
    # )

    # sonar = "wh"
    # ios0 = load_adcp_binary(
    # ios_path + ios_fns[0], sonar=sonar, yearbase=2005, orientation="down"
    # )
    # ios1 = load_adcp_binary(
    #    ios_path + ios_fns[1], sonar=sonar, yearbase=2016, orientation="down"
    # )
    # ios2 = load_adcp_binary(
    #    ios_path + ios_fns[2], sonar=sonar, yearbase=2006, orientation="down"
    # )

    v50path = Path(v50exp)
    v50files = sorted(map(str, v50path.parent.rglob(v50path.name)))
    sonar = "sv"

    v50 = load_adcp_binary(
        v50files,
        sonar=sonar,
        yearbase=2020,
        orientation="down",
        leading_index=100,
        trailing_index=10000,
    )

    # v100 = load_adcp_binary(v100file, sonar=sonar, yearbase=2020, orientation="down")
    sw_pd0 = load_adcp_binary(
        pd0_sw_path, sonar="sw_pd0", yearbase=2020, orientation="down"
    )
    sw = load_adcp_binary(
        ens_sw_path,
        sonar="sw",
        yearbase=2020,
        orientation="down",
        leading_index=100,
        trailing_index=10,
    )

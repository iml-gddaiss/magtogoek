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

- This schould probably be turned into an object.
See Also
--------
   * pycurrents.adcp.rdiraw.Multiread
   * rti_python

"""
import logging
import typing as tp
from pathlib import Path

import click
import numpy as np
import pandas as pd
import xarray as xr
from magtogoek.adcp.rti_reader import RtiReader
from magtogoek.adcp.tools import dday_to_datetime64
from magtogoek.utils import Logger, get_files_from_expresion
from nptyping import NDArray
from pycurrents.adcp import rdiraw, transform
from pycurrents.adcp.rdiraw import Bunch, Multiread, rawfile

# This is to prevent pycurrents from printing warnings.
logging.getLogger(rdiraw.__name__).setLevel("CRITICAL")

RDI_SONAR = ["wh", "sv", "os", "sw_pd0"]
RTI_SONAR = ["sw"]

VEL_FILL_VALUE = -32768.0

l = Logger(level=0)


class FilesFormatError(Exception):
    pass


class InvalidSonarError(Exception):
    pass


def load_adcp_binary(
    filenames: tp.Tuple[str, tp.List[str]],
    sonar: str,
    yearbase: int,
    orientation: str = None,
    leading_index: int = None,
    trailing_index: int = None,
    sensor_depth: float = None,
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
    leading_index:
        FIXME
    trailing_index:
        FIXME
    sensor_depth:
        If provided, will be used as a static sensor depth.
    Returns
    -------
        Dataset with the loaded adcp data

    """
    l.reset()
    l.section("Loading adcp data", t=True)

    filenames = get_files_from_expresion(filenames)

    if sonar == "sv":
        l.warning(
            """(from pycurrents)
- The SV support is under development.  Missing features:
- The 0x7000-0x7004 IDs are not being parsed and stored.
- See pycurrents.adcp.rdiraw module for for information"""
        )

    # ------------------------ #
    # Reading the data file(s) #
    # ------------------------ #
    if sonar in RTI_SONAR:
        l.log(_fprint_filenames("RTI ENS", filenames))
        data = RtiReader(filenames=filenames).read(
            start_index=leading_index, stop_index=trailing_index
        )
    elif sonar in RDI_SONAR:
        if sonar == "sw_pd0":
            sonar = "wh"
            l.log(_fprint_filenames("RTI pd0", filenames))
        else:
            l.log(_fprint_filenames("RDI pd0", filenames))

        if trailing_index:
            trailing_index = -trailing_index

        try:
            data = Multiread(fnames=filenames, sonar=sonar, yearbase=yearbase).read(
                start=leading_index, stop=trailing_index
            )
            if not data:
                raise ValueError(
                    "The sum of the trim values is greater than the number of ensemble."
                )
        except RuntimeError:
            raise FilesFormatError(f"Not RDI pd0 file format. RDI sonar : {RDI_SONAR}")

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
                "The given adcp orientation does not match the one found in the binary files."
            )
    # ---------------------------- #
    # Convert `dday` to datetime64 #
    # ---------------------------- #
    bad_dday = False
    if (data.dday < 0).any():
        bad_dday = True
        l.warning(
            f"The `dday` vector contains negative values. The time coords was replaced by a default datetime vector: len(dday) with a 1 second time step since {yearbase}-1-1 00:00:00"
        )
    elif (np.diff(data.dday) < 0).any():
        bad_dday = True
        l.warning(
            f"The `dday` vector is not monotonically increasing. The time coords was replaced by a default datetime vector: len(dday) with a 1 second time step since {yearbase}-1-1 00:00:00"
        )
        time, time_string = dday_to_datetime64(
            np.arange(len(data.dday)) / (3600 * 24), yearbase
        )
    else:
        time, time_string = dday_to_datetime64(data.dday, yearbase)

    # ----------------------------------------------------------- #
    # Convert depth relative to the ADCP to depth below surface   #
    # ----------------------------------------------------------- #
    if sonar == "os":
        xducer_depth = data.XducerDepth[0]
        if sensor_depth:
            l.log(
                f"The difference between `sensor_depth` and `XducerDepth` is {abs(sensor_depth - xducer_depth)} m"
            )
            # data.dep was computed from the fixed xducer_depth and so needs to be corrected.
            depth = data.dep + (sensor_depth - xducer_depth)
            xducer_depth = sensor_depth
        else:
            depth = data.dep
    else:
        xducer_depth = np.median(data.XducerDepth)
        if sensor_depth:
            l.log(
                [
                    "The difference between the provided `sensor_depth` and `XducerDepth`",
                    f"is {round(abs(sensor_depth - xducer_depth),3)} m.",
                ]
            )
            xducer_depth = sensor_depth

        if orientation == "down":
            depth = xducer_depth + data.dep
        else:
            depth = xducer_depth - data.dep

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

    data.vel[data.vel.data == VEL_FILL_VALUE] = np.nan  # fill

    ds["u"] = (["depth", "time"], np.asarray(data.vel[:, :, 0].T))
    ds["v"] = (["depth", "time"], np.asarray(data.vel[:, :, 1].T))
    ds["w"] = (["depth", "time"], np.asarray(data.vel[:, :, 2].T))
    ds["e"] = (["depth", "time"], np.asarray(data.vel[:, :, 3].T))

    if sonar == "sv":
        data.vbvel[data.vbvel.data == VEL_FILL_VALUE] = np.nan
        ds["vb_vel"] = (["depth", "time"], np.asarray(data.vbvel.T))
        ds["vb_corr"] = (["depth", "time"], np.asarray(data.VBCorrelation.T))
        ds["vb_amp"] = (["depth", "time"], np.asarray(data.VBIntensity.T))
        if "VBPercentGood" in data:
            ds["vb_pg"] = (["depth", "time"], np.asarray(data.VBPercentGood.T))
        l.log("Data from the Sentinel V fifth beam loaded.")

    if "bt_vel" in data:
        if not (data.bt_vel == 0).all():
            data.bt_vel[data.bt_vel.data == VEL_FILL_VALUE] = np.nan
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
        if (data.bt_depth == 0).all():
            l.log(
                "Bottom depth values were all `0` and so they were dropped from the ouput."
            )
        elif not np.isfinite(data.bt_depth).all():
            l.log(
                "Bottom depth values were all `nan` and so they were dropped from the ouput."
            )
        else:
            if sonar == "os" or orientation == "up":
                bt_depth = data.bt_depth
            else:
                bt_depth = data.bt_depth + xducer_depth

            ds["bt_depth"] = (
                ["time"],
                np.asarray(np.nanmean(bt_depth, axis=-1)),
            )
            l.log("Bottom depth  data loaded")

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
        wh="WorkHorse", sv="Sentinel V", os="Ocean Surveyor", sw="SeaWATCH"
    )
    ds.attrs["sonar"] = sonar_names[sonar]
    ds.attrs["manufacturer"] = (
        "Teledyne RD Instruments Inc."
        if sonar in ["wh", "sv", "os"]
        else "Rowe Technologie Inc. (RTI)"
    )
    if "xducer_depth" not in ds:
        ds.attrs["xducer_depth"] = xducer_depth
    ds.attrs["coord_system"] = data.trans["coordsystem"]
    ds.attrs["beam_angle"] = data.sysconfig["angle"]
    ds.attrs["frequency"] = data.sysconfig["kHz"] * 1000
    ds.attrs["bin_size"] = data.CellSize
    ds.attrs["ping_per_ensemble"] = data.NPings
    ds.attrs["ping_type"] = data.pingtype

    ds.attrs["firmware_version"] = ".".join(
        list(str(data.FL["FWV"])) + list(str(data.FL["FWR"]))
    )
    ds.attrs["xmit_lag"] = data.FL["Pulse"] / 100  # centimeters to meters

    ds.attrs["delta_t_sec"] = np.round(
        np.mean((np.diff(ds.time).astype("timedelta64[s]"))).astype(float), 2
    )
    ds.attrs["sampling_interval"] = str(ds.attrs["delta_t_sec"]) + " seconds"

    ds.attrs["beam_pattern"] = "convex" if data.sysconfig["convex"] else "concave"

    ds.attrs["janus"] = "5-Beam" if sonar == "sv" else "4-Beam"

    ds.attrs["magnetic_declination"] = None
    if "FL" in data:
        if "EV" in data.FL:
            if data.FL["EV"] == 0:
                ds.attrs["magnetic_declination"] = None
            else:
                ds.attrs["magnetic_declination"] = data.FL["EV"] / 100

    ds.attrs["orientation"] = orientation
    if "SerialNumber" in data:
        ds.attrs["serial_number"] = data.SerialNumber

    l.log(f"File(s) loaded with {l.w_count} warnings")
    ds.attrs["logbook"] = l.logbook

    return ds


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

    beam_pattern = "convex" if data.sysconfig["convex"] else "concave"

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


def _fprint_filenames(file_type: str, filenames: tp.List) -> str:
    """Format a string of filenames for prints
    `file_type` files :
      |-filename1
           :
      |-filenameN
    """
    return (
        file_type
        + " files :\n"
        + "  |-".join([p.name for p in list(map(Path, filenames))])
        + "\n"
    )

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
import sys
import typing as tp
from pathlib import Path

# import click
import numpy as np
# import pandas as pd
import xarray as xr
from magtogoek.adcp.rti_reader import RtiReader
from magtogoek.adcp.rti_reader import l as rti_log
from magtogoek.adcp.tools import dday_to_datetime64
from magtogoek.utils import Logger, get_files_from_expresion
# from nptyping import NDArray
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
    depth_range: tp.Tuple[int, float, list] = None,
    sensor_depth: float = None,
    fixed_sensor_depth: float = None,
):
    """Load RDI and RTI adcp data.

    Return a dataset with the ADCP data loaded. For RDI FIXME pycurcurents...

    Notes:
    -----
    The adcp prientation is taken from the first profile of the first file
    if no orientation is given.

    Parameters
    ----------
    filenames :
        Path/to/files
    sonar :
        Type of sonar (`os`, `wh`, `sv`, `sw`, `sw_pd0`)
    yearbase :
        year that the sampling begun.
    orientation :
        Adcp orientation. Either `up` or `down`. Will overwrite the value
        of the binary file.
    leading_index :
        Number of ensemble to cut from the start.
    trailing_index :
        Number of ensemble to cut from the end.
    depth_range :
        Depth min or (min max)
    sensor_depth:
        If provided, the adcp depth will be adjusted so that its median equal `sensor_depth`.
    fixed_sensor_depth:
        If provided, the adcp depth will be adjusted so that its median equal `sensor_depth`.
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
        l.logbook += rti_log.logbook
    elif sonar in RDI_SONAR:
        if sonar == "sw_pd0":
            sonar = "wh"
            l.log(_fprint_filenames("RTI pd0", filenames))
        else:
            l.log(_fprint_filenames("RDI pd0", filenames))

        if trailing_index:
            trailing_index *= -1

        try:
            data = Multiread(fnames=filenames, sonar=sonar, yearbase=yearbase).read(
                start=leading_index, stop=trailing_index
            )
            if not data:
                raise ValueError(
                    "The sum of the trim values is greater than the number of ensemble."
                )
            data.vel = np.asarray(data.vel)
            if "vbvel" in data:
                data.vbvel = np.asarray(data.vbvel)
            if "bt_vel" in data:
                data.bt_vel = np.asarray(data.bt_vel)
        except RuntimeError:
            print(
                f"ERROR: The input_files are not in a RDI pd0 format. RDI sonar : {RDI_SONAR}"
            )
            sys.exit()

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
    sysconfig_orientation = "up" if data.sysconfig["up"] else "down"
    if not orientation:
        orientation = sysconfig_orientation
    else:
        if orientation != sysconfig_orientation:
            l.warning(
                f"The user input adcp orientation is {orientation} but the one found in the file was {sysconfig_orientation}."
            )

    l.log(f"Adcp orientation is set to {orientation}.")

    # ---------------------------- #
    # Convert `dday` to datetime64 #
    # ---------------------------- #
    bad_dday = False
    if (data.dday < 0).any():
        bad_dday = True
        l.warning(
            f"""The `dday` vector contains negative values. The provided yearbase might be wrong.
            The time coords was replaced by a default datetime vector: {len(data.dday)} with a 1 x
            second time step since {yearbase}-1-1 00:00:00."""
        )
        time, time_string = dday_to_datetime64(
            np.arange(len(data.dday)) / (3600 * 24), yearbase
        )
    elif (np.diff(data.dday) < 0).any():
        bad_dday = True
        l.warning(
            f"""The `dday` vector is not monotonically increasing.
            The time coords was replaced by a default datetime vector: len(dday) with a 1 second time
            step since {yearbase}-1-1 00:00:00."""
        )
        time, time_string = dday_to_datetime64(
            np.arange(len(data.dday)) / (3600 * 24), yearbase
        )
    else:
        time, time_string = dday_to_datetime64(data.dday, yearbase)

    # ----------------------------------------------------------- #
    # Convert depth relative to the ADCP to depth below surface   #
    # ----------------------------------------------------------- #
    if fixed_sensor_depth:  # FIXME
        sensor_depth = None
        data.XducerDepth[:] = fixed_sensor_depth

    average_xducer_depth = round(np.median(data.XducerDepth), 3)
    xducer_depth = data.XducerDepth

    if sensor_depth:
        depth_difference = round(average_xducer_depth - sensor_depth, 3)
        if abs(depth_difference) > 0:
            l.log(
                [
                    f"The difference between the instrument averaged `XducerDepth` ({average_xducer_depth} m) and the given `sensor_depth` ({sensor_depth} m) is {depth_difference} m",
                ]
            )

            l.log(
                f"{-depth_difference} m was added to the depths mesured by the instrument."
            )

        average_xducer_depth = sensor_depth
        xducer_depth -= depth_difference

    if sonar == "os":
        if sensor_depth:
            # For Ocean surveyor, data.dep correspond to depth below surface.
            # These values was computed with the instrument XducerDepth value.
            # Thus it needs to be corrected if a different sensro_depth was given.
            # Ocean Surveyor are considere to be always down looking.
            depth = data.dep - depth_difference
        else:
            depth = data.dep
    else:
        if orientation == "down":
            depth = average_xducer_depth + data.dep
        else:
            depth = average_xducer_depth - data.dep

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
    data.vel[data.vel == VEL_FILL_VALUE] = np.nan
    # WATER VELOCITIES
    ds["u"] = (["depth", "time"], data.vel[:, :, 0].T)
    ds["v"] = (["depth", "time"], data.vel[:, :, 1].T)
    ds["w"] = (["depth", "time"], data.vel[:, :, 2].T)
    ds["e"] = (["depth", "time"], data.vel[:, :, 3].T)
    l.log("Velocity data loaded")

    if sonar == "sv":
        data.vbvel[data.vbvel == VEL_FILL_VALUE] = np.nan
        ds["vb_vel"] = (["depth", "time"], data.vbvel.T)
        ds["vb_corr"] = (["depth", "time"], np.asarray(data.VBCorrelation.T))
        ds["vb_amp"] = (["depth", "time"], np.asarray(data.VBIntensity.T))
        if "VBPercentGood" in data:
            ds["vb_pg"] = (["depth", "time"], np.asarray(data.VBPercentGood.T))
        l.log("Data from the Sentinel V fifth beam loaded.")

    # BOTTOM VELOCITIES
    if "bt_vel" in data:
        if (data.bt_vel == 0).all():
            l.log(
                "Bottom track values were all `0`, therefore they were dropped from the ouput."
            )
        elif not np.isfinite(data.bt_vel).all():
            l.log(
                "Bottom track values were all `nan`, therefore they were dropped from the ouput."
            )

        else:
            l.log(
                "Bottom track values were all `0`, therefore they were dropped from the ouput."
            )
            data.bt_vel[data.bt_vel == VEL_FILL_VALUE] = np.nan
            ds["bt_u"] = (["time"], data.bt_vel[:, 0])
            ds["bt_v"] = (["time"], data.bt_vel[:, 1])
            ds["bt_w"] = (["time"], data.bt_vel[:, 2])
            ds["bt_e"] = (["time"], data.bt_vel[:, 3])
            l.log("Bottom track data loaded")

    # BOTTOM DEPTH
    if "bt_depth" in data:
        if (data.bt_depth == 0).all():
            l.log(
                "Bottom depth values were all `0`, therefore they were dropped from the ouput."
            )
        elif not np.isfinite(data.bt_depth).all():
            l.log(
                "Bottom depth values were all `nan`, therefore they were dropped from the ouput."
            )
        else:
            ds["bt_depth"] = (["time"], np.asarray(np.nanmean(data.bt_depth, axis=-1)))
            if orientation == "up":
                l.log(
                    "In a `up` orientation, bottom_depth corresponds to the water height above adcp, thus should correspond to the xducer_depth mesurements and bottom velocities correspond to the water surface velocity."
                )
                l.log(
                    f"The averaged xducer_depth computed from the bottom tracking is {np.median(data.bt_depth)}."
                )
            elif sensor_depth:
                if abs(depth_difference) > 0 and sonar == "os":
                    ds["bt_depth"] -= depth_difference
            else:
                ds["bt_depth"] += xducer_depth

            l.log("Bottom depth  data loaded")

    # QUALITY
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
        ds["xducer_depth"] = (["time"], np.asarray(xducer_depth))

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
        ds = ds.sortby("depth")

    # -------------- #
    #  Cutting bins  #
    # -------------- #
    if depth_range:
        if not isinstance(depth_range, (list, tuple)):
            depth_range = [depth_range]
        if len(depth_range) == 1:
            if depth_range[0] > ds.depth.max():
                l.log(
                    "depth_range value is greater than the maximum bin depth. Depth slicing aborded."
                )
            else:
                ds = ds.sel(depth=slice(depth_range[0], None))
                l.log(f"Bin of depth inferior to {depth_range[0]} m were cut.")
        elif len(depth_range) == 2:
            if depth_range[0] > ds.depth.max() or depth_range[1] < ds.depth.min():
                l.log(
                    "depth_range values are outside the actual depth range. Depth slicing aborded."
                )
            else:
                ds = ds.sel(depth=slice(*depth_range))
                l.log(
                    f"Bin of depth inferior to {depth_range[0]} m and superior to {depth_range[1]} m were cut."
                )
        else:
            l.log(
                f"depth_range expects a maximum of 2 values but {len(depth_range)} were givien. Depth slicing aborded."
            )

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
        ds.attrs["xducer_depth"] = round(average_xducer_depth, 2)
    ds.attrs["coord_system"] = data.trans["coordsystem"]
    ds.attrs["beam_angle"] = data.sysconfig["angle"]
    ds.attrs["frequency"] = data.sysconfig["kHz"] * 1000  # kHz to hz
    ds.attrs["bin_size"] = data.CellSize
    ds.attrs["ping_per_ensemble"] = data.NPings
    ds.attrs["ping_type"] = data.pingtype
    ds.attrs["blank"] = data.Blank / 100  # cm to m
    ds.attrs["bin1dist"] = data.Bin1Dist

    ds.attrs["firmware_version"] = ".".join(
        list(str(data.FL["FWV"])) + list(str(data.FL["FWR"]))
    )
    ds.attrs["transmit_pulse_lenght_m"] = data.FL["Pulse"] / 100  # cm to m

    ds.attrs["delta_t_sec"] = np.round(
        np.mean((np.diff(ds.time).astype("timedelta64[s]"))).astype(float), 2
    )
    ds.attrs["sampling_interval"] = str(ds.attrs["delta_t_sec"]) + " seconds"

    ds.attrs["beam_pattern"] = "convex" if data.sysconfig["convex"] else "concave"

    ds.attrs["janus"] = "5-Beam" if sonar == "sv" else "4-Beam"

    ds.attrs["magnetic_declination"] = None
    if "FL" in data:
        if "EV" in data.FL:
            if data.FL["EV"] != 0:
                ds.attrs["magnetic_declination"] = data.FL["EV"] / 100

    ds.attrs["serial_number"] = None
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
        l.log(
            f"Coordsystem value of {data.sysconfig.coordsystem} not recognized. Conversion to enu not available."
        )

    beam_pattern = "convex" if data.sysconfig["convex"] else "concave"

    xyze, xyze_bt = data.vel.data, data.bt_vel.data

    if data.trans.coordsystem == "beam":
        if data.sysconfig.angle:
            trans = transform.Transform(
                angle=data.sysconfig.angle, geometry=beam_pattern
            )
            xyze = trans.beam_to_xyz(data.vel)
            bt_xyze = trans.beam_to_xyz(data.bt_vel)
        else:
            l.log("Beam angle missing. Could not convert from beam coordinate.")

    if (data.heading == 0).all() or (data.roll == 0).all() or (data.pitch == 0).all():
        data.trans["coordsystem"] = "xyz"

        for i in range(4):
            data.vel[:, :, i] = np.round(xyze[:, :, i], decimals=3)
            data.bt_vel[:, i] = np.round(bt_xyze[:, i], decimals=3)
    else:
        enu = transform.rdi_xyz_enu(
            xyze, data.heading, data.pitch, data.roll, orientation=orientation,
        )
        bt_enu = transform.rdi_xyz_enu(
            bt_xyze, data.heading, data.pitch, data.roll, orientation=orientation,
        )
        data.trans["coordsystem"] = "earth"

        for i in range(4):
            data.vel[:, :, i] = np.round(enu[:, :, i], decimals=3)
            data.bt_vel[:, i] = np.round(bt_enu[:, i], decimals=3)


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
        + " files : \n  |-"
        + "\n  |-".join([p.name for p in list(map(Path, filenames))])
    )

"""
author: jerome.guay@protonmail.com

Module to load GPS data and compute navigation data from `nmea`, `gpx` or `netcdf` file format


Notes
-----
compute_navigation:
    After testing, the u_ship, v_ship computation need more work, using a large value for the rolling
    average window could do the trick.
"""

import typing as tp
import warnings
from pathlib import Path

import gpxpy
import numpy as np
import pynmea2
import xarray as xr
import matplotlib.pyplot as plt
from magtogoek.tools import get_gps_bearing, vincenty
from magtogoek.utils import get_files_from_expression

FILE_FORMATS = [".log", ".gpx", ".nc"]
GPS_VARIABLES_NAME = ["lon", "lat", "time"]
VARIABLE_TRANSLATOR = dict(
    time=["Time", "TIME", "T", "t"],
    lon=["LON", "Lon", "longitude", "LONGITUDE", "Longitude", "X", "x"],
    lat=["LAT", "Lat", "latitude", "LATITUDE", "Latitude", "Y", "y"],
)


def load_navigation(filenames):
    """Load gps data from  `nmea`, `gpx` or `netcdf` file format.
    Returns a xarray.Dataset with the loaded data.
    """

    filenames = get_files_from_expression(filenames)

    datasets = []

    for filename in filenames:
        ext = Path(filename).suffix
        if ext not in FILE_FORMATS:
            with open(filename) as unkown_format:
                first_char = unkown_format.read(1)
                # some XML first char are order mark, \ufeef, for big- and little-endian.
                if first_char == "\ufeff":
                    first_char = unkown_format.read(1)
                if first_char == "<":
                    ext = ".gpx"
                if first_char == "$":
                    ext = ".log"

        if ext == ".nc":
            dataset = xr.open_dataset(filename)
            dataset = _check_variables_names(dataset)
        elif ext == ".gpx":
            dataset = _load_gps(filename, file_type="gpx")
        elif ext == ".log":
            dataset = _load_gps(filename, file_type="nmea")
        else:
            dataset = None

        if dataset:
            datasets.append(dataset)

    if len(datasets) > 0:
        return xr.merge(datasets)
    else:
        return None


def _load_gps(filename: str, file_type: str) -> xr.Dataset:
    """Load navigation data `lon`, `lat` and `time` from a gpx or nmea file format."""
    reader = {"gpx": _read_gpx, "nmea":_read_nmea}[file_type]
    gps_data = reader(filename)

    dataset = xr.Dataset(
        {"lon": (["time"], gps_data["lon"]), "lat": (["time"], gps_data["lat"])},
        coords={"time": gps_data["time"]},
        attrs={"filename": str(Path(filename).resolve())},
    )
    return dataset.sortby("time")


def _read_gpx(filename: str) -> tp.Dict:
    """Load navigation data `lon`, `lat` and `time` from a gpx file.
    Returns a dictionary with the loaded data."""
    gps_data = dict(time=[], lon=[], lat=[])
    with open(filename, "r") as f:
        gps = gpxpy.parse(f)
        for track in gps.tracks:
            for segment in track.segments:
                for point in segment.points:
                    gps_data["time"].append(
                        np.datetime64(point.time.replace(tzinfo=None))
                    )
                    gps_data["lon"].append(point.longitude)
                    gps_data["lat"].append(point.latitude)

    return gps_data


def _read_nmea(filename: str) -> tp.Dict:
    """Load navigation data `lon`, `lat` and `time` from a NMEA file.
    Returns a dictionary with the loaded data.
    """
    gps_data = dict(time=[], lon=[], lat=[])
    with open(filename, "r") as f:
        for line in f.readlines():
            m = pynmea2.parse(line)
            if m.sentence_type == "GGA":
                gps_data["lon"].append(m.longitude)
                gps_data["lat"].append(m.latitude)
            if m.sentence_type == "ZDA":
                gps_data["time"].append(np.datetime64(m.datetime.replace(tzinfo=None)))
    return gps_data


def compute_navigation(
    filenames: str, output_name: str = None, window: int = 1,
):
    """Compute the `bearing`, `speed`, `u_ship` and `v_ship` from gps data in nmea text format or gpx xml format.

    Returns an xarray.dataset object with the compute data and gps data.

    Parameters
    ----------
    output_name
    filenames
    window :
        Size of the centered averaging window for u_ship, v_ship and bearing computation.

    Notes
    -----
    WARNINGS:
        After testing, the u_ship, v_ship computation need more works.

    """

    filenames = get_files_from_expression(filenames)

    dataset = load_navigation(filenames)
    dataset = _compute_navigation(dataset, window=window)

    dataset.attrs["input_files"] = filenames

    if not output_name:
        output_name = filenames[0]
        if Path(output_name).suffix == ".nc":
            p = Path(output_name)
            output_name = str(p.with_name(p.stem + "_nav.nc"))

    _plot_navigation(dataset)

    dataset.to_netcdf(Path(output_name).with_suffix(".nc"))

    return dataset


def _compute_navigation(
    dataset: xr.Dataset, window: int = 1
) -> xr.Dataset:
    """compute bearing, speed, u_ship and v_ship

    Computes the distance between each GPS coordinates with Vincenty and
    WGS84 and speed = distance / time_delta.

    Parameters
    ----------
    window :
        Size of the centered averaging window.
    """

    if not isinstance(window, int):
        window = int(window)

    position0 = np.array((dataset.lon.values[:-1], dataset.lat.values[:-1])).T.tolist()
    position1 = np.array((dataset.lon.values[1:], dataset.lat.values[1:])).T.tolist()

    distances = list(map(vincenty, position0, position1))  # meter

    bearing = list(map(get_gps_bearing, position0, position1))  # degree

    time_delta = np.diff(dataset.time).astype("timedelta64[s]")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)

        speed = distances / time_delta.astype("float64")  # meter per seconds

    time_centered = dataset.time[:-1] + time_delta / 2

    u_ship = speed * np.sin(np.deg2rad(bearing))
    v_ship = speed * np.cos(np.deg2rad(bearing))

    nav_dataset = xr.Dataset(
        {
            "bearing": (["time"], bearing),
            "speed": (["time"], speed),
            "u_ship": (["time"], u_ship),
            "v_ship": (["time"], v_ship),
        },
        coords={"time": time_centered},
    )

    nav_dataset = (
        nav_dataset.rolling(time=window, center=True).mean().interp(time=dataset.time)
    )

    dataset = xr.merge((nav_dataset, dataset), compat='override')

    return dataset


def _plot_navigation(dataset: xr.Dataset):
    """plots bearing, speed, u_ship and v_ship from a dataset"""

    fig = plt.figure(figsize=(12, 8))
    ax_bearing = plt.subplot(411)
    ax_bearing.set_ylabel("bearing [degree]")
    ax_speed = plt.subplot(412, sharex=ax_bearing)
    ax_speed.set_ylabel("speed [m/s]")
    ax_uship = plt.subplot(413, sharex=ax_bearing)
    ax_uship.set_ylabel("uship [m/s]")
    ax_vship = plt.subplot(414, sharex=ax_bearing)
    ax_vship.set_ylabel("vship [m/s]")

    dataset.bearing.plot(ax=ax_bearing)
    dataset.speed.plot(ax=ax_speed)
    dataset.u_ship.plot(ax=ax_uship)
    dataset.v_ship.plot(ax=ax_vship)

    ax_bearing.get_xaxis().set_visible(False)
    ax_speed.get_xaxis().set_visible(False)
    ax_uship.get_xaxis().set_visible(False)

    plt.subplots_adjust(hspace=0.05)

    plt.show()


def _check_variables_names(dataset):
    """Return None if a variable cannot be found in the dataset"""
    for var in GPS_VARIABLES_NAME:
        if var not in dataset:
            for varname in VARIABLE_TRANSLATOR[var]:
                if varname in dataset:
                    dataset = dataset.rename({varname: var})
                    break
        if var not in dataset:
            print(f"{var} missing from netcdf gps data")
            dataset = None
            break

    return dataset


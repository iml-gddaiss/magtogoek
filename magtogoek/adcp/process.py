"""
Script to process adcp data.

- Load
- Quality_Control
- MetaData
- Export -> .nc or .odf
"""
import typing as tp
import warnings

import numpy as np
import pandas as pd
import xarray as xr
from magtogoek.utils import Logger, get_gps_bearing, vincenty

l = Logger(level=0)

from pathlib import Path


def load_navigation(filename: str, window: int = 60) -> tp.Type[xr.Dataset]:
    """Load navigation data from netcdf file.

    The netcd files must contains `lon` and `lat`
    (longitude and latitude in decimal degrees) along a `time`
    coordinates.

    This functions computes the `bearing`, `u_ship` and `v_ship` from
    `lon` and `lat`.

    Computes the distance between each GPS coordinates with Vincenty and
    WGS84 and speed = distance / time_delta. The navigation data computed
    are averaged over `window` number of assemble and interpolated of the
    original time vector.

    Parameters
    ----------
    filename :
        GPS netcdf filename.
    window :
        Size of the centered averaging window.
    Returns
    -------
        dataset with the loaded navigation data.
    Notes
    -----
        Not properly tested.

    """
    if Path(filename).is_file():
        try:
            dataset = xr.open_dataset(filename).dropna("time")
        except OSError(f"{filename} is not a netcdf file."):
            l.warning("GPS file was not in netcdf format.")

        if "lon" in dataset.variables and "lat" in dataset.variables:

            dataset = xr.merge((dataset, compute_nav(dataset, window=window)))

            return dataset

        else:
            l.warning(
                "GPS data, `lon` and/or `lat`, were not found in the gsp netcdf file provided."
            )
    else:
        l.warning("No GPS files found.")


def compute_nav(dataset: tp.Type[xr.Dataset], window: int = 60) -> tp.Type[xr.Dataset]:
    """compute bearing, speed, u_ship and v_ship

    Computes the distance between each GPS coordinates with Vincenty and
    WGS84 and speed = distance / time_delta.

    Parameters
    ----------
    window :
        Size of the centered averaging window.
    """

    position0 = np.array((dataset.lon.values[:-1], dataset.lat.values[:-1])).T.tolist()
    position1 = np.array((dataset.lon.values[1:], dataset.lat.values[1:])).T.tolist()

    distances = list(map(vincenty, position0, position1))  # meter

    bearing = list(map(get_gps_bearing, position0, position1))  # degree

    time_delta = np.diff(dataset.time).astype("timedelta64[s]")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)

    speed = distances / time_delta.astype("float64")  # meter per seconds

    time_centered = dataset.time[:-1] + time_delta / 2

    u_ship = speed * np.sin(np.radians(bearing))
    v_ship = speed * np.cos(np.radians(bearing))

    ds = xr.Dataset(
        {
            "bearing": (["time"], bearing),
            "speed": (["time"], speed),
            "u_ship": (["time"], u_ship),
            "v_ship": (["time"], v_ship),
        },
        coords={"time": time_centered},
    )

    ds = ds.rolling(time=window, center=True).mean().interp(time=dataset.time)

    return ds


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    test_files = "../../test/files/gps_sillex2018.nc"

    ds = xr.open_dataset(test_files)

    ds_vel = load_navigation(test_files, window=1)

    vel = ds.bt_u[abs(ds.bt_u) < 50]

    plt.figure("vel mag")
    plt.plot(ds_vel.time, ds_vel.u_ship, label="ship")
    plt.plot(vel.time, -vel, label="bottom")

    plt.legend()

    plt.show()

"""
Module to make navigation files from `longitude` and `lattitude` data.
"""

import typing as tp
import warnings
from pathlib import Path

import numpy as np
import xarray as xr

from magtogoek.tools import get_gps_bearing, vincenty
from magtogoek.utils import Logger

l = Logger(level=0)


def make_navigation(
    filename: str, output: str, window: int = 60, plot: bool = True
) -> tp.Type[xr.Dataset]:
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
    output:
        name for the ouput ncdf4 file.
    window :
        Size of the centered averaging window.
    plot:
       If `True``, will plot the computed navigation data.
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

            dataset = xr.merge((dataset, compute_navigation(dataset, window=window)))

            if output is not None:
                dataset.to_netcdf(Path(output).with_suffix(".nc"))

            if plot:
                plot_navigation(dataset)

            return dataset

        else:
            l.warning(
                "GPS data, `lon` and/or `lat`, were not found in the gsp netcdf file provided."
            )
    else:
        l.warning("No GPS files found.")


def compute_navigation(
    dataset: tp.Type[xr.Dataset], window: int = 60
) -> tp.Type[xr.Dataset]:
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


def plot_navigation(dataset: tp.Type[xr.Dataset]):
    """FIXME"""

    fig = plt.figure(12, 8)
    ax_bearing = fig.subplot(411)
    ax_bearing.set_ylabel("bearing [degree]")
    ax_speed = fig.subplot(412, sharex=ax_bearing)
    ax_speed.set_ylabel("speed [m/s]")
    ax_uship = fig.subplot(413, sharex=ax_bearing)
    ax_uship.set_ylabel("uship [m/s]")
    ax_vship = fig.subplot(414, sharex=ax_bearing)
    ax_vship.set_ylabel("vship [m/s]")

    dataset.bearing.plot(axe=ax_bearing)
    dataset.speed.plot(axe=ax_speed)
    dataset.uship.plot(axe=ax_uship)
    dataset.vship.plot(axe=ax_vship)

    plt.setp(ax_speed.get_xticklabels(), visible=False)
    plt.setp(ax_uship.get_xticklabels(), visible=False)
    plt.setp(ax_vship.get_xticklabels(), visible=False)

    plt.show()


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    test_files = "../../test/files/gps_sillex2018.nc"

    ds = xr.open_dataset(test_files)

    ds_vel = make_navigation(test_files, window=1)

    vel = ds.bt_u[abs(ds.bt_u) < 50]

    plt.figure("vel mag")
    plt.plot(ds_vel.time, ds_vel.u_ship, label="ship")
    plt.plot(vel.time, -vel, label="bottom")

    plt.legend()

    plt.show()

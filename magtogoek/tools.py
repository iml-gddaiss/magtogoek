"""
This modules contains mathematical and scientific functions.
They are separated from utils.py due to longer import time.
"""
import typing as tp

import numpy as np
import xarray as xr
from nptyping import NDArray
from pygeodesy.ellipsoidalVincenty import LatLon


def flag_data(dataset: xr.Dataset, var: str, flag_thres: int = 2, ancillary_variables: str = None):
    """

    Parameters
    ----------
    dataset :
        The variable `var` must be in the dataset along with `var+'_QC'`.
    var :
    ancillary_variables :
    flag_thres :

    Returns
    -------

    """
    if ancillary_variables is None:
        ancillary_variables = dataset[var].attrs["ancillary_variables"]

    return dataset[var].where(dataset[ancillary_variables].data <= flag_thres)


def round_up(x: float, scale: float=1):
    return np.ceil(np.asarray(x) * 1 / scale) * scale


def nans(shape: tp.Union[list, tuple, np.ndarray]) -> np.ndarray:
    """return array of nan of shape `shape`"""
    return np.full(shape, np.nan)


def polar_histo(dataset: xr.Dataset, x_vel: str, y_vel: str, r_max: float):
    u = flag_data(dataset, x_vel).data.flatten()
    v = flag_data(dataset, y_vel).data.flatten()
    ii = np.isfinite(u) & np.isfinite(v)

    azimut, radius = cartesian2northpolar(u[ii], v[ii])

    rN, aN = 30, 180
    rbins, abins = np.linspace(0, r_max, rN), np.linspace(0, 2 * np.pi, aN)

    return np.histogram2d(azimut, radius, bins=(abins, rbins))


def cartesian2northpolar(x, y):
    """Return the azimut (north clockwise)  and the radius from x, y vector."""
    return (np.arctan2(x, y) + 2 * np.pi) % (2 * np.pi), np.hypot(x, y)


def circular_distance(a1, a2, units="rad"):
    """
    Function circdist usage:
        d   =   circdist(a1,a2,units='rad')

    Returns to 'd' the distance between angles a1 and a2
    expected to be radians by default, or degrees if units
    is specified to 'deg'.
    Parameters
    ----------
    a1, a2 : float
        Input angle.
    units : str
        Units of input angles ('deg', 'rad')
    Returns
    -------
    float
        Angular distance between `a1` and `a2`.

    Notes
    -----
    Taken from jeanlucshaw adcp2nc: https://github.com/jeanlucshaw/adcp2nc/
    """
    if units == "deg":
        a1 = np.pi * a1 / 180
        a2 = np.pi * a2 / 180

    if np.isscalar(a1) and np.isscalar(a2):
        v1 = np.array([np.cos(a1), np.sin(a1)])
        v2 = np.array([np.cos(a2), np.sin(a2)])
        dot = np.dot(v1, v2)
    elif not np.isscalar(a1) and np.isscalar(a2):
        a2 = np.tile(a2, a1.size)
        v1 = np.array([np.cos(a1), np.sin(a1)]).T
        v2 = np.array([np.cos(a2), np.sin(a2)]).T
        dot = (v1 * v2).sum(-1)
    else:
        v1 = np.array([np.cos(a1), np.sin(a1)]).T
        v2 = np.array([np.cos(a2), np.sin(a2)]).T
        dot = (v1 * v2).sum(-1)

    res = np.arccos(np.clip(dot, -1.0, 1.0))

    if units == "deg":
        res = 180 * res / np.pi

    return res


def vincenty(p0: tp.Tuple[float, float], p1: tp.Tuple[float, float]) -> float:
    """Calculate the distance between 2 coordinates with pygeodesy.ellipsoidalVincenty.LatLon

    Great Circule Distance with Datum = WGS84

    Parameters
    ----------
    p0 :
       (longitude, latitude) of the first points in decimal degrees
    p1 :
       (longitude, latitude) of the second points in decimal degrees

    Returns
    -------
    distance :
        distance between the two points in meters.
    """

    return LatLon(p0[1], p0[0]).distanceTo(LatLon(p1[1], p1[0]))


def get_gps_bearing(p0: tp.Tuple[float, float], p1: tp.Tuple[float, float]) -> float:
    """Calculate the bearing between two coordinates with pygeodesy.ellipsoidalVincenty.LatLon

    Datum = WGS84

    Parameters
    ----------
    p0 :
       (longitude, latitude) of the first points in decimal degrees
    p1 :
       (longitude, latitude) of the second points in decimal degrees

    Returns
    -------
    bearing in degrees [0, 360]
    """

    return LatLon(p0[1], p0[0]).initialBearingTo(LatLon(p1[1], p1[0]))


def rotate_2d_vector(
    X: NDArray, Y: NDArray, angle: float
) -> tp.Tuple[NDArray, NDArray]:
    """Rotates the X and Y component of the velocities anti-clockwise.

    [X_r]  = [cos(angle), -sin(angle)][X]
    [Y_r]  = [sin(angle),  cos(angle)][Y]

    Parameters
    ----------
    X:
       Velocity components of velocities along X

    Y:
       Velocity components of velocities along Y

    angle:
        Angle of rotation in decimal degree

    Returns
    -------
    X_r :
        Rotated velocity components along X_r.
    Y_r :
        Rotated velocity components along Y_r.
    """

    angle_rad = np.deg2rad(angle)

    X_r = np.cos(angle_rad) * X - np.sin(angle_rad) * Y
    Y_r = np.sin(angle_rad) * X + np.cos(angle_rad) * Y

    return X_r, Y_r
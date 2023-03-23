"""
Date: February 2023
Made by jeromejguay

This module contains general mathematical and scientific functions.
"""
import numpy as np
import typing as tp
from nptyping import NDArray
from pygeodesy.ellipsoidalVincenty import LatLon


def cartesian2north_polar(x: NDArray, y: NDArray):
    """Compute the azimut (north clockwise)  and the radius from x, y vector.

    Parameters
    ----------
    x:
        Vector x component
    y:
        Vector y component

    Returns
    -------
    azimut (north clockwise), radius
    """
    return (np.arctan2(x, y) + 2 * np.pi) % (2 * np.pi), np.hypot(x, y)


def north_polar2cartesian(radius: NDArray, azimut: NDArray) -> tp.Tuple[NDArray, NDArray]:
    """ Compute x and y from radius and azimut (degree) (north clockwise)

    Parameters
    ----------
    radius:
        Vector norm
    azimut (degree):
        Vector direction (north clockwise)

    Returns
    -------
    x, y

    """
    return radius * np.sin(np.deg2rad(azimut)), radius * np.cos(np.deg2rad(azimut))


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
        a1 = np.deg2rad(a1)
        a2 = np.deg2rad(a2)
        #a1 = np.pi * a1 / 180
        #a2 = np.pi * a2 / 180

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
        res = np.rad2deg(res)
        #res = 180 * res / np.pi

    return res


def vincenty(p0: tp.Tuple[float, float], p1: tp.Tuple[float, float]) -> float:
    """Calculate the distance between 2 coordinates with pygeodesy.ellipsoidalVincenty.LatLon

    Great Circle Distance with Datum = WGS84

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


def rotate_heading(heading: NDArray, angle: tp.Union[NDArray, float]) -> NDArray:
    """
    Equation for the heading: (heading + 180 + angle) % 360 - 180
        1. [-180, 180[ -> [0, 360[ -> [angle, 360+angle[
        2. [angle, 360+angle[ -> [0, 360[ -> [-180, 180[

    Parameters
    ----------
    heading :
        heading (-180 to 180) | North = 0, East = 90
    angle :
        Clockwise angle to rotate.

    Returns
    -------
    Rotated Heading
    """
    return (heading + 180 + angle) % 360 - 180



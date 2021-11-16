"""
Set of functions and objects used for adcp processing
"""
import typing as tp
from datetime import datetime
from pathlib import Path

import click
import numpy as np
from nptyping import NDArray
from pandas import Timestamp, to_datetime


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


def dday_to_datetime64(dday: np.ndarray, yearbase: int) -> tp.Tuple[NDArray, NDArray]:
    """Convert time recorded time to pandas time (np.datetime64[s]).

    Replace time coordinates with datetime64 in strftime='%Y-%m-%d %H:%M:%S'
    Add `time_string` variables to dataset (strftime='%Y-%m-%d %H:%M:%S')

    Parameters
    ----------
    yearbase:
    dday:

    """
    start_time = Timestamp(str(yearbase) + "-01-01")
    time = np.array(
        to_datetime(dday, unit="D", origin=start_time, utc=True).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        dtype="datetime64[s]",
    )
    time_string = time.astype(str)

    return time, time_string


def datetime_to_dday(
    datetimes: tp.List[tp.Type[datetime]], yearbase: int = None
) -> NDArray:
    """Convert sequence of datetime to an array of dday since yearbase

    If yearbase is none, default to the year of the first datetime.
    """
    yearbase = yearbase if yearbase else datetimes[0].year

    return (
        np.array([(t - datetime(yearbase, 1, 1)).total_seconds() for t in datetimes])
        * 1
        / (3600 * 24)
    )


def get_datetime_and_count(trim_arg: str):
    """Get datetime and count from trim_arg.

    If `trim_arg` is None, returns (None, None)
    If 'T' is a datetime or a count returns (Timestamp(trim_arg), None)
    Else returns (None, int(trim_arg))

    Returns:
    --------
    datetime:
        None or pandas.Timestamp
    count:
        None or int

    """

    if trim_arg:
        if "T" in trim_arg:
            return (Timestamp(trim_arg), None)
        else:
            return (None, int(trim_arg))
    else:
        return (None, None)

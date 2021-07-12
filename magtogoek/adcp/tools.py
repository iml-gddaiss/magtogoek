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


def magnetic_to_true(
    magnetic_east: NDArray, magnetic_north: NDArray, magnetic_declination: float
) -> tp.Tuple[NDArray, NDArray]:
    """Convert velocities from magnetic to true(geographic).
    FIXME

    angle:  magnetic_declination

    [true_east,  = [[np.cos(angle), -np.sin(angle)] * [magnetic_east,
     true_north]    [np.sin(angle),  np.cos(angle)]]    magnetic_north]

    Parameters
    ----------
    magnetic_east :
       Eastward velocities in the magnetic frame of reference.

    magnetic_north :
       Northward velocities in the magnetic frame of reference.

    declination :
        Measured in the geographic frame of reference in decimal degrees.

    Returns
    -------
    true_east :
        Eastward velocities in the geographic frame of reference
    true_north :
        Northward velocities in the geographic frame of reference
    """

    def R(angle):
        return [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]

    angle_rad = np.radians(magnetic_declination)

    true_east = np.cos(angle_rad) * magnetic_east - np.sin(angle_rad) * magnetic_north
    true_north = np.sin(angle_rad) * magnetic_east + np.cos(angle_rad) * magnetic_north

    return true_east, true_north


def dday_to_datetime64(dday: tp.List, yearbase: int) -> tp.Tuple[NDArray, NDArray]:
    """Convert time recorded time to pandas time (np.datetime64[s]).

    Replace time coordinates with datetime64 in strftime='%Y-%m-%d %H:%M:%S'
    Add `time_string` variables to dataset (strftime='%Y-%m-%d %H:%M:%S')

    Parameters
    ----------
    dataset:
       FIXME
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
    """Get datime and count from trim_arg.

    If `trim_arg` is None, returns (None, None)
    If 'T' is a datetimeor a count returns (Timstamp(trim_arg), None)
    Else returns (None, int(trim_arg))

    Returns:
    --------
    datetime:
        None or pandas.Timstamp
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

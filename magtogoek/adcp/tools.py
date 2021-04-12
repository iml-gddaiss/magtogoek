"""
Set of functions and objects used for adcp processing
"""
import typing as tp
from datetime import datetime

import click
import numpy as np
from nptyping import NDArray
from pandas import Timestamp, to_datetime
from path import Path


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

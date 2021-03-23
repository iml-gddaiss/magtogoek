"""
Set of functions and objects used for adcp processing
"""
import typing as tp
from datetime import datetime

import click
import numpy as np
import pandas as pd
from nptyping import NDArray
from path import Path


def get_files_from_expresion(filenames: tp.Tuple[str, tp.List[str]]) -> tp.List[str]:
    """Get existing files from expression.

    Returns a list of existing files.

    Raises:
    -------
    FileNotFoundError:
        If files does not exist, or a matching regex not found.
    """
    if isinstance(filenames, str):
        p = Path(filenames)
        if p.isfile():
            filenames = [filenames]
        else:
            filenames = sorted(map(str, p.parent.glob(p.name)))
            if len(filenames) == 0:
                raise FileNotFoundError(f"Expression `{p}` does not match any files.")

    return sorted(filenames)


def nans(shape: tp.Tuple[list, tuple, NDArray]) -> NDArray:
    """return array of nan of shape `shape`"""
    return np.full(shape, np.nan)


def magnetic_to_true(
    magnetic_longitude: NDArray, magnetic_latitude: NDArray, magnetic_declination: float
) -> tp.Tuple[NDArray, NDArray]:
    """Covert coordiniates from magnetic to true(geographic).

    [true_longitude,  = [[np.cos(m_d), -np.sin(m_d)]   [magnetic_longitude,
     true_latitude]     [np.sin(m_d), np.cos(m_d)]] *  magnetic_latitude]

    Parameters
    ----------
    longitude :
        Decimal degrees (East)
    latitude:
        Decimal degress (North)
    declination:
        Measured in teh geogrpahic frame of reference in decimal degrees.

    Returns:
    --------
    true_longitude:

    true_latitude:

    """

    def R(angle):
        return [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]

    angle_rad = -np.radians(magnetic_declination)
    longitude, longitude = np.split(
        np.dot(R(angle_rad), [magnetic_longitude, magnetic_latitude]), 2
    )


def dday_to_datetime64(dday: tp.List, yearbase: int) -> tp.Tuple[NDArray, NDArray]:
    """Convert time recorded time to pandas time (np.datetime64[s]).

    Replace time coordinates with datetime64 in strftime='%Y-%m-%d %H:%M:%S'
    Add `time_string` variables to dataset (strftime='%Y-%m-%d %H:%M:%S')

    Parameters
    ----------
    dataset:
       FIXME
    """
    start_time = pd.Timestamp(str(yearbase) + "-01-01")
    time = np.array(
        pd.to_datetime(dday, unit="D", origin=start_time, utc=True).strftime(
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


class Logger:
    def __init__(self, logbook: str = "", level: int = 0):

        self.logbook = logbook
        self.w_count = 0
        self.level = level

    def __repr__(self):
        return self.logbook

    def section(self, section: str, t: bool = False):
        """
        Parameters:
        -----------
        section:
           Section's names.
        t:
           Log time if True.

        """
        time = "" if t is False else " " + self._timestamp()
        self.logbook += "[" + section + "]" + time + "\n"
        click.secho(section, fg="green") if self.level < 1 else None

    def log(self, msg: str, t: bool = False):
        """
        Parameters:
        -----------
        msg:
           Message to log.
        t:
           Log time if True.
        """
        if isinstance(msg, list):
            [self.log(m, t=t) for m in msg]
        else:
            if self.level < 1:
                print(msg)
            msg = msg if t is False else self._timestamp() + " " + msg
            self.logbook += " " + msg + "\n"

    def warning(self, msg: str, t: bool = False):
        """
        Parameters:
        -----------
        msg:
           Message to log.
        t:
           Log time if True.
        """
        if isinstance(msg, list):
            [self.warning(m, t=t) for m in msg]
        else:
            if self.level < 2:
                click.echo(click.style("WARNING:", fg="yellow") + msg)
                self.w_count += 1
            msg = msg if t is False else self._timestamp() + " " + msg
            self.logbook += " " + msg + "\n"

    @staticmethod
    def _timestamp():
        return pd.Timestamp.now().strftime("%Y-%m-%d %Hh%M:%S")

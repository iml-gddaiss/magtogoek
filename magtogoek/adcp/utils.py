"""
Set of functions and objects used for adcp processing
"""
import typing as tp

import click
import numpy as np
import pandas as pd
import xarray as xr
from nptyping import NDArray


def nans(shape: tp.Tuple[list, tuple, NDArray]) -> NDArray:
    """return array of nan of shape `shape`"""
    return np.full(shape, np.nan)


def magnetic_to_true(dataset: tp.Type[xr.Dataset]):
    """Covert coordiniates from magnetic to true(geographic).

    The coordinates needs to be in decimal degrees and in a East(x)-North(y)
    frame of reference. The coordinates are rotated from magnetics to true
    using the `magnectic_declination` angle which need to be  measured in
    the geographic frame of reference in decimal degrees.

    [east_true,  = [[np.cos(x), -np.sin(x)]   [magnetic_east,
    north_true]     [np.sin(x), np.cos(x)]] *  magnetic_north]


    Parameters
    ----------
    dataset :
        dataset with variable lon: East coordinates measured by the ADCP.
        dataset with variable lat: North coordinates measured by the ADCP.
        dataset with attrs magnetic_declination.
    """

    def R(angle):
        return [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]

    angle_rad = -np.radians(dataset.attrs["magnetic_declination"])
    dataset.lon.values, dataset.lat.values = np.split(
        np.dot(R(angle_rad), [dataset.lon, dataset.lat]), 2
    )


def dday_to_datetime64(dday, yearbase):
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


class Logger:
    def __init__(self, logbook=""):

        self.logbook = "" + logbook
        self.w_count = 0
        self.silent = False

    def __repr__(self):
        return self.logbook

    def section(self, msg, t=False):
        time = "" if t is False else " " + self._timestamp()
        self.logbook += "[" + msg + "]" + time + "\n"

        click.secho(msg, fg="green") if not self.silent else None

    def log(self, msg, t=False):
        if isinstance(msg, list):
            [self.log(m) for m in msg]
        else:
            if not self.silent:
                if "WARNING:" in msg:
                    click.echo(click.style("WARNING:", fg="yellow") + msg[8:])
                    self.w_count += 1
                else:
                    print(msg)
            msg = msg if t is False else self._timestamp() + " " + msg
            self.logbook += " " + msg + "\n"

    def silence(self, silent):
        self.silent = silent

    @staticmethod
    def _timestamp():
        return pd.Timestamp.now().strftime("%Y-%m-%d %Hh%M:%S")

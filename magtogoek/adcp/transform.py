"""Module that contains transformation function for adcp data.
TODO
----
-> test if it works or if you need masked arrays.

Notes
-----
Move Coordinate transformation here
Move motion correction to here.
"""
from typing import *
import numpy as np
import xarray as xr
from pycurrents.adcp import transform


def coordsystem2earth(dataset: xr.Dataset, vels: Tuple[str] = None):
    """Transforms beam and xyz coordinates to enu coordinates

        FIXME

        Replace the values of data.vel, data.bt_vel with East, North and Up velocities
        and the velocity error for 4 beams ADCP. UHDAS transform functions are used to
        transform for beam coordinates and xyz to east-north-up (enu). These function
        can use a three-beam solution by faking a fourth beam.

        Also change the values of of `coordinates` in data.trans.

        beam coordinates : Velocity measured along beam axis.
        xyz coordinates : Velocity in a cartesian coordinate system in the ADCP frame of reference.
        enu coordinates : East North Up measured using the heading, pitch, roll of the ADCP.
        """
    if vels is None:
        vels = ('u', 'v', 'w', 'e')

    bt_vels = ('bt_' + v for v in vels)

    if dataset.attrs["coord_system"] == "beam" and dataset.attrs["beam_angle"] is not None:
        _beam2xyze(dataset, vels)
        if all(v in dataset for v in bt_vels):
            _beam2xyze(dataset, bt_vels)
        dataset.attrs["coord_system"] = "xyz"

    if any((dataset['heading'] == 0).all(),
           (dataset['roll_'] == 0).all(),
           (dataset['pitch'] == 0).all()):
        _xyze2enu(dataset, vels)
        if all(v in dataset for v in bt_vels):
            _xyze2enu(dataset, vels)
        dataset.attrs["coord_system"] = "earth"


def _beam2xyze(dataset: xr.Dataset, vels: Tuple[str]):
    """

    Parameters
    ----------
    dataset
    vels

    Returns
    -------

    """
    trans = transform.Transform(angle=dataset.attrs["beam_angle"], geometry=dataset.attrs["beam_pattern"])
    xyze = trans.beam_to_xyz(np.stack([dataset[v].T for v in vels], axis=2))
    for i, v in enumerate(vels):
        dataset[v].values = np.round(xyze[:, :, i].T, decimals=3)


def _xyze2enu(dataset: xr.Dataset, vels: Tuple[str]):
    """

    Parameters
    ----------
    dataset
    vels

    Returns
    -------

    """
    enu = transform.rdi_xyz_enu(
        np.stack([dataset[v].T for v in vels], axis=2),
        dataset['heading'], dataset['pitch'], dataset['roll_'],
        orientation=dataset.attrs['orientation'],
    )
    for i, v in enumerate(vels):
        dataset[v].values = np.round(enu[:, :, i].T, decimals=3)






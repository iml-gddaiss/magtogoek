"""Module that contains transformation function for adcp data.

TODO
----



Notes
-----
-> Seems to work just fine
-> Move Coordinate transformation here.
-> Move motion correction to here.

-> qc_variables will not be transformed. Qc need to be run afterward.

"""
from typing import *
import numpy as np
import xarray as xr
from pycurrents.adcp import transform

from magtogoek.utils import Logger

l = Logger(level=0)


def motion_correction(dataset: xr.Dataset, mode: str):
    """Carry motion correction on velocities.

    If mode is 'bt' the motion correction is along x, y, z.
    If mode is 'nav' the motion correction is along x, y.
    """
    l.reset()

    if mode == "bt":
        if all(f"bt_{v}" in dataset for v in ["u", "v", "w"]):
            for field in ["u", "v", "w"]:
                dataset[field].values -= dataset[f"bt_{field}"].values
            l.log("Motion correction carried out with bottom track")
        else:
            l.warning("Motion correction aborted. Bottom velocity (bt_u, bt_v, bt_w) missing")
    elif mode == "nav":
        if all(f"{v}_ship" in dataset for v in ["u", "v"]):
            for field in ["u", "v"]:
                if all([v in dataset for v in ['lon', 'lat']]):
                    velocity_correction = dataset[field + "_ship"].where(np.isfinite(dataset.lon.values), 0)
                else:
                    velocity_correction = dataset[field + "_ship"]
                dataset[field] += np.tile(velocity_correction, (dataset.depth.size, 1))
            l.log("Motion correction carried out with navigation")
        else:
            l.warning("Motion correction aborted. Navigation velocity (u_ship, v_ship) missing")
    else:
        l.warning("Motion correction aborted. Motion correction mode invalid. ('bt' or 'nav')")

    dataset.attrs["logbook"] += l.logbook


def coordsystem2earth(dataset: xr.Dataset) -> xr.Dataset:
    """Transforms beam or xyz coordinates to enu coordinates

    Replace velocities variables in the dataset.

    #FIXME NEEDS SOME MORE TESTING

    Parameters
    ----------
    dataset :
        Required Variables:
            Velocities: ('v1','v2','v3','v4') or ('u', 'v', 'w', 'e').
            'heading'
            'pitch'
            'roll_'
        Required Attributes:
            'beam_angle': int
            'beam_pattern': 'convex' or 'concave'
            'orientation': 'up' or 'down'
    Returns
    -------
    dataset with either:
        beam velocities ('v1','v2','v3','v4') replaced by xyz velocities ('u', 'v', 'w', 'e')
        or
        xyz velocities ('u', 'v', 'w', 'e') replaced by enu velocities ('u', 'v', 'w', 'e').

    Notes
    -----
    UHDAS transform functions are used to transform for beam coordinates and xyz to east-north-up (enu).
    These function can use a three-beam solution by faking a fourth beam.

    beam coordinates : Velocity measured along beam axis.
    xyz coordinates : Velocity in a cartesian coordinate system in the ADCP frame of reference.
    enu coordinates : East North Up measured using the heading, pitch, roll of the ADCP.
    """
    l.reset()

    if dataset.attrs['coord_system'] == "beam" and dataset.attrs['beam_angle'] is not None:
        dataset = beam2xyze(dataset)

    if dataset.attrs['coord_system'] == 'xyz':
        if any([(dataset['heading'] == 0).all(), (dataset['roll_'] == 0).all(), (dataset['pitch'] == 0).all()]):
            l.warning(
                "Roll, Pitch or Heading seems to be missing from the data file. Data not transformed to earth coordinates.")
        else:
            xyz2enu(dataset)

    dataset.attrs["logbook"] += l.logbook

    return dataset


def beam2xyze(dataset: xr.Dataset) -> xr.Dataset:
    """Transform xyze velocities from beam velocities.

    Parameters
    ----------
    dataset :
        Required Variables
            Beam Velocities: ('v1', 'v2', 'v3','v4')
        Required Coordinates
            ["depth", "time"]
        Required Attributes:
            `beam_angle`: int
            `beam_pattern`: `convex` or `concave`
    Returns
    -------
    dataset with beam velocities ('v1','v2','v3','v4') replaced by xyz ('u', 'v', 'w', 'e').
    """
    trans = transform.Transform(angle=dataset.attrs['beam_angle'], geometry=dataset.attrs['beam_pattern'])

    beam_velocities = ('v1', 'v2', 'v3', 'v4')
    _beam2xyz(dataset, trans, beam_velocities)
    xyze_velocities = ('u', 'v', 'w', 'e')
    dataset = dataset.rename({b: v for b, v in zip(beam_velocities, xyze_velocities)})
    l.log('Water velocities transformed from beam to xyz coordinates.')

    bt_beam_velocities = ('bt_v1', 'bt_v2', 'bt_v3', 'bt_v4')
    if all(v in dataset for v in bt_beam_velocities):
        _beam2xyz(dataset, trans, bt_beam_velocities)
        bt_xyze_velocities = ('bt_u', 'bt_v', 'bt_w', 'bt_e')
        dataset = dataset.rename({b: v for b, v in zip(bt_beam_velocities, bt_xyze_velocities)})
        l.log('Bottom velocities transformed from beam to xyz coordinates.')

    dataset.attrs['coord_system'] = "xyz"

    return dataset


def _beam2xyz(dataset: xr.Dataset, trans: transform.Transform, velocities: Tuple[str]):
    """See beam2xyze
    """
    trans_vel = trans.beam_to_xyz(np.stack([dataset[v].T for v in velocities], axis=2))
    for i, v in enumerate(velocities):
        dataset[v] = (["depth", "time"], np.round(trans_vel[:, :, i].T, decimals=3))


def xyz2beam(dataset: xr.Dataset) -> xr.Dataset:
    """Transform beam velocities from xyz velocities.

    Parameters
    ----------
    dataset :
        Required Variables
            Beam Velocities: ('u', 'v', 'w', 'e')
        Required Coordinates
            ["depth", "time"]
        Required Attributes:
            `beam_angle`: int
            `beam_pattern`: `convex` or `concave`
    Returns
    -------
    dataset with xyz ('u', 'v', 'w', 'e') replaced by beam velocities ('v1','v2','v3','v4').
    """
    trans = transform.Transform(angle=dataset.attrs['beam_angle'], geometry=dataset.attrs['beam_pattern'])

    xyze_velocities = ('u', 'v', 'w', 'e')
    _xyz2beam(dataset, trans, xyze_velocities)
    beam_velocities = ('v1', 'v2', 'v3', 'v4')
    dataset = dataset.rename({v: b for v, b in zip(xyze_velocities, beam_velocities)})
    l.log('Water velocities transformed from xyz to beam coordinates.')

    bt_xyze_velocities = ('bt_u', 'bt_v', 'bt_w', 'bt_e')
    if all(v in dataset for v in bt_xyze_velocities):
        _xyz2beam(dataset, trans, bt_xyze_velocities)
        bt_beam_velocities = ('bt_v1', 'bt_v2', 'bt_v3', 'bt_v4')
        dataset = dataset.rename({v: b for v, b in zip(bt_xyze_velocities, bt_beam_velocities)})
        l.log('Bottom velocities transformed from xyz to beam coordinates.')

    dataset.attrs['coord_system'] = "beam"

    return dataset


def _xyz2beam(dataset: xr.Dataset, trans: transform.Transform, velocities: Tuple[str]):
    """See beam2xyze
    """
    trans_vel = trans.xyz_to_beam(np.stack([dataset[v].T for v in velocities], axis=2))
    for i, v in enumerate(velocities):
        dataset[v] = (["depth", "time"], np.round(trans_vel[:, :, i].T, decimals=3))


def xyz2enu(dataset: xr.Dataset):
    """Transform velocities from xyz velocities to enu.

    Parameters
    ----------
    dataset :
        Required Variables:
            'u', 'v', 'w', 'e'
            'heading'
            'pitch'
            'roll_'
        Required Attributes:
            `orientation`: 'up' or 'down
    """
    velocities = ('u', 'v', 'w', 'e')
    bt_velocities = ('bt_u', 'bt_v', 'bt_w', 'bt_e')

    _xyz2enu(dataset, velocities)
    l.log('Water velocities transformed from xyze to earth coordinates.')
    if all(v in dataset for v in bt_velocities):
        _xyz2enu(dataset, bt_velocities)
        l.log('Bottom velocities transformed from xyze to earth coordinates.')

    dataset.attrs['coord_system'] = "earth"


def _xyz2enu(dataset: xr.Dataset, velocities: Tuple[str]):
    """See xyze2enu
    """
    enu = transform.rdi_xyz_enu(
        np.stack([dataset[v].T for v in velocities], axis=2),
        dataset['heading'], dataset['pitch'], dataset['roll_'],
        orientation=dataset.attrs['orientation'],
    )
    for i, v in enumerate(velocities):
        dataset[v].values = np.round(enu[:, :, i].T, decimals=3)


if __name__ == "__main__":
    # import matplotlib.pyplot as plt
    import xarray as xr

    #
    # # vels=('LCEWAP01', 'LCNSAP01', 'LRZAAP01', 'LERRAP01')
    # vels = ('u', 'v', 'w', 'e')
    #
    path = "/home/jeromejguay/ImlSpace/Data/Sillex2019/"
    #filename = "D30K_001.nc"
    filename = "D60K_000.nc"
    #
    ds = xr.open_dataset(path + filename)
    # ds = ds.sel(time=slice('2018-10-01T00:00:00', '2018-10-01T01:00:00'))
    #
    # compute_beam2xyze(ds, vels)
    # fig, axes = plt.subplots(3, 1)
    # axes[0].imshow(ds.u, aspect='auto')
    # axes[1].imshow(ds.v, aspect='auto')
    # axes[2].imshow(ds.w, aspect='auto')
    #
    # u = ds.u.values
    # compute_xyze2beam(ds, vels)
    # compute_beam2xyze(ds, vels)
    # fig2, axes = plt.subplots(3, 1)
    # axes[0].imshow(ds.u, aspect='auto')
    # axes[1].imshow(ds.v, aspect='auto')
    # axes[2].imshow(ds.w, aspect='auto')
    #
    # du = abs(ds.u.values - u)

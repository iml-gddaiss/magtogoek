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

    #FIXME NEEDS TESTING

    Parameters
    ----------
    dataset :
        Required Variables:
            Velocities: `v1`, `v2`, `v3`, `v4` or `u`, `v`, `w`, `e`
            `heading`
            `pitch`
            `roll_`
        Required Attributes:
            `beam_angle`: int
            `beam_pattern`: `convex` or `concave`
            `orientation`: `up` or `down`

    Notes
    -----
    UHDAS transform functions are used to transform for beam coordinates and xyz to east-north-up (enu).
    These function can use a three-beam solution by faking a fourth beam.

    beam coordinates : Velocity measured along beam axis.
    xyz coordinates : Velocity in a cartesian coordinate system in the ADCP frame of reference.
    enu coordinates : East North Up measured using the heading, pitch, roll of the ADCP.
    """
    l.reset()

    beam_vels_name = ('v1', 'v2', 'v3', 'v4')
    xyze_vels_name = ('u', 'v', 'w', 'e')
    bt_beam_vels_name = ('bt_' + v for v in beam_vels_name)
    bt_xyze_vels_name = ('bt_' + v for v in xyze_vels_name)

    if dataset.attrs['coord_system'] == "beam" and dataset.attrs['beam_angle'] is not None:
        compute_beam2xyze(dataset, beam_vels_name, xyze_vels_name)
        dataset = dataset.drop_vars(beam_vels_name)

        if all(v in dataset for v in bt_beam_vels_name):
            compute_beam2xyze(dataset, bt_beam_vels_name, bt_xyze_vels_name)
            dataset = dataset.drop_vars(('bt_' + v for v in beam_vels_name))

        dataset.attrs['coord_system'] = "xyz"
        l.log('Data transformed from beam to xyze coordinates.')

    if any([(dataset['heading'] == 0).all(), (dataset['roll_'] == 0).all(), (dataset['pitch'] == 0).all()]):
        l.warning("Roll, Pitch or Heading seems to be missing from the data file. Data not transformed to earth coordinates.")
    else:
        xyze2enu(dataset, xyze_vels_name)

        if all(v in dataset for v in bt_xyze_vels_name):
            xyze2enu(dataset, bt_xyze_vels_name)

        dataset.attrs['coord_system'] = "earth"
        l.log('Data transformed from xyze to earth coordinates.')

    dataset.attrs["logbook"] += l.logbook

    return dataset


def compute_beam2xyze(dataset: xr.Dataset, beam_vels_name: Tuple[str] = None, xyze_vels_name: Tuple[str] = None):
    """Compute xyze velocities from beam velocities.

    Add variables `u`, `v`, `w`, `e` to dataset.

    Parameters
    ----------
    dataset :
        Required Attributes:
            `beam_angle`: int
            `beam_pattern`: `convex` or `concave`
    beam_vels_name : Default `v1`, `v2`, `v3`,`v4`
        Name of the beam velocities in the dataset.
    xyze_vels_name : Default `u`, `v`, `w`, `e`
        Name for the computed xyze velocities.
    """
    if beam_vels_name is None:
        beam_vels_name = ('v1', 'v2', 'v3', 'v4')
    if xyze_vels_name is None:
        xyze_vels_name = ('u', 'v', 'w', 'e')

    trans = transform.Transform(angle=dataset.attrs['beam_angle'], geometry=dataset.attrs['beam_pattern'])
    xyze = trans.beam_to_xyz(np.stack([dataset[v].T for v in beam_vels_name], axis=2))

    for i, v in enumerate(xyze_vels_name):
        dataset[v] = (["depth", "time"], np.round(xyze[:, :, i].T, decimals=3))


def compute_xyze2beam(dataset: xr.Dataset, beam_vels_name: Tuple[str] = None, xyze_vels_name: Tuple[str] = None):
    """Compute beam velocities from xyze velocities.

    Add variables `v1`, `v2`, `v3`, `v4` to dataset.

    Parameters
    ----------
    dataset :
        Required Variables:
            xyze_vels_name
        Required Attributes:
            `beam_angle`: int
            `beam_pattern`: `convex` or `concave`
    beam_vels_name : Default `v1`, `v2`, `v3`,`v4`
        Name for the computed beam velocities.
    xyze_vels_name : Default `u`, `v`, `w`, `e`
        Name of the xyze velocities in the dataset.

    """
    if xyze_vels_name is None:
        xyze_vels_name = ('u', 'v', 'w', 'e')
    if beam_vels_name is None:
        beam_vels_name = ('v1', 'v2', 'v3', 'v4')

    trans = transform.Transform(angle=dataset.attrs['beam_angle'], geometry=dataset.attrs['beam_pattern'])
    beam = trans.xyz_to_beam(np.stack([dataset[v].T for v in xyze_vels_name], axis=2))

    for i, v in enumerate(beam_vels_name):
        dataset[v] = (["depth", "time"], np.round(beam[:, :, i].T, decimals=3))


def xyze2enu(dataset: xr.Dataset, vels_name: Tuple[str]=None):
    """Transform xyze velocities to enu velocities.

    Parameters
    ----------
    dataset :
        Required Variables:
            vels_name
            `heading`
            `pitch`
            `roll_`
        Required Attributes:
            `orientation`: `up` or `down`
    vels_name : Default `u`, `v`, `w`, `e`
        Name of the velocities in the dataset.
    """
    if vels_name is None:
        vels_name = ('u', 'v', 'w', 'e')
    enu = transform.rdi_xyz_enu(
        np.stack([dataset[v].T for v in vels_name], axis=2),
        dataset['heading'], dataset['pitch'], dataset['roll_'],
        orientation=dataset.attrs['orientation'],
    )
    for i, v in enumerate(vels_name):
        dataset[v].values = np.round(enu[:, :, i].T, decimals=3)


if __name__ == "__main__":
    #import matplotlib.pyplot as plt
    import xarray as xr
    #
    # # vels=('LCEWAP01', 'LCNSAP01', 'LRZAAP01', 'LERRAP01')
    # vels = ('u', 'v', 'w', 'e')
    #
    path = "/home/jeromejguay/ImlSpace/Data/Sillex2019/"
    filename = "D30K_001.nc"
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

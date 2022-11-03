"""Module that contains transformation function for adcp data.

Notes
-----
Move Coordinate transformation here
Move motion correction to here.
"""
import numpy as np
import xarray as xr
from pycurrents.adcp import transform


def coordsystem2earth(dataset: xr.Dataset, orientation: str):
    """Transforms beam and xyz coordinates to enu coordinates

    NOTE: not properly tested. But it should work.

    Replace the values of data.vel, data.bt_vel with East, North and Up velocities
    and the velocity error for 4 beams ADCP. UHDAS transform functions are used to
    transform for beam coordinates and xyz to east-north-up (enu). These function
    can use a three-beam solution by faking a fourth beam.

    Also change the values of of `coordinates` in data.trans.

    beam coordinates : Velocity measured along beam axis.
    xyz coordinates : Velocity in a cartesian coordinate system in the ADCP frame of reference.
    enu coordinates : East North Up measured using the heading, pitch, roll of the ADCP.

    Parameters
    ----------
    data:
        pycurrents.adcp.rdiraw.Bunche object containing: vel[time, depth, beams], bt_vel[time, beams],
        heading, roll, pitch sysconfig.convex, sysconfig.angle  and trans.coordsystem.

    orientation:
        adcp orientation. Either `up` or `down`.
    Notes
    -----
    Move the prints outside
    """

    if dataset.attrs["coord_system"] not in ["beam", "xyz"]:
        pass
        # l.log(f"Coordsystem value of {dataset.attrs['coord_system']} not recognized. Conversion to enu not available.")

    beam_pattern = dataset.attrs["beam_pattern"]

    xyze, bt_xyze = data.vel, data.bt_vel

    if data.trans.coordsystem == "beam":
        if data.sysconfig.angle:
            trans = transform.Transform(
                angle=data.sysconfig.angle, geometry=beam_pattern
            )
            xyze = trans.beam_to_xyz(data.vel)
            bt_xyze = trans.beam_to_xyz(data.bt_vel)
        else:
            pass
            # l.log("Beam angle missing. Could not convert from beam coordinate.")

    if (data.heading == 0).all() or (dataset['roll_'] == 0).all() or (dataset['pitch'] == 0).all():
        dataset.attrs["coord_system"] = "xyz"

        for i in range(4):
            data.vel[:, :, i] = np.round(xyze[:, :, i], decimals=3)
            data.bt_vel[:, i] = np.round(bt_xyze[:, i], decimals=3)
    else:
        enu = transform.rdi_xyz_enu(
            xyze, dataset['heading'], dataset['pitch'], dataset['roll_'], orientation=orientation,
        )
        bt_enu = transform.rdi_xyz_enu(
            bt_xyze, dataset['heading'], dataset['pitch'], dataset['roll_'], orientation=orientation,
        )
        dataset.attrs["coord_system"] = "earth"

        for i in range(4):
            data.vel[:, :, i] = np.round(enu[:, :, i], decimals=3)
            data.bt_vel[:, i] = np.round(bt_enu[:, i], decimals=3)


def reshape_velocity(dataset: xr.Dataset):
    pass
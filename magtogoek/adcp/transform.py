"""Module that contains transformation function for adcp data.
TODO
----
-> test if it works or if you need masked arrays. ANSWER You don't.
-> test what happens with nan. Maybe I should make a mask.



Notes
-----
-> Move Coordinate transformation here
-> Move motion correction to here.

-> qc_variables will not be transformed. Qc need to be run afterward.

"""
from typing import *
import numpy as np
import xarray as xr
from pycurrents.adcp import transform


def coordsystem2earth(dataset: xr.Dataset, vels: Tuple[str] = None,
                      coord_system="coord_system",
                      beam_angle="beam_angle", beam_pattern="beam_pattern",
                      heading="heading", pitch="pitch", roll="_roll", orientation="orientation"):
    """Transforms beam and xyz coordinates to enu coordinates

    FIXME

    Replace velocities values in the dataset for a 4 beams ADCP.
    UHDAS transform functions are used to transform for beam coordinates and xyz to east-north-up (enu).
    These function can use a three-beam solution by faking a fourth beam.

    beam coordinates : Velocity measured along beam axis.
    xyz coordinates : Velocity in a cartesian coordinate system in the ADCP frame of reference.
    enu coordinates : East North Up measured using the heading, pitch, roll of the ADCP.

    Parameters
    ----------
    dataset
    vels: Defaults ('u', 'v', 'w', 'e')
    coord_system
    beam_angle
    beam_pattern
    heading
    pitch
    roll
    orientation

    Returns
    -------

    """

    if vels is None:
        vels = ('u', 'v', 'w', 'e')

    bt_vels = ('bt_' + v for v in vels)

    if dataset.attrs[coord_system] == "beam" and dataset.attrs[beam_angle] is not None:
        beam2xyze(dataset=dataset, vels=vels, beam_angle=beam_angle,
                  beam_pattern=beam_pattern, coord_system=coord_system)
        if all(v in dataset for v in bt_vels):
            beam2xyze(dataset=dataset, vels=vels,
                      beam_angle=beam_angle, beam_pattern=beam_pattern, coord_system=coord_system)

    if any((dataset[heading] == 0).all(),
           (dataset[roll] == 0).all(),
           (dataset[pitch] == 0).all()):
        xyze2enu(dataset=dataset, vels=vels, heading=heading, pitch=pitch, roll=roll,
                 orientation=orientation, coord_system=coord_system)
        if all(v in dataset for v in bt_vels):
            xyze2enu(dataset=dataset, vels=vels, heading=heading, pitch=pitch, roll=roll,
                     orientation=orientation, coord_system=coord_system)


def beam2xyze(dataset: xr.Dataset, vels: Tuple[str] = None, beam_angle="beam_angle", beam_pattern="beam_pattern",
              coord_system="coord_system"):
    """

    Parameters
    ----------
    dataset
    vels: Defaults ('u', 'v', 'w', 'e')
    beam_angle
    beam_pattern
    coord_system

    Returns
    -------

    """
    if dataset.attrs[coord_system] == "beam":
        if vels is None:
            vels = ('u', 'v', 'w', 'e') #FIXME ('v1','v2',v3','v4') #FOR BEAM
        trans = transform.Transform(angle=dataset.attrs[beam_angle], geometry=dataset.attrs[beam_pattern])
        xyze = trans.beam_to_xyz(np.stack([dataset[v].T for v in vels], axis=2))
        for i, v in enumerate(vels):
            dataset[v].values = np.round(xyze[:, :, i].T, decimals=3)

        dataset.attrs[coord_system] = "xyz"
    else:
        raise ValueError(f'Coordinate system: ({coord_system}) value is not `beam`')


def xyze2beam(dataset: xr.Dataset, vels: Tuple[str] = None, beam_angle="beam_angle", beam_pattern="beam_pattern",
              coord_system="coord_system"):
    """
    #FIXME Should it return ('v1','v2',v3','v4') ?
    Parameters
    ----------
    dataset
    vels: Defaults ('u', 'v', 'w', 'e')
    beam_angle
    beam_pattern
    coord_system

    Returns
    -------

    """
    if dataset.attrs[coord_system] == "xyz":
        if vels is None:
            vels = ('u', 'v', 'w', 'e')
        trans = transform.Transform(angle=dataset.attrs[beam_angle], geometry=dataset.attrs[beam_pattern])
        beam = trans.xyz_to_beam(np.stack([dataset[v].T for v in vels], axis=2))
        for i, v in enumerate(vels):
            dataset[v].values = np.round(beam[:, :, i].T, decimals=3)

        dataset.attrs[coord_system] = "xyz"
    else:
        raise ValueError(f'Coordinate system: ({coord_system}) value is not `xyz`')


def xyze2enu(dataset: xr.Dataset, vels: Tuple[str] = None,
             heading="heading", pitch="pitch", roll="_roll", orientation="orientation",
             coord_system="coord_system"):
    """

    Parameters
    ----------
    dataset
    vels: Defaults ('u', 'v', 'w', 'e')
    heading
    pitch
    roll
    orientation
    coord_system

    Returns
    -------

    """
    if vels is None:
        vels = ('u', 'v', 'w', 'e')
    enu = transform.rdi_xyz_enu(
        np.stack([dataset[v].T for v in vels], axis=2),
        dataset[heading], dataset[pitch], dataset[roll],
        orientation=dataset.attrs[orientation],
    )
    for i, v in enumerate(vels):
        dataset[v].values = np.round(enu[:, :, i].T, decimals=3)

    dataset.attrs[coord_system] = "earth"


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    import xarray as xr
    path = "/home/jeromejguay/ImlSpace/Data/Mingan2021/ADCP/ADCP/"
    filename = "16EED000.nc"

    ds = xr.open_dataset(path+filename)




import numpy as np
import xarray as xr

from magtogoek import logger as l
from magtogoek.process_common import add_correction_attributes_to_dataarray
from magtogoek.sci_tools import rotate_2d_vector, rotate_heading


def apply_motion_correction(dataset: xr.Dataset, mode: str):
    """Carry motion correction on velocities.

    If mode is 'bt' the motion correction is along x, y, z.
    If mode is 'nav' the motion correction is along x, y.
    """

    if mode == "bt":
        if all(f"bt_{v}" in dataset for v in ["u", "v", "w"]):
            for field in ["u", "v", "w"]:
                dataset[field].values -= dataset[f"bt_{field}"].values
            l.log("Motion correction carried out with bottom track")
            for v in ["u", "v", "w"]:
                add_correction_attributes_to_dataarray(dataset[v])
                dataset[v].attrs['corrections'] += "Motion correction carried out with bottom track\n"
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
            for v in ["u", "v", "w"]:
                add_correction_attributes_to_dataarray(dataset[v])
                dataset[v].attrs['corrections'] += "Motion correction carried out with navigation\n"
        else:
            l.warning("Motion correction aborted. Navigation velocity (u_ship, v_ship) missing")
    else:
        l.warning("Motion correction aborted. Motion correction mode invalid. ('bt' or 'nav')")


def apply_magnetic_correction(dataset: xr.Dataset, magnetic_declination: float):
    """Correct velocities and heading to true north and east.

    Computes the relative magnetic correction to apply.

    Rotates velocities vector clockwise by `magnetic_declination` angle effectively
    rotating the frame fo reference by the `magnetic_declination` anti-clockwise.
    Corrects the heading with the `magnetic_declination`:

    Equation for the heading: (heading + 180 + magnetic_declination) % 360 - 180
        [-180, 180[ -> [0, 360[ -> [MD, 360+MD[
        -> [MD, 360+MD[ -> [0, 360[ -> [-180, 180[

    Dataset variables needed:
        `u`, `v` (optional: `bt_u`, `bt_v`), `heading`.


    Parameters
    ----------
    dataset :

    magnetic_declination:
        Absolute magnetic declination

    """

    magnetic_correction = _compute_relative_magnetic_declination(dataset, magnetic_declination)

    dataset.u.values, dataset.v.values = rotate_2d_vector(dataset.u, dataset.v, -magnetic_correction)
    l.log(f"Velocities transformed to true north and true east.")
    for v in ["u", "v"]:
        add_correction_attributes_to_dataarray(dataset[v])
        dataset[v].attrs['corrections'] += "Velocities transformed to true north and true east.\n"

    if all(v in dataset for v in ["bt_u", "bt_v"]):
        dataset.bt_u.values, dataset.bt_v.values = rotate_2d_vector(
            dataset.bt_u, dataset.bt_v, -magnetic_correction
        )
        l.log(f"Bottom velocities transformed to true north and true east.")
        for v in ["bt_u", "bt_v"]:
            add_correction_attributes_to_dataarray(dataset[v])
            dataset[v].attrs['corrections'] += "Bottom velocities transformed to true north and true east.\n"

    # heading goes from -180 to 180
    if "heading" in dataset:
        dataset.heading.values = rotate_heading(dataset.heading.data, magnetic_correction)
        l.log(f"Heading transformed to true north.")
        add_correction_attributes_to_dataarray(dataset['heading'])
        dataset['heading'].attrs['corrections'] += "Heading transformed to true north.\n"

    dataset.attrs["magnetic_declination"] = magnetic_declination

    l.log(f"Absolute magnetic declination: {dataset.attrs['magnetic_declination']} degree north.")


def _compute_relative_magnetic_declination(dataset: xr.Dataset, magnetic_declination: float):
    """Return the difference between the absolute magnetic declination and
    the correction already applied on the data.

    The correction already applied needs to be stored as a global attribute of the dataset.
        dataset.attrs['magnetic_declination'] = ...

    Parameters
    ----------
    dataset :
        Requires global attribute : "magnetic_declination"
    magnetic_declination:
        Absolute magnetic declination

    """
    if dataset.attrs["magnetic_declination"]:
        angle = round((magnetic_declination - dataset.attrs["magnetic_declination"]), 4)
        l.log(f"An additional correction of {angle} degree north was applied.")
        return angle
    return magnetic_declination



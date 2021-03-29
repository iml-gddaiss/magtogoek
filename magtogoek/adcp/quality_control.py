"""
Module that contains fonction for adcp data quality control.

Based mostly on the adcp2nc package by jeanlucshaw: https://github.com/jeanlucshaw/adcp2nc/
"""
import typing as tp

import numpy as np
import xarray as xr
from magtogoek.utils import Logger, circular_distance
from path import Path
from scipy.stats import circmean

# Brand dependent quality control defaults
#    rti_qc_defaults = dict(amp_th=20)
#    rdi_qc_defaults = dict(amp_th=0)


def adcp_qc(
    dataset: tp.Type[xr.Dataset],
    amp_th: float = 30,
    pg_th: float = 90,
    corr_th: float = 64,
    roll_th: float = 20,
    pitch_th: float = 20,
    horizontal_vel_th: float = 5,
    vertical_vel_th: float = 5,
    mode_platform_velocity: bool = False,
    mode_sidelobes: bool = False,
    gps_file: str = None,
    side_lobe_depth: float = None,
) -> tp.Type[xr.Dataset]:
    """
    Perform ADCP quality control.

    This was adaptated from jeanlucshaw adcp2nc package.

    Parameters
    ----------
    dataset :
        ADCP dataset formatted as done by adcp_init.
    amp_th :
        Require more than this amplitude values.
    pg_th :
        Require more than this percentage of good 4-beam transformations.
    corr_th :
        Require more than this beam correlation value.
    roll_th :
        Require roll values be smaller than this value (degrees).
    pitch_th :
        Require pitch values be smaller than this value (degrees).
    horizontal_vel_th:
        Require u, v  values be smaller than this value (meter per seconds).
    veritcal_vel_th:
        Require w  values be smaller than this value (meter per seconds).
    mode_platform_velocity :
        If `True`, will corrected velocities from the platform motion.
    gps_file : str
        GPS dataset with longitude(time), latitude(time).
    mode_sidelobes :
        Use fixed depth or bottom track range to remove side lobe
        contamination. Set to either `dep` or `bt`.
    side_lob_depth : float
        If not `None`, this depth used for removing side lobe contamination.
    Note
    ----
       Quality control flags follow those used by DAISS for ADCP
       data at Maurice-Lamontagne Institute. Meaning of the flagging
       values is the following.
       * 0: no quality control
       * 1: datum seems good
       * 3: datum seems questionable
       * 4: datum seems bad
       * 5: datum has been modified
       * 9: datum is missing
       Data are marked as questionable if they fail only the 4beam
       transformation test. If they fail the 4beam test and any other
       non-critical tests they are marked as bad. Data likely to be
       biased from sidelobe interference are also marked as bad. If
       pitch or roll is greater than 90 degrees data are also marked
       as bad since the ADCP is not looking in the right direction.
    """
    # Work on copy
    #    ds = dataset.copy(deep=True) # This could take all the ram for big files.
    ds = dataset
    l = Logger(ds.logbook)
    # Remove bins with improbable values
    for v in ["u", "v", "w"]:
        plausible = (ds[v] > -10) & (ds[v] < 10)
        ds["u"] = ds["u"].where(plausible)
        ds["v"] = ds["v"].where(plausible)
        ds["w"] = ds["w"].where(plausible)

    # Check for gps file if required
    if gps_file is not None:
        if Path(gps_file).is_file():
            gps_ds = xr.open_dataset(gps_file).interp(time=ds.time)
            try:
                ds["lon"].values = gps_ds.lon
                ds["lat"].values = gps_ds.lat
            except KeyError("Var name must be: `lon`, `lat`"):
                l.warning("GPS data were not found in the gsp netcdf4 file provided.")
        else:
            l.warning("No GPS files found.")

    # Acoustics conditions (True fails)
    corr_condition = np.abs(ds.corr1) < corr_th
    pg_condition = np.abs(ds.pg) < pg_th
    amp_condition = np.abs(ds.amp1) < amp_th

    # Roll conditions (True fails)
    roll_mean = circmean(ds.roll_.values, low=-180, high=180)
    roll_from_mean = circular_distance(ds.roll_.values, roll_mean, units="deg")
    roll_condition = np.abs(roll_from_mean) > roll_th
    roll_looking_condition = np.abs(roll_from_mean) > 90

    # Pitch conditions (True fails)
    pitch_mean = circmean(ds.pitch.values, low=-180, high=180)
    pitch_from_mean = circular_distance(ds.pitch.values, pitch_mean, units="deg")
    pitch_condition = np.abs(pitch_from_mean) > pitch_th
    pitch_looking_condition = np.abs(pitch_from_mean) > 90

    # Motion conditions (True fails)
    motion_condition = roll_condition | pitch_condition
    looking_condition = roll_looking_condition | pitch_looking_condition

    # Outlier conditions (True fails)
    horizontal_velocity = np.sqrt(ds.u ** 2 + ds.v ** 2)
    horizontal_velocity_condition = np.greater(
        horizontal_velocity.values,
        horizontal_vel_th,
        where=np.isfinite(horizontal_velocity),
    )
    vertical_velocity_condition = np.greater(
        ds.w.values,
        vertical_vel_th,
        where=np.isfinite(horizontal_velocity),
    )
    if "u_bt" in ds.data_vars and "v_bt" in ds.data_vars:
        bottom_track_condition = np.greater(
            abs(ds.u_bt.values), horizontal_vel_th, where=np.isfinite(ds.u_bt.values)
        ) | np.greater(
            abs(ds.v_bt.values), horizontal_vel_th, where=np.isfinite(ds.v_bt.values)
        )

    # Missing condition (True fails)
    missing_condition = (
        ~np.isfinite(ds.u) | ~np.isfinite(ds.v) | ~np.isfinite(ds.w)
    ).values

    # Boolean summary of non-critical tests (True fails)
    ncrit_condition = (
        corr_condition
        | amp_condition
        | motion_condition
        | horizontal_velocity_condition
        | vertical_velocity_condition
    )

    # Remove side lob influence (True fails) according to a fixed depths (e.g. Moorings)
    if mode_sidelobes == "dep":
        #        (sidelobe from fixe depth) FIXME

        adcp_depth = ds.depth.mean()  # FIXME not mean. Do it throught time
        beam_angle_cos = np.cos(np.rad(ds.attrs["beam_angle"]))
        # Dowward looking
        if ds.attrs["orientation"] == "down":
            if side_lobe_depth != None:
                sidelobe_condition = ds.z > (
                    adcp_depth + (side_lobe_depth - adcp_depth) * beam_angle_cos
                )
            else:
                l.warning("Can not correct for side lobes, depth not provided.")

        # Upward looking
        elif ds.attrs["looking"] == "up":
            sidelobe_condition = ds.z < adcp_depth * (1 - beam_angle_cos)

        # Orientation unknown
        else:
            l.warning("Can not correct for side lobes, looking attribute not set.")
            sidelobe_condition = np.ones(ds.z.values.size, dtype="bool")

    # Do not perform side lobe removal
    else:
        sidelobe_condition = np.zeros_like(ds.u.values, dtype="bool")

    # Apply condition to bottom track velocities
    if "u_bt" in ds.data_vars and "v_bt" in ds.data_vars:
        for field in ["u_bt", "v_bt", "w_bt"]:
            ds[field] = ds[field].where(bottom_track_condition)

    # Determine quality flags
    ds["flags"] = (["depth", "time"], np.ones(ds.depth.shape + ds.time.shape))
    ds["flags"].values = xr.where(pg_condition, 3, ds.flags)
    ds["flags"].values = xr.where(pg_condition & ncrit_condition, 4, ds.flags)
    ds["flags"].values = xr.where(sidelobe_condition, 4, ds.flags)
    ds["flags"].values = xr.where(looking_condition, 4, ds.flags)
    ds["flags"].values = xr.where(missing_condition, 9, ds.flags)

    # Correct for platform motion
    for field in ["u", "v", "w"]:

        # Bottom track correction in 3D
        if mode_platform_velocity == "bt":
            ds[field] -= ds["%s_bt" % field].values

        # GPS velocity correction in 2D
        elif mode_platform_velocity == "gps" and (field in ["u", "v"]):
            ds[field] += np.tile(
                gps_ds[field].where(np.isfinite(gps_ds.lon.values), 0), (ds.z.size, 1)
            )
            ds["%sship" % field].values = gps_ds[field].values

            # Remove bottom track data if not used
            for v in ["u_bt", "v_bt", "w_bt", "range_bt", "pg_bt", "corr_bt"]:
                if v in ds.data_vars:
                    ds.drop_vars(names=v)

    return ds


if __name__ == "__main__":
    from magtogoek.adcp.loader import load_adcp_binary

    sillex_path = "/media/jeromejguay/5df6ae8c-2af4-4e5b-a1e0-a560a316bde3/home/jeromejguay/WorkSpace_2019/Data/Raw/ADCP/"
    sillex_fns = ["COR1805-ADCP-150kHz009_000001", "COR1805-ADCP-150kHz009_000002"]

    v50_files = (
        "/media/jeromejguay/Bruno/TREX2020/V50/TREX2020_V50_20200911T121242_003_*.ENX"
    )

    pd0_sw_path = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/sw_300_4beam_20deg_piston.pd0"

    ens_sw_path = (
        "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/rowetech_seawatch.ens"
    )

    sonar = "os"
    enr = load_adcp_binary(
        [sillex_path + fn + ".ENR" for fn in sillex_fns],
        sonar=sonar,
        yearbase=2018,
        orientation="down",
    )
    enx = load_adcp_binary(
        [sillex_path + fn + ".ENX" for fn in sillex_fns],
        sonar=sonar,
        yearbase=2018,
        orientation="down",
    )
    sw_pd0 = load_adcp_binary(
        pd0_sw_path, sonar="sw_pd0", yearbase=2020, orientation="down"
    )
    sw = load_adcp_binary(
        ens_sw_path,
        sonar="sw",
        yearbase=2020,
        orientation="down",
        leading_index=100,
        trailing_index=10,
    )

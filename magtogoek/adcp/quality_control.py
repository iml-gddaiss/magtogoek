"""
Module that contains fonction for adcp data quality control.

Based on the adcp2nc package by jeanlucshaw: https://github.com/jeanlucshaw/adcp2nc/

Notes:
------
    Find good default threshold value
"""
import typing as tp
from pathlib import Path

import numpy as np
import xarray as xr
from magtogoek.utils import Logger, circular_distance
from scipy.stats import circmean

# Brand dependent quality control defaults
#    rti_qc_defaults = dict(amp_th=20)
#    rdi_qc_defaults = dict(amp_th=0)

l = Logger(level=0)

IMPLAUSIBLE_VEL_TRESHOLD = 15  # meter per second


def adcp_quality_control(
    dataset: tp.Type[xr.Dataset],
    amp_th: float = 30,
    pg_th: float = 90,
    corr_th: float = 64,
    roll_th: float = 20,
    pitch_th: float = 20,
    horizontal_vel_th: float = 5,
    vertical_vel_th: float = 5,
    error_vel_th: float = 5,
    motion_correction: float = None,
    mode_sidelobes: bool = False,
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

    Notes:
    ------
       SeaDatNet Quality Control Flags Value
       * 0: no_quality_control
       * 1: good_value
       * 2: probably_good_value
       * 3: probably_bad_value
       * 4: bad_value
       * 5: changed_value
       * 6: value_below_detection
       * 7: value_in_excess
       * 8: interpolated_value
       * 9: missing_value

    FIXME
       Data are marked as questionable if they fail only the 4beam
       transformation test. If they fail the 4beam test and any other
       non-critical tests they are marked as bad. Data likely to be
       biased from sidelobe interference are also marked as bad. If
       pitch or roll is greater than 90 degrees data are also marked
       as bad since the ADCP is not looking in the right direction.
    """

    if motion_correction not in [None, "bt", "gps"]:
        raise ValueError(
            f"{motion_correction} is not a valid option for motion_correction. Valid are `bt` or `gps`."
        )

    l.logbook += dataset.logbook

    # condition to check (test)
    amplitude_condition = None
    correlation_condition = None
    percentgood_condition = None
    roll_condition = None
    pitch_condition = None
    sidelobe_condition = None
    horizontal_velocity_condition = None
    vertical_velocity_condition = None
    error_velocity_condition = None
    pressure_condition = None
    temperature_condition = None

    # flags field to make
    u_flags = None
    v_flags = None
    w_flags = None
    vb_flags = None
    pressure_qc = None
    temperature_qc = None

    if motion_correction == "bt":
        bottom_track_motion_correction(dataset)

    if motion_correction == "gps":
        gps_motion_correction(dataset)

    set_implausible_vel_to_nan(dataset, vel_thresh=IMPLAUSIBLE_VEL_TRESHOLD)

    # Acoustics conditions (True fails)
    # NOTE JeanLucShaw used absolute but is it needed ?
    if amp_th:
        amplitude_condition = amplitude_test(dataset, amp_th)
    if corr_th:
        correlation_condition = correlation_test(dataset, corr_th)
    if pg_th:
        percentgood_condition = percentgood_test(dataset, pg_th)

    # Roll conditions (True fails)
    # Distance from mean

    roll_condition = roll_test(dataset, roll_th)
    pitch_condition = pitch_test(dataset, pitch_th)

    # Pitch conditions (True fails)
    # Distance from Mean
    pitch_mean = circmean(dataset.pitch.values, low=-180, high=180)
    pitch_from_mean = circular_distance(dataset.pitch.values, pitch_mean, units="deg")
    pitch_condition = pitch_from_mean > pitch_th

    # Motion(Rotation) conditions (True fails)
    motion_condition = roll_condition | pitch_condition

    # Outlier conditions (True fails)
    horizontal_velocity = np.sqrt(dataset.u ** 2 + dataset.v ** 2)

    horizontal_velocity_condition = np.greater(
        horizontal_velocity.values,
        horizontal_vel_th,
        where=np.isfinite(horizontal_velocity),
    )
    vertical_velocity_condition = np.greater(
        dataset.w.values,
        vertical_vel_th,
        where=np.isfinite(horizontal_velocity),
    )

    # Missing condition (True fails)
    missing_condition = (
        ~np.isfinite(dataset.u) | ~np.isfinite(dataset.v) | ~np.isfinite(dataset.w)
    ).values

    ## def remove_side_influence(dataset):
    # Remove side lob influence (True fails) according to a fixed depths (e.g. Moorings)
    if mode_sidelobes == "dep":
        #        (sidelobe from fixe depth) FIXME

        adcp_depth = dataset.depth.mean()  # FIXME not mean. Do it throught time
        beam_angle_cos = np.cos(np.rad(dataset.attrs["beam_angle"]))
        # Dowward looking
        if dataset.attrs["orientation"] == "down":
            if side_lobe_depth != None:
                sidelobe_condition = dataset.z > (
                    adcp_depth + (side_lobe_depth - adcp_depth) * beam_angle_cos
                )
            else:
                l.warning("Can not correct for side lobes, depth not provided.")

        # Upward looking
        elif dataset.attrs["looking"] == "up":
            sidelobe_condition = dataset.z < adcp_depth * (1 - beam_angle_cos)

        # Orientation unknown
        else:
            l.warning("Can not correct for side lobes, looking attribute not set.")
            sidelobe_condition = np.ones(dataset.z.values.size, dtype="bool")

    # Do not perform side lobe removal
    else:
        sidelobe_condition = np.zeros_like(dataset.u.values, dtype="bool")

    # Boolean summary of non-critical tests (True fails)
    ncrit_condition = (
        correlation_condition
        | amplitude_condition
        | motion_condition
        | horizontal_velocity_condition
        | vertical_velocity_condition
    )

    dataset["flags"] = (
        ["depth", "time"],
        np.ones(dataset.depth.shape + dataset.time.shape),
    )
    dataset["flags"].values = xr.where(percentgood_condition, 3, dataset.flags)
    dataset["flags"].values = xr.where(
        percentgood_condition & ncrit_condition, 4, dataset.flags
    )
    dataset["flags"].values = xr.where(sidelobe_condition, 4, dataset.flags)

    dataset["flags"].values = xr.where(missing_condition, 9, dataset.flags)

    # QC FOR SENTINEL V
    # SENTINELV_FLAG

    return dataset


def set_implausible_vel_to_nan(dataset: tp.Type[xr.Dataset], vel_thresh: float = 10):
    """Set bin with improbable values to Nan."""
    for v in ["u", "v", "w"]:
        plausible = (dataset[v] > -10) & (dataset[v] < 10)
        dataset["u"] = dataset["u"].where(plausible)
        dataset["v"] = dataset["v"].where(plausible)
        dataset["w"] = dataset["w"].where(plausible)
        # flag 4: bad values ? now missing ?


def correlation_test(dataset, threshold):
    """FIXME"""
    return (
        (dataset.corr1 < threshold)
        & (dataset.corr2 < threshold)
        & (dataset.corr3 < threshold)
        & (dataset.corr4 < threshold)
    )


def amplitude_test(dataset, threshold):
    """FIXME"""
    return (
        (dataset.amp1 < threshold)
        & (dataset.amp2 < threshold)
        & (dataset.amp3 < threshold)
        & (dataset.amp4 < threshold)
    )


def percentgood_test(dataset, threshold):
    """FIXME"""
    return dataset.pg < threshold


def bottom_track_motion_correction(dataset: tp.Type[xr.Dataset]):
    """FIXME u, v, w motion correction"""
    for field in ["u", "v", "w"]:
        dataset[field] -= dataset[f"{field}_bt"].values


def gps_motion_correction(dataset: tp.Type[xr.Dataset]):
    """FIXME u, v motion correction"""
    for field in ["u", "v"]:
        dataset[field] += np.tile(
            dataset[field + "_ship"].where(np.isfinite(dataset.lon.values), 0),
            (dataset.depth.size, 1),
        )
        dataset[f"{field}ship"].values = dataset[field].values


def roll_test(dataset: tp.Type[xr.Dataset], thres: float) -> tp.List[bool]:
    """FIXME"""
    roll_mean = circmean(dataset.roll_.values, low=-180, high=180)
    roll_from_mean = circular_distance(dataset.roll_.values, roll_mean, units="deg")
    return roll_from_mean > thres


if __name__ == "__main__":
    import matplotlib.pyplot as plt
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
    #    enr = load_adcp_binary(
    # [sillex_path + fn + ".ENR" for fn in sillex_fns],
    # sonar=sonar,
    # yearbase=2018,
    # orientation="down",
    # )
    enx = load_adcp_binary(
        [sillex_path + fn + ".ENX" for fn in sillex_fns],
        sonar=sonar,
        yearbase=2018,
        orientation="down",
    )
    # sw_pd0 = load_adcp_binary(
    #    pd0_sw_path, sonar="sw_pd0", yearbase=2020, orientation="down"
    # )
    ds = load_adcp_binary(
        ens_sw_path,
        sonar="sw",
        yearbase=2020,
        orientation="down",
        leading_index=None,
        trailing_index=None,
    )

    adcp_quality_control(ds)

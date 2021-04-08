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
    sidelobes_correction: bool = False,
    bottom_depth: float = None,
    beam_angle: float = None,
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
        Require w values be smaller than this value (meter per seconds).
    error_vel_th:
        Require e values be smaller than this value (meter per seconds).
    motion_correction
        If `True`, will corrected velocities from the platform motion.
    sidelobes_correction :
        Use fixed depth or bottom track range to remove side lobe
        contamination. Set to either "dep" or "bt" or None.
    bottom_depth : float
        If not `None`, this depth used for removing side lobe contamination.

    Notes:
    ------
       The same threshold for corr, amp and pg are applied to sentinelV fifth beam.

       Tests returns True when failed.

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

    if beam_angle:
        dataset.attrs["beam_angle"] = beam_angle

    l.logbook += dataset.logbook

    # condition to check (test)
    quality_test = dict(
        amplitude=False,
        correlation=False,
        percentgood=False,
        roll=False,
        pitch=False,
        sidelobe=False,
        horizontal_vel=False,
        vertical_vel=False,
        error_velocity=False,
        pressure=False,
        temperature=False,
        missing=False,
    )

    # flags field to make
    flags = dict(
        u_flags=None,
        v_flags=None,
        w_flags=None,
        vb_flags=None,
        pressure_qc=None,
        temperature_qc=None,
    )
    # if bt bt_u etc are in bt
    if motion_correction == "bt":
        bottom_track_motion_correction(dataset)

    if motion_correction == "gps":
        gps_motion_correction(dataset)

    set_implausible_vel_to_nan(dataset, vel_thresh=IMPLAUSIBLE_VEL_TRESHOLD)

    # NOTE if amp1,2,3,4 in dataset
    if amp_th:
        quality_test["amplitude"] = amplitude_test(dataset, amp_th)
    if corr_th:
        quality_test["correlation"] = correlation_test(dataset, corr_th)
    if pg_th:
        quality_test["percentgood"] = percentgood_test(dataset, pg_th)

    if roll_th:
        quality_test["roll"] = roll_test(dataset, roll_th)
    if pitch_th:
        quality_test["pitch"] = pitch_test(dataset, pitch_th)

    # Outlier conditions (True fails)
    if horizontal_vel_th:
        quality_test["horizontal_vel"] = horizontal_vel_test(dataset, horizontal_vel_th)

    if vertical_vel_th:
        quality_test["vertical_velocity"] = vertical_vel_test(dataset, vertical_vel_th)

    vb_quality_test = vertical_beam_test(dataset, amp_th, corr_th, pg_th)

    if sidelobes_correction:
        quality_test["sidelobe"] = sidelobe_test(
            dataset, sidelobes_correction, bottom_depth
        )

    # Missing condition (True fails)
    motion_condition = quality_test["roll"] | quality_test["pitch"]

    missing_condition = (
        ~np.isfinite(dataset.u) | ~np.isfinite(dataset.v) | ~np.isfinite(dataset.w)
    ).values

    # Boolean summary of non-critical tests (True fails)
    # NOTE none critical is not in quality_test
    ncrit_condition = (
        quality_test["correlation"]
        | quality_test["amplitude"]
        | quality_test["motion"]
        | quality_test["horizontal_velocity"]
        | quality_test["vertical_velocity"]
    )

    dataset["flags"] = (
        ["depth", "time"],
        np.ones(dataset.depth.shape + dataset.time.shape),
    )
    dataset["flags"].values = xr.where(quality_test["percentgood"], 3, dataset.flags)
    dataset["flags"].values = xr.where(
        quality_test["percentgood"] & ncrit_condition, 4, dataset.flags
    )
    dataset["flags"].values = xr.where(quality_test["sidelobe"], 4, dataset.flags)

    dataset["flags"].values = xr.where(missing_condition, 9, dataset.flags)

    return dataset


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


def set_implausible_vel_to_nan(dataset: tp.Type[xr.Dataset], vel_thresh: float = 10):
    """Set bin with improbable values to Nan."""
    for v in ["u", "v", "w"]:
        plausible = (dataset[v] > -10) & (dataset[v] < 10)
        dataset["u"] = dataset["u"].where(plausible)
        dataset["v"] = dataset["v"].where(plausible)
        dataset["w"] = dataset["w"].where(plausible)
        # flag 4: bad values ? now missing ?


def correlation_test(dataset, threshold):
    """FIXME
    NOTE JeanLucShaw used absolute but is it needed ?"""
    return (
        (dataset.corr1 < threshold)
        & (dataset.corr2 < threshold)
        & (dataset.corr3 < threshold)
        & (dataset.corr4 < threshold)
    )


def amplitude_test(dataset, threshold):
    """FIXME
    NOTE JeanLucShaw used absolute but is it needed ?"""
    return (
        (dataset.amp1 < threshold)
        & (dataset.amp2 < threshold)
        & (dataset.amp3 < threshold)
        & (dataset.amp4 < threshold)
    )


def percentgood_test(dataset, threshold):
    """FIXME
    NOTE JeanLucShaw used absolute but is it needed ?"""
    return dataset.pg < threshold


def roll_test(dataset: tp.Type[xr.Dataset], thres: float) -> tp.Type[np.array]:
    """FIXME
    Roll conditions (True fails)
    Distance from mean"""
    roll_mean = circmean(dataset.roll_.values, low=-180, high=180)
    roll_from_mean = circular_distance(dataset.roll_.values, roll_mean, units="deg")
    return roll_from_mean > thres


def pitch_test(dataset: tp.Type[xr.Dataset], thres: float) -> tp.Type[np.array]:
    """FIXME
    Pitch conditions (True fails)
    Distance from Mean
    """
    pitch_mean = circmean(dataset.pitch.values, low=-180, high=180)
    pitch_from_mean = circular_distance(dataset.pitch.values, pitch_mean, units="deg")
    return pitch_from_mean > thres


def horizontal_vel_test(
    dataset: tp.Type[xr.Dataset], thres: float
) -> tp.Type[np.array]:
    """FIXME
    None finite value value will also fail"""
    horizontal_velocity = np.sqrt(dataset.u ** 2 + dataset.v ** 2)

    return np.greater(
        horizontal_velocity.values,
        thres,
        where=np.isfinite(horizontal_velocity),
    )


def vertical_vel_test(dataset: tp.Type[xr.Dataset], thres: float) -> tp.Type[np.array]:
    """FIXME
    None finite value value will also fail"""
    return np.greater(
        abs(dataset.w.values),
        thres,
        where=np.isfinite(dataset.w.values),
    )


def error_vel_test(dataset: tp.Type[xr.Dataset], thres: float) -> tp.Type[np.array]:
    """FIXME
    None finite value value will also fail"""
    return np.greater(
        abs(dataset.e.values),
        thres,
        where=np.isfinite(dataset.w.values),
    )


def vertical_beam_test(
    dataset: tp.Type[xr.Dataset], amp_thres: float, corr_thres: float, pg_thres: float
) -> tp.Type[np.array]:
    """FIXME"""
    quality_test = dict()
    if "vb_amp" in dataset.variables:
        quality_test["vb_amp"] = dataset.vb_amp < amp_thres
    if "vb_corr" in dataset.variables:
        quality_test["vb_corr"] = dataset.vb_corr < corr_thres
    if "vb_pg" in dataset.variables:
        quality_test["vb_pg"] = dataset.vb_pg < pg_thres

    return quality_test


def sidelobe_test(dataset: tp.Type[xr.Dataset], bottom_depth: float = None):
    """FIXME
    Remove side lob influence (True fails) according to a fixed depths (e.g. Moorings)
    Parameters
    ----------
    depth :
        Fixed bottom depth used for sidelob correction
    """

    if dataset.attrs["beam_angle"] and dataset.attrs["orientation"]:
        cos_angle = np.cos(np.radians(dataset.attrs["beam_angle"]))
        if dataset.attrs["orientation"] == "down":
            if "xducer_depth" in dataset:
                xducer_depth = dataset["xducer_depth"]
            elif "xducer_depth" in dataset.attrs:
                xducer_depth = np.full(dataset.time.shape, dataset["xducer_depth"])
            else:
                l.warning(
                    "Sidelobes correct aborded. Adcp depth `xducer_depth` not provided."
                )
                return False

            if bottom_depth:
                bottom_depth = np.full(dataset.time.shape, bottom_depth)
            elif "bt_depth" in dataset:
                bottom_depth = dataset.bt_depth
            else:
                l.warning(
                    "Sidelobes correct aborded. Bottom depth not found or provided."
                )
                return False

            return dataset.z > (
                xducer_depth + (bottom_depth - xducer_depth) * cos_angle
            )

        elif dataset.attrs["orientation"] == "up":
            return dataset.z < xducer_depth * (1 - cos_angle)

        else:
            l.warning("Can not correct for sidelobes, looking attribute not set.")


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

#    adcp_quality_control(ds)

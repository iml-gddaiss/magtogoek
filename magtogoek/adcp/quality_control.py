"""
Module that contains function for adcp data quality control.

Based on the adcp2nc package by jeanlucshaw: https://github.com/jeanlucshaw/adcp2nc/

Notes
-----
   Tests return `True` where cells fail a test.

   - Cells that haven't failed any test are given a flag value of `1` (probably_good_value).
   - Velocities in any direction are set to NaN if greater than 15 meters per second gets a 4.
   - Failing amplitude, correlation, percentgood, roll, pitch, side_lobe, horizontal
   velocity or vertical velocity test returns a flag_value of `3` (probably_bad_value)
   for the corresponding velocity cells.
   - Temperatures outside [-2, 32] Celsius have a flag_value of `4` (bad_value).
   - Pressures outside [0, 180] dbar value have a flag_value of `4` (bad_value).
   and the corresponding velocity cells have a flag_value of `3` (probably_bad_value)
   - The amplitude, correlation and percentgood thresholds are also applied to
   sentinelV fifth beam data.


   SeaDataNet Quality Control Flags Value
   * 0: no_quality_control
   * 1: good_value
   * 2: probably_good_value
   * 3: probably_bad_value
       - Unusual data value, inconsistent with real phenomena.
   * 4: bad_value
       - Obviously erroneous data value.
   * 5: changed_value
   * 6: value_below_detection
   * 7: value_in_excess
   * 8: interpolated_value
   * 9: missing_value

NOTE
IML flags meaning : (Basically the same)
   * 0: no_quality_control
   * 1: value_seems_correct
   * 2: value_appears_inconsistent_with_other_values
   * 3: values_seems_doubtful
   * 4: value_seems_erroneous
   * 5: value_was_modified
   * 9: value_missing

"""
import numpy as np
import typing as tp
import xarray as xr
from pandas import Timestamp
from scipy.stats import circmean

import magtogoek.logger as l
from magtogoek import GLOBAL_IMPOSSIBLE_PARAMETERS, FLAG_REFERENCE, FLAG_VALUES, FLAG_MEANINGS
from magtogoek.sci_tools import circular_distance
from magtogoek.tools import outlier_values_test

ABSOLUTE_IMPOSSIBLE_VELOCITY = 15


def no_adcp_quality_control(dataset: xr.Dataset):
    """Adds var_QC ancillary variables to dataset with value 0.

    Ancillary variables:  temperature, pres, u, v, w.

    SeaDataNet Quality Control Flags Value
    * 0: no_quality_control

    Parameters
    ----------
    dataset :
        ADCP dataset formatted as done by adcp_init.
    """
    l.section("Adcp Quality Controlled")

    l.log("No quality control carried out")

    variables = ["temperature", "pres"]
    if dataset.attrs['coord_system'] == 'beam':
        variables += ['v1', 'v2', 'v3', 'v4']
    else:
        variables += ["u", "v", "w"]

    for var in variables:
        if var in dataset:
            dataset[var + "_QC"] = dataset[var].copy().astype("int8") * 0
            dataset[var + "_QC"].attrs.update({
                'quality_test': "",
                "quality_date": Timestamp.now().strftime("%Y-%m-%d"),
                "flag_meanings": FLAG_MEANINGS,
                "flag_values": FLAG_VALUES,
                "flag_reference": FLAG_REFERENCE
            })

    dataset.attrs["flags_reference"] = FLAG_REFERENCE
    dataset.attrs["flags_values"] = FLAG_VALUES
    dataset.attrs["flags_meanings"] = FLAG_MEANINGS
    dataset.attrs["quality_comments"] = "No quality control."


def adcp_quality_control(
    dataset: xr.Dataset,
    amp_th: int = 30,
    corr_th: int = 64,
    pg_th: int = 90,
    roll_th: float = 20,
    pitch_th: float = 20,
    horizontal_vel_th: float = 5,
    vertical_vel_th: float = 5,
    error_vel_th: float = 5,
    sidelobes_correction: bool = False,
    bottom_depth: float = None,
    bad_pressure: bool = False
):
    """
    Perform ADCP quality control.

    This was adapted from jeanlucshaw adcp2nc package.

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
    vertical_vel_th :
        Require w values be smaller than this value (meter per seconds).
    error_vel_th :
        Require e values be smaller than this value (meter per seconds).
    sidelobes_correction :
        Use fixed depth or bottom track range to remove side lobe
        contamination. Set to either "dep" or "bt" or None.
    bottom_depth :
        If not `None`, this depth used for removing side lobe contamination.
    bad_pressure:
        If True, XducerDepth is set to 0 or to `sensor_depth` if provided.

    Notes
    -----
       Tests return `True` where cells fail a test.

       - Cells that haven't failed any test are given a flag value of `2` (probably_good_value).
       - Failing amplitude, correlation, percentgood, roll, pitch, side_lobe, horizontal
       velocity or vertical velocity test returns a flag_value of `3` (probably_bad_value)
       for the corresponding velocity cells.
       - Temperatures outside [-2, 32] Celsius have a flag_value of `4` (bad_value).
       - Pressures outside [0, 180] dbar value have a flag_value of `4` (bad_value).
       and the corresponding velocity cells have a flag_value of `3` (probably_bad_value)
       - The amplitude, correlation and percentgood thresholds are also applied to
       sentinelV fifth beam data.


       SeaDataNet Quality Control Flags Value
       * 0: no_quality_control
       * 1: good_value
       * 2: probably_good_value
       * 3: probably_bad_value
           - Unusual data value, inconsistent with real phenomena.
       * 4: bad_value
           - Obviously erroneous data value.
       * 5: changed_value
       * 6: value_below_detection
       * 7: value_in_excess
       * 8: interpolated_value
       * 9: missing_value
    """
    l.section("Adcp Quality Control")

    vel_flags = np.ones(dataset.depth.shape + dataset.time.shape).astype(int)
    binary_mask = np.zeros(dataset.depth.shape + dataset.time.shape).astype(int)

    vel_qc_test = []
    binary_mask_tests_value = [None] * 9

    if amp_th is not None:
        l.log(f"amplitude threshold {amp_th}")
        amp_flag = amplitude_test(dataset, amp_th)
        vel_flags[amp_flag] = 3
        vel_qc_test.append(f"amplitude_threshold:{amp_th} (flag=3).")
        binary_mask[amp_flag] += 2 ** 0
        binary_mask_tests_value[0] = amp_th

    if corr_th is not None:
        l.log(f"correlation threshold {corr_th}")
        corr_flag = correlation_test(dataset, corr_th)
        vel_flags[corr_flag] = 3
        vel_qc_test.append(f"correlation_threshold:{corr_th} (flag=3).")
        binary_mask[corr_flag] += 2 ** 1
        binary_mask_tests_value[1] = corr_th

    if pg_th is not None:
        l.log(f"percentgood threshold {pg_th}")
        pg_flag = percentgood_test(dataset, pg_th)
        vel_flags[pg_flag] = 3
        vel_qc_test.append(f"percentgood_threshold:{pg_th} (flag=3).")
        binary_mask[pg_flag] += 2 ** 2
        binary_mask_tests_value[2] = pg_th

    if dataset.attrs['coord_system'] == "earth":
        if horizontal_vel_th is not None:
            l.log(f"horizontal velocity threshold {horizontal_vel_th} m/s")
            horizontal_vel_flag = horizontal_vel_test(dataset, horizontal_vel_th)
            vel_flags[horizontal_vel_flag] = 3
            vel_qc_test.append(f"horizontal_velocity_threshold:{horizontal_vel_th} m/s (flag=3).")
            binary_mask[horizontal_vel_flag] += 2 ** 3
            binary_mask_tests_value[3] = horizontal_vel_th

        if vertical_vel_th is not None:
            l.log(f"vertical velocity threshold {vertical_vel_th} m/s")
            vertical_vel_flag = vertical_vel_test(dataset, vertical_vel_th)
            vel_flags[vertical_vel_flag] = 3
            vel_qc_test.append(f"vertical_velocity_threshold:{vertical_vel_th} m/s (flag=3).")
            binary_mask[vertical_vel_flag] += 2 ** 4
            binary_mask_tests_value[4] = vertical_vel_th

    if dataset.attrs['coord_system'] in ["xyz", "earth"]:
        if error_vel_th is not None:
            l.log(f"error velocity threshold {error_vel_th} m/s")
            error_vel_flag = error_vel_test(dataset, error_vel_th)
            vel_flags[error_vel_flag] = 3
            vel_qc_test.append(f"velocity_error_threshold:{error_vel_th} m/s (flag=3).")
            binary_mask[error_vel_flag] += 2 ** 5
            binary_mask_tests_value[5] = error_vel_th

    if roll_th is not None:
        l.log(f"Roll threshold {roll_th} degree")
        roll_flag = np.tile(roll_test(dataset, roll_th), dataset.depth.shape + (1,))
        vel_flags[roll_flag] = 3
        vel_qc_test.append(f"roll_threshold:{roll_th} degree (flag=4).")
        binary_mask[roll_flag] += 2 ** 6
        binary_mask_tests_value[6] = roll_th

    if pitch_th is not None:
        l.log(f"Pitch threshold {pitch_th} degree")
        pitch_flag = np.tile(pitch_test(dataset, pitch_th), dataset.depth.shape + (1,))
        vel_flags[pitch_flag] = 3
        vel_qc_test.append(f"pitch_threshold:{pitch_th} degree (flag=3).")
        binary_mask[pitch_flag] += 2 ** 7
        binary_mask_tests_value[7] = pitch_th

    if sidelobes_correction is True:
        sidelobe_flag, msg = sidelobe_test(dataset, bottom_depth)
        if isinstance(sidelobe_flag, np.ndarray):
            l.log(f"Sidelobe correction carried out. {msg}. (flag=3).")
            vel_flags[sidelobe_flag] = 3
            vel_qc_test.append("sidelobes")
            binary_mask[sidelobe_flag] += 2 ** 8
            binary_mask_tests_value[8] = sidelobes_correction

    if "pres" in dataset:
        dataset["pres_QC"] = (["time"], np.ones(dataset.pres.shape))
        if bad_pressure is True:
            l.log("Pressure were flagged as bad (4) by the user.")
            dataset["pres_QC"].values *= 4
            dataset["pres_QC"].attrs[
                "quality_test"] = "Flagged as bad (4) by the user."
        else:
            _msg = f"Pressure_threshold: less than {GLOBAL_IMPOSSIBLE_PARAMETERS['pres']['min']} dbar and greater than {GLOBAL_IMPOSSIBLE_PARAMETERS['pres']['max']} dbar (flag=4)."

            pressure_flags = pressure_test(dataset)
            l.log(_msg)
            dataset["pres_QC"].values[pressure_flags] = 4
            dataset["pres_QC"].attrs["quality_test"] = _msg

            vel_flags[np.tile(pressure_flags, dataset.depth.shape + (1,))] = 3
            vel_qc_test.append(dataset["pres_QC"].attrs["quality_test"])

    if "temperature" in dataset:
        _msg=f"Good temperature range {GLOBAL_IMPOSSIBLE_PARAMETERS['temperature']['min']} to {GLOBAL_IMPOSSIBLE_PARAMETERS['temperature']['max']} celsius (flag=4)"
        temperature_QC = np.ones(dataset.temperature.shape)
        temperature_flags = temperature_test(dataset)
        temperature_QC[temperature_flags] = 4
        dataset["temperature_QC"] = (["time"], temperature_QC)
        dataset["temperature_QC"].attrs["quality_test"] = _msg
        l.log(_msg)

    if "vb_vel" in dataset:
        l.log(
            "Fifth beam quality control carried out with"
            + f"amplitude_threshold: {amp_th}" * ("vb_amp" in dataset)
            + f", correlation_threshold: {corr_th}" * ("vb_corr" in dataset)
            + f", percentgood_threshold: {pg_th}" * ("vb_pg" in dataset)
            + "."
        )
        vb_flag = vertical_beam_test(dataset, amp_th, corr_th, pg_th)
        dataset["vb_vel_QC"] = (["depth", "time"], vb_flag * 3)
        dataset["vb_vel_QC"].attrs["quality_test"] = (
            f"amplitude_threshold: {amp_th}\n" * ("vb_amp" in dataset)
            + f"correlation_threshold: {corr_th}\n" * ("vb_corr" in dataset)
            + f"percentgood_threshold: {pg_th}\n" * ("vb_pg" in dataset)
        )

    if dataset.attrs['coord_system'] != "beam":
        vel_flags[flag_implausible_vel(dataset, threshold=ABSOLUTE_IMPOSSIBLE_VELOCITY)] = 4
        l.log(f"Implausible velocity, greater than {ABSOLUTE_IMPOSSIBLE_VELOCITY}, were flagged as bad (4).")

    if dataset.attrs['coord_system'] == "beam":
        velocity_variables = ("v1", "v2", "v3", "v4")
    else:
        velocity_variables = ("u", "v", "w")

    missing_vel = np.sum(
        np.stack(
            [~np.isfinite(dataset[v].values) for v in velocity_variables]
        ), axis=0, dtype=bool)

    vel_flags[missing_vel] = 9

    for v in velocity_variables:
        dataset[v + "_QC"] = (["depth", "time"], vel_flags)
        dataset[v + "_QC"].attrs["quality_test"] = "\n".join(vel_qc_test)

    for var in list(dataset.variables):
        if "_QC" in var:
            dataset[var].attrs["quality_date"] = Timestamp.now().strftime("%Y-%m-%d")
            dataset[var].attrs["flag_meanings"] = FLAG_MEANINGS
            dataset[var].attrs["flag_values"] = FLAG_VALUES
            dataset[var].attrs["flag_reference"] = FLAG_REFERENCE

    dataset.attrs["quality_comments"] = l.logbook.split("[Adcp Quality Control]\n")[1]

    #l.log(f"Quality Control was carried out with {l.w_count} warnings") # l.log is not reseted anymore.
    percent_good_vel = (np.sum(vel_flags == 1) + np.sum(vel_flags == 2)) / (len(dataset.depth) * len(dataset.time))
    l.log(f"{round(percent_good_vel * 100, 2)}% of the velocities have flags of 1 or 2.")

    dataset.attrs["flags_reference"] = FLAG_REFERENCE
    dataset.attrs["flags_values"] = FLAG_VALUES
    dataset.attrs["flags_meanings"] = FLAG_MEANINGS

    dataset["binary_mask"] = (["depth", "time"], binary_mask)

    dataset.attrs["binary_mask_tests"] = [
        "amp",
        "corr",
        "pg",
        "horizontal vel",
        "vertical vel",
        "error",
        "roll",
        "pitch",
        "sidelobe",
    ]
    dataset.attrs["binary_mask_tests_values"] = binary_mask_tests_value


def flag_implausible_vel(
    dataset: xr.Dataset, threshold: float = 15
) -> tp.Type[np.array]:
    """Values greater than `threshold` return True"""
    return (
        (dataset.v > threshold) & (dataset.u > threshold) & (dataset.w > threshold)
    ).data


def correlation_test(dataset: xr.Dataset, threshold: int):
    """FIXME
    Value must be greater than the threshold to be good. (True fails)
    NOTE JeanLucShaw used absolute but is it needed ?"""

    if all(f"corr{i}" in dataset for i in range(1, 5)):
        return (
            (dataset.corr1 < threshold)
            & (dataset.corr2 < threshold)
            & (dataset.corr3 < threshold)
            & (dataset.corr4 < threshold)
        ).data
    else:
        l.warning("Correlation test aborted. Missing one or more corr data")
        return np.full(dataset.depth.shape + dataset.time.shape, False)


def amplitude_test(dataset: xr.Dataset, threshold: int):
    """FIXME
    Value must be greater than the threshold to be good. (True fails)
    NOTE JeanLucShaw used absolute but is it needed ?"""
    if all(f"amp{i}" in dataset for i in range(1, 5)):
        return (
            (dataset.amp1 < threshold)
            & (dataset.amp2 < threshold)
            & (dataset.amp3 < threshold)
            & (dataset.amp4 < threshold)
        ).data
    else:
        l.warning("Amplitude test aborted. Missing one or more amp data")
        return np.full(dataset.depth.shape + dataset.time.shape, False)


def percentgood_test(dataset: xr.Dataset, threshold: int):
    """FIXME
    Value must be greater than the threshold to be good. (True fails)
    NOTE JeanLucShaw used absolute but is it needed ?"""
    if "pg" in dataset:
        return (dataset.pg < threshold).data
    else:
        l.warning("Percent Good test aborted. Missing one or more pg data")
        return np.full(dataset.depth.shape + dataset.time.shape, False)


def roll_test(dataset: xr.Dataset, threshold: float) -> tp.Type[np.array]:
    """FIXME
    Roll conditions (True fails)
    Distance from mean"""
    if "roll_" in dataset:
        roll_mean = circmean(dataset.roll_.values, low=-180, high=180)
        roll_from_mean = circular_distance(dataset.roll_.values, roll_mean, units="deg")
        return roll_from_mean > threshold
    else:
        l.warning("Roll test aborted. Missing roll data")
        return np.full(dataset.time.shape, False)


def pitch_test(dataset: xr.Dataset, threshold: float) -> tp.Type[np.array]:
    """FIXME
    Pitch conditions (True fails)
    Distance from Mean
    """
    if "pitch" in dataset:
        pitch_mean = circmean(dataset.pitch.values, low=-180, high=180)
        pitch_from_mean = circular_distance(
            dataset.pitch.values, pitch_mean, units="deg"
        )
        return pitch_from_mean > threshold

    else:
        l.warning("Pitch test aborted. Missing pitch data")
        return np.full(dataset.time.shape, False)


def horizontal_vel_test(dataset: xr.Dataset, threshold: float) -> tp.Type[np.array]:
    """FIXME
    None finite value value will also fail"""

    horizontal_velocity = np.sqrt(dataset.u ** 2 + dataset.v ** 2)

    return np.greater(horizontal_velocity.values, threshold)


def vertical_vel_test(dataset: xr.Dataset, threshold: float) -> tp.Type[np.array]:
    """FIXME
    None finite value value will also fail"""
    return np.greater(abs(dataset.w.values), threshold)


def error_vel_test(dataset: xr.Dataset, threshold: float) -> tp.Type[np.array]:
    """FIXME
    None finite value value will also fail"""
    return np.greater(abs(dataset.e.values), threshold)


def vertical_beam_test(
    dataset: xr.Dataset,
    amp_threshold: float,
    corr_threshold: float,
    pg_threshold: float,
) -> tp.Type[np.array]:
    """FIXME"""
    vb_test = np.full(dataset.depth.shape + dataset.time.shape, False)
    if "vb_amp" in dataset.variables and amp_threshold:
        vb_test[dataset.vb_amp < amp_threshold] = True
    if "vb_corr" in dataset.variables and corr_threshold:
        vb_test[dataset.vb_corr < corr_threshold] = True
    if "vb_pg" in dataset.variables and pg_threshold:
        vb_test[dataset.vb_pg < pg_threshold] = True

    return vb_test


def sidelobe_test(dataset: xr.Dataset, bottom_depth: float = None) -> tp.Union[tp.Tuple[np.ndarray, str],
                                                                               tp.Tuple[bool, None]]:
    """FIXME
    Test for sidelobe contamination (True fails).

    Returns a boolean array or a False statement if the test cannot be carried out.

    Downward equation:
        bin_depth + 0.5*bin_size > XducerDepth + (bottom_depth - XducerDepth)*cos(beam_angle)
    Upward equation:
        bin_depth - 0.5*bin_size < XducerDepth * ( 1 - cos(beam_angle))

    Parameters
    ----------
    dataset :
    bottom_depth : optional
        Fixed bottom depth to use for sidelobe correction
    Returns
    -------
    sidelobe_flags : Boolean Array
    msg :
    """
    msg = ""
    if dataset.attrs["beam_angle"] and dataset.attrs["orientation"]:
        angle_cos = np.cos(np.radians(dataset.attrs["beam_angle"]))
        depth_array = np.tile(dataset.depth.data, dataset.time.shape + (1,))
        if "xducer_depth" in dataset:
            xducer_depth = dataset["xducer_depth"].data
            msg += "xducer_depth: time dependent"
        elif "xducer_depth" in dataset.attrs:
            xducer_depth = np.tile(dataset.attrs["xducer_depth"], dataset.time.shape)
            msg += f"xducer_depth: constant {xducer_depth[0]}"
        else:
            l.warning(
                "Sidelobes correction aborted. Adcp depth `xducer_depth` not found and one was not provided."
            )
            return False, None

        if dataset.attrs["orientation"] == "down":
            if "bt_depth" in dataset:
                sounding = dataset.bt_depth.data
                msg += ", sounding: bottom range"
            elif bottom_depth is not None:
                sounding = bottom_depth
                msg += f", sounding: constant {sounding}"
            else:
                l.warning(
                    "Sidelobes correction aborted. Bottom depth not found and one was not provided."
                )
                return False, None

            max_depth = xducer_depth + (sounding - xducer_depth) * angle_cos
            return depth_array.T + dataset.attrs["bin_size_m"] / 2 > max_depth, msg

        elif dataset.attrs["orientation"] == "up":
            min_depth = xducer_depth * (1 - angle_cos)
            return depth_array.T - dataset.attrs["bin_size_m"] / 2 < min_depth.T, msg

        else:
            l.warning(
                "Can not correct for sidelobes, `adcp_orientation` parameter not set. Must be `up` or `down`."
            )
            return False, None
    else:
        l.warning("Can not correct for sidelobes, beam_angle not found in raw file.")
        return False, None


def temperature_test(dataset: xr.Dataset) -> np.ndarray:
    """"""
    return outlier_values_test(
        dataset.temperature.data, lower_limit=GLOBAL_IMPOSSIBLE_PARAMETERS['temperature']['min'], upper_limit=GLOBAL_IMPOSSIBLE_PARAMETERS['temperature']['min']
    )


def pressure_test(dataset: xr.Dataset) -> np.ndarray:
    """FIXME"""
    return outlier_values_test(
            dataset.pres.data, lower_limit=GLOBAL_IMPOSSIBLE_PARAMETERS['pres']['min'], upper_limit=GLOBAL_IMPOSSIBLE_PARAMETERS['pres']['max']
        )


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

    test = "SW_PD0"

    if test == "SV":
        _dataset = load_adcp_binary(
            v50_files, sonar="sv", yearbase=2020, orientation="down",
        )

    if test == "ENX":
        _dataset = load_adcp_binary(
            #            [sillex_path + fn + ".ENX" for fn in sillex_fns],
            sillex_path + "COR1805-ADCP-150kHz009.ENX",
            sonar="os",
            yearbase=2018,
            orientation="down",
        )
    if test == "SW_PD0":
        _dataset = load_adcp_binary(
            pd0_sw_path, sonar="sw_pd0", yearbase=2020, orientation="down"
        )
    if test == "ENS":
        _dataset = load_adcp_binary(
            ens_sw_path,
            sonar="sw",
            yearbase=2020,
            orientation="down",
            leading_index=None,
            trailing_index=None,
        )

    adcp_quality_control(
        _dataset,
        roll_th=20,
        pitch_th=20,
        horizontal_vel_th=2,
        vertical_vel_th=0.1,
        sidelobes_correction=True,
        bottom_depth=None,
    )

    _dataset.u.where(_dataset.u_QC == 1).plot()

    plt.show()

#!/usr/bin/python3
"""
author: Jérôme Guay
date: Feb. 12, 2021

This script stores Sea Data Net variables attributes in dictionnaries
using their BODC names.
The resulting dictionnary are meant to be exported in .json.
Json files are be used to set attributes.

The SDN attributes for variables, if available, are:
-'standard_name'
-'units'
-'long_name'
-'ancillary_variables'
-'sdn_parameter_urn'
-'sdn_parameter_name'
-'sdn_uom_urn'
-'sdn_uom_name'
-'legacy_GF3_code'
Some may have additionals attributes, such has depth variables (position = 'down').
In that case, using "depth" as standard_name implies that depth are measured from
the surface and positive downward.

FIXME:
- The attributes "sensor_type" = 'adcp', should only be present for P01 name that explicitly refers to an adcp measuments. Otherwise, it should be added by the instruments subpackage.
- Long name may also be added later. They could also be overwritten later.
- Remove under score in long_name
- PCGDAP01: missing GF3 code.
NOTE:
- PCGDAP01: Use for 4 beam solution, adcp or earth coordinate
- PCGDAP00: Use for beam 1, beam coordinate
- PCGDAP02: Use for beam 2, beam coordinate
- PCGDAP03: Use for beam 3, beam coordinate
- PCGDAP04: Use for beam 4, beam coordinate
"""
import typing as tp

from magtogoek.utils import dict2json

# --------------------------------------------------------------------------- #
# ---------------- Functions to define variables attributes ----------------- #
# --------------------------------------------------------------------------- #


def _L_A_01(s0: str, s1: str, s2: str, s3: str, s4: str) -> tp.Dict[str, str]:
    """skeleton for L(--)AP01 attributes dictionnary"""
    return dict(
        standard_name=f"{s0}ward_sea_water_velocity",
        units="m s-1",
        sensor_type="adcp",
        long_name=f"{s0}ward sea water velocity",
        sdn_parameter_urn=f"SDN:P01::{s1}",
        sdn_parameter_name=(
            f"{s2}ward current velocity "
            "(Eulerian measurement) in the water body "
            "by {s4} acoustic doppler current profiler "
            "(ADCP)"
        ),
        sdn_uom_urn="SDN:P06::UVAA",
        sdn_uom_name="Metres per second",
        legacy_GF3_code=f"SDN:GF3::{s3}",
    )


def _TNIHCE(s0: str) -> tp.Dict[str, str]:
    """skeleton for TNIHCE(-) attributes dictionnary"""
    return dict(
        standard_name="signal_intensity_from_multibeam_acoustic_doppler_velocity_sensor_in_sea_water",
        units="counts",
        sensor_type="adcp",
        long_name=f"ADCP echo intensity beam {s0}",
        sdn_parameter_urn=f"SDN:P01::TNIHCE0{s0}",
        sdn_parameter_name=(
            "Echo intensity from the water body by moored "
            "acoustic doppler current profiler (ADCP) "
            f"beam {s0}"
        ),
        sdn_uom_urn="SDN:P06::UCNT",
        sdn_uom_name="Counts",
        legacy_GF3_code=f"SDN:GF3::BEAM_0{s0}",
    )


def _CMAGZZ(s0: str) -> tp.Dict[str, str]:
    """skeleton for CMAGZZ(-) attributes dictionnary"""
    return dict(
        standard_name="beam_consistency_indicator_from_multibeam_acoustic_doppler_velocity_profiler_in_sea_water",
        units="counts",
        sensor_type="adcp",
        long_name=f"ADCP correlation magnitude beam {s0}",
        sdn_parameter_urn=f"SDN:P01::CMAGZZ0{s0}",
        sdn_parameter_name=(
            "Correlation magnitude of acoustic signal returns "
            "from the water body by moored acoustic doppler "
            f"current profiler (ADCP) beam {s0}"
        ),
        legacy_GF3_code=f"SDN:GF3::CMAG_0{s0}",
    )


def _PCGDAP(s0: str, s1: str) -> tp.Dict[str, str]:
    """skeleton for PCGDAP(-) attributes dictionnary"""
    return dict(
        standard_name="proportion_of_acceptable_signal_returns_from_acoustic_instrument_in_sea_water",
        units="percent",
        sensor_type="adcp",
        long_name=f"ADCP percent good beam {s0}",
        sdn_parameter_urn=f"SDN:P01::{s1}",
        sdn_parameter_name=(
            "Acceptable proportion of signal returns "
            "by moored acoustic doppler current profiler "
            f"(ADCP) beam {s0}"
        ),
        sdn_uom_urn="SDN:P06::UPCT",
        sdn_uom_name="Percent",
        legacy_GF3_code=f"SDN:GF3::PGDP_0{s0}",
    )


def _A_ZZ01(s0: str, s1: str, s2: str, s3: str, s4: str, s5: str) -> tp.Dict[str, str]:
    """skeleton for A(---)ZZ01 attributes dictionnary"""
    return dict(
        standard_name=f"{s0}",
        units=f"degrees_{s1}",
        long_name=f"{s0}",
        sdn_parameter_urn=f"SDN:P01::A{s2}ZZ01",
        sdn_parameter_name=f"{s3} {s1}",
        sdn_uom_urn=f"SDN:P06::{s4}",
        sdn_uom_name=f"Degrees {s1}",
        legacy_GF3_code=f"SDN:GF3::{s5}",
    )


# --------------------------------------------------------------------------- #
# ------------------ Variables attributes are define below ------------------ #
# --------------------------------------------------------------------------- #


sdn = dict(
    Conventions="CF-1.8",
    naming_authority=["CF", "SDN:P01::", "SDN:P06::", "SDN:GF3"],
    LCEWAP01=_L_A_01("east", "LCEWAP01", "East", "EWCT", "moored"),
    LCNSAP01=_L_A_01("north", "LCNSAP01", "North", "NWCT", "moored"),
    LRZAAP01=_L_A_01("up", "LRZAAP01", "Up", "VCSP", "moored"),
    LERRAP01=dict(
        units="m s-1",
        sensor_type="adcp",
        long_name="error velocity in sea water",
        sdn_parameter_urn="SDN:P01::LERRAP01",
        sdn_parameter_name=(
            "Current velocity error in the water "
            "body by moored acoustic doppler current profiler"
            "(ADCP)"
        ),
        sdn_uom_urn="SDN:P06::UVAA",
        sdn_uom_name="Metres per second",
        legacy_GF3_code="SDN:GF3::ERRV",
    ),
    LCEWAS01=_L_A_01("east", "LCEWAS01", "East", "EWCT", "shipborne"),
    LCNSAS01=_L_A_01("north", "LCNSAS01", "North", "NWCT", "shipborne"),
    LRZAAS01=_L_A_01("up", "LRZAAS01", "Up", "VCSP", "shipborne"),
    LERRAS01=dict(
        units="m s-1",
        sensor_type="adcp",
        long_name="error velocity in sea water",
        sdn_parameter_urn="SDN:P01::LERRAS01",
        sdn_parameter_name=(
            "Current velocity error in the water "
            "body by shipborne acoustic doppler current profiler"
            "(ADCP)"
        ),
        sdn_uom_urn="SDN:P06::UVAA",
        sdn_uom_name="Metres per second",
        legacy_GF3_code="SDN:GF3::ERRV",
    ),
    TNIHCE01=_TNIHCE("1"),
    TNIHCE02=_TNIHCE("2"),
    TNIHCE03=_TNIHCE("3"),
    TNIHCE04=_TNIHCE("4"),
    CMAGZZ01=_CMAGZZ("1"),
    CMAGZZ02=_CMAGZZ("2"),
    CMAGZZ03=_CMAGZZ("3"),
    CMAGZZ04=_CMAGZZ("4"),
    PCGDAP00=_PCGDAP("1", "PCGDAP00"),  # beam 1 beam coordinate
    PCGDAP02=_PCGDAP("2", "PCGDAP02"),  # beam 2 beam coordinate
    PCGDAP03=_PCGDAP("3", "PCGDAP03"),  # beam 3 beam coordinate
    PCGDAP04=_PCGDAP("4", "PCGDAP04"),  # beam 4 beam coordinate
    PCGDAP01=dict(  # 4 beam solution earth coordinate
        standard_name=(
            "proportion_of_acceptable_signal"
            "_returns_from_acoustic_instrument"
            "_in_sea_water"
        ),
        units="percent",
        sensor_type="adcp",
        long_name="ADCP percent good of 4 beams solution",
        sdn_parameter_urn="SDN:P01::PCGDA00",
        sdn_parameter_name=(
            "Acceptable proportion of signal returns "
            "by moored acoustic doppler current profiler "
            "(ADCP)"
        ),
        sdn_uom_urn="SDN:P06::UPCT",
        sdn_uom_name="Percent",
    ),
    LRZUVP01=dict(
        standard_name="upward_sea_water_velocity",
        units="m s-1",
        sensor_type="adcp",
        long_name="upward sea water velocity by vertical beam",
        sdn_parameter_urn="SDN:P01::LRZUVP01",
        sdn_parameter_name=("upward_sea_water_velocity_by_vertical_beam"),
        sdn_uom_urn="SDN:P06::UVAA",
        sdn_uom_name="Metres per second",
    ),
    TNIHCE05=dict(
        standard_name="signal_intensity_from_multibeam_acoustic_doppler_velocity_sensor_in_sea_water",
        units="counts",
        sensor_type="adcp",
        long_name="ADCP echo intensity beam 5",
        sdn_parameter_urn="SDN:P01::TNIHCE05",
        sdn_parameter_name=(
            "Echo intensity from the water body by moored acoustic doppler current "
            "profiler (ADCP) vertical beam"
        ),
        sdn_uom_urn="SDN:P06::UCNT",
        sdn_uom_name="Counts",
    ),
    CMAGZZ05=dict(
        standard_name="beam_consistency_indicator_from_multibeam_acoustic_doppler_velocity_profiler_in_sea_water",
        units="counts",
        sensor_type="adcp",
        long_name="ADCP correlation magnitude beam 5",
        sdn_parameter_urn="SDN:P01::CMAGZZ05",
        sdn_parameter_name=(
            "Correlation magnitude of acoustic signal returns from the water body "
            "by moored acoustic doppler current profiler (ADCP) vertical beam"
        ),
        sdn_uom_urn="SDN:P06::UCNT",
        sdn_uom_name="Counts",
    ),
    PCGDAP05=dict(
        standard_name="proportion_of_acceptable_signal_returns_from_acoustic_instrument_in_sea_water",
        units="percent",
        sensor_type="adcp",
        long_name="ADCP percent good beam 5",
        sdn_parameter_urn="SDN:P01::PCGDAP05",
        sdn_parameter_name=(
            "Acceptable proportion of signal returns by moored acoustic doppler "
            "current profiler (ADCP) vertical beam"
        ),
        sdn_uom_urn="SDN:P06::UPCT",
        sdn_uom_name="Percent",
    ),
    ALATZZ01=_A_ZZ01("latitude", "north", "LAT", "Latitude", "DEGN", "lat"),
    ALONZZ01=_A_ZZ01("longitude", "east", "LON", "Longitude", "DEGE", "lon"),
    PTCHGP01=dict(
        standard_name="platform_pitch",
        units="degree",
        long_name="pitch",
        sdn_parameter_urn="SDN:P01::PTCHGP01",
        sdn_parameter_name=(
            "Orientation (pitch) of measurement platform " "by inclinometer"
        ),
        sdn_uom_urn="SDN:P06::UAAA",
        sdn_uom_name="Degrees",
        legacy_GF3_code="SDN:GF3::PTCH",
    ),
    HEADCM01=dict(
        standard_name="platform_orientation",
        units="degree",
        long_name="heading",
        sdn_parameter_urn="SDN:P01::HEADCM01",
        sdn_parameter_name=(
            "Orientation (horizontal relative to true north) "
            "of measurement device {heading}"
        ),
        sdn_uom_urn="SDN:P06::UAAA",
        sdn_uom_name="Degrees",
        legacy_GF3_code="SDN:GF3::HEAD",
    ),
    ROLLGP01=dict(
        standard_name="platform_roll",
        units="degree",
        long_name="roll",
        sdn_parameter_urn="SDN:P01::ROLLGP01",
        sdn_parameter_name=(
            "Orientation (roll angle) of measurement platform "
            "by inclinometer (second sensor)"
        ),
        sdn_uom_urn="SDN:P06::UAAA",
        sdn_uom_name="Degrees",
        legacy_GF3_code="SDN:GF3::ROLL",
    ),
    SVELCV01=dict(
        standard_name="speed of sound in sea water",
        units="m s-1",
        long_name="speed of sound",
        sdn_parameter_urn="SDN:P01::SVELCV01",
        sdn_parameter_name=(
            "Sound velocity in the water body "
            "by computation from temperature "
            "and salinity by unspecified algorithm"
        ),
        sdn_uom_urn="SDN:P06::UVAA",
        sdn_uom_name="Metres per second",
        legacy_GF3_code="SDN:GF3::SVEL",
    ),
    TEMPPR01=dict(
        units="degree_C",
        long_name="temperature",
        sdn_parameter_urn="SDN:P01::TEMPPR01",
        sdn_parameter_name="Temperature of the water body",
        sdn_uom_urn="SDN:P06::UPAA",
        sdn_uom_name="Celsius degree",
        legacy_GF3_code="SDN:GF3::te90",
    ),
    DISTTRAN=dict(
        units="m",
        long_name="height of sea surface",
        sdn_parameter_urn="SDN:P01::DISTTRAN",
        sdn_uom_urn="SDN:P06::ULAA",
        sdn_uom_name="Metres",
        legacy_GF3_code="SDN:GF3::HGHT",
    ),
    DTUT8601=dict(
        sdn_parameter_urn="SDN:P01::DTUT8601",
        sdn_parameter_name=(
            "String corresponding to format "
            "'YYYY-MM-DDThh:mm:ss.sssZ' "
            "or other valid ISO8601 string"
        ),
        sdn_uom_urn="SDN:P06::TISO",
        sdn_uom_name="ISO8601",
        legacy_GF3_code="SDN:GF3::time_string",
    ),
    PPSAADCP=dict(  # bins depth
        standard_name="depth",
        positive="down",  # depth as standard_name implies positive "down"
        units="m",
        sensor_type="adcp",
        long_name="depth vector",
        sdn_parameter_urn="SDN:P01::PPSAADCP",
        sdn_parameter_name=(
            "Depth below surface of the water body"
            "by acoustic doppler current profiler (ADCP) and computation from travel"
            "time averaged from all operational beams and unknown sound velocity profile"
        ),
        sdn_uom_urn="SDN:P06::ULAA",
        sdn_uom_name="Metres",
        legacy_GF3_code="SDN:GF3::DEPH",
    ),
    PRESPR01=dict(
        standard_name="sea_water_pressure",
        units="dbar",
        long_name="pressure",
        sdn_parameter_urn="SDN:P01::PRESPR01",
        sdn_parameter_name="",
        sdn_uom_urn="SDN:P06::UPDB",
        sdn_uom_name="Decibards",
        legacy_GF3_code="SDN:GF3::PRES",
    ),
    APEWGP01=dict(
        units="m s-1",
        long_name="eastward velocity of the measurement platform",
        sdn_parameter_urn="SDN:P01::APEWGP01",
        sdn_parameter_name=(
            "Eastward velocity of measurement platform "
            "relative to ground surface "
            "by unspecified GPS system"
        ),
    ),
    APNSGP01=dict(
        units="m s-1",
        long_name="northward velocity of the measurement platform",
        sdn_parameter_urn="SDN:P01::APNSGP01",
        sdn_parameter_name=(
            "Northward velocity of measurement platform "
            "relative to ground surface "
            "by unspecified GPS system"
        ),
    ),
    ADEPZZ01=dict(  # depth below surface ?
        standard_name="depth",  # depth as standard_name implies positive "down"
        positive="down",
        units="m",
        long_name="depth below surface",
        sdn_parameter_urn="SDN:P01::ADEPZZ01",
        sdn_parameter_name="Depth relative to water surface in the water body",
        Sdn_uom_urn="SDN:P06::ULAA",
        sdn_uom_name="Metres",
        legacy_GF3_code="SDN:GF3::DEPH",
    ),
    ELTMEP01=dict(
        standard_name="time",
        long_name="time",
        sdn_parameter_urn="SDN:P01::ELTMEP01",
        sdn_parameter_name=("Elapsed time relative to 1970-01-01T00:00:00Z"),
        Sdn_uom_urn="SDN:P06::UTBB",
        sdn_uom_name="Seconds",
        legacy_GF3_code="SDN:GF3::N/A",
    ),
    APNSBT01=dict(
        units="m s-1",
        sensor_type="adcp",
        long_name="northward velocity of the measurment platform by bottom tracking",
        sdn_parameter_urn="SDN:P01::",
        sdn_parameter_name=(
            "Northward velocity of measurement platform relative to ground surface "
            "by ADCP bottom tracking."
        ),
    ),
    APEWBT01=dict(
        units="m s-1",
        sensor_type="adcp",
        long_name="eastward velocity of the measurment platform by bottom tracking",
        sdn_parameter_urn="SDN:P01::APEWBT01",
        sdn_parameter_name=(
            "Eastward velocity of measurement platform relative to ground surface "
            "by ADCP bottom tracking."
        ),
    ),
    APZABT01=dict(
        units="m s-1",
        sensor_type="adcp",
        long_name="upward velocity of the measurment platform by bottom tracking",
        sdn_parameter_urn="SDN:P01::APZABT01",
        sdn_parameter_name="Upward velocity of measurement platform by ADCP bottom tracking.",
    ),
    APERBT01=dict(
        units="m s-1",
        sensor_type="adcp",
        long_name="error velocity of the measurment platform by bottom tracking",
        sdn_parameter_urn="SDN:P01::APERBT01",
        sdn_parameter_name=(
            "Error velocity of measurement platform relative to ground surface "
            "by ADCP bottom tracking."
        ),
    ),
)

if __name__ == "__main__":
    # probably not good practice. Creating the absulute path to load the files.
    file_name = "/".join(__file__.split("/")[:-2]) + "/files/sdn.json"
    dict2json(file_name, sdn)

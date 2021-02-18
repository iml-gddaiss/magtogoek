"""
author: Jérôme Guay
date: Feb. 12, 2021

This script stores Sea Data Net variables attributes in dictionnaries
using their BODC names.
The resulting dictionnary are exported in .json file which will be used to set attributes.

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
- The attributes "sensor_type" = 'adcp', should only be present for P01 name that explicitly
refers to an adcp measuments. Otherwise, it should be added by the instruments subpackage.
- Long name may also be added later. They could also be overwritten later.
- It appears that, we do note have a depth variable for instrument depth.
NOTE:
- P01 parameter name for PERCENTGOOD are only good for beam coordinates data.

"""
import typing as tp
import json

# --------------------------------------------------------------------------- #
# ------------------- Making of the json attributes file -------------------- #
# --------------------------------------------------------------------------- #


def make_json_file(file_name: str, variables_attrs: tp.Dict) -> None:
    """Makes json file from dictionnary"""
    with open(file_name, "w") as f:
        json.dump(variables_attrs, f, indent=4)


# --------------------------------------------------------------------------- #
# ---------------- Functions to define variables attributes ----------------- #
# --------------------------------------------------------------------------- #


def _L_AP01(s0: str, s1: str, s2: str, s3: str) -> tp.Dict[str, str]:
    """skeleton for L(--)AP01 attributes dictionnary"""
    return dict(
        standard_name=f"{s0}ward_sea_water_velocity",
        units="m s-1",
        sensor_type="adcp",
        long_name=f"{s0}ward_sea_water_velocity",
        # ancillary_variables = f'{s1}_QC',
        sdn_parameter_urn=f"SDN:P01::{s1}",
        sdn_parameter_name=(
            f"{s2}ward current velocity "
            "(Eulerian measurement) in the water body "
            "by moored  acoustic doppler current profiler "
            "(ADCP)"
        ),
        sdn_uom_urn="SDN:P06::UVAA",
        sdn_uom_name="Metres per second",
        legacy_GF3_code=f"SDN:GF3::{s3}",
    )


def _TNIHCE(s0: str) -> tp.Dict[str, str]:
    """skeleton for TNIHCE(-) attributes dictionnary"""
    return dict(
        units="counts",
        sensor_type="adcp",
        long_name=f"ADCP_echo_intensity_beam_{s0}",
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
        units="counts",
        sensor_type="adcp",
        long_name=f"ADCP_correlation_magnitude_beam_{s0}",
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
        units="percent",
        sensor_type="adcp",
        long_name=f"percent_good_beam_{s0}",  # This is not it.
        sdn_parameter_urn=f"SDN:P01::{s1}",
        sdn_parameter_name=(
            "Acceptable proportion of signal returns "
            "by moored acoustic doppler current profiler "
            f"(ADCP) beam {s0}"
        ),  # Same this is not it.
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


variables_attrs = dict(
    Conventions="CF-1.8",
    naming_authority=["CF", "SDN:P01::", "SDN:P06::", "SDN:GF3"],
    LCEWAP01=_L_AP01("east", "LCEWAP01", "East", "EWCT"),
    LCNSAP01=_L_AP01("north", "LCNSAP01", "North", "NWCT"),
    LRZAAP01=_L_AP01("up", "LRZAAP01", "Up", "VCSP"),
    LERRAP01=dict(
        units="m s-1",
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
    TNIHCE01=_TNIHCE("1"),
    TNIHCE02=_TNIHCE("2"),
    TNIHCE03=_TNIHCE("3"),
    TNIHCE04=_TNIHCE("4"),
    CMAGZZ01=_CMAGZZ("1"),
    CMAGZZ02=_CMAGZZ("2"),
    CMAGZZ03=_CMAGZZ("3"),
    CMAGZZ04=_CMAGZZ("4"),
    PCGDAP00=_PCGDAP("1", "PCGDAP00"),
    PCGDAP02=_PCGDAP("2", "PCGDAP02"),
    PCGDAP03=_PCGDAP("3", "PCGDAP03"),
    PCGDAP04=_PCGDAP("4", "PCGDAP04"),
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
        sensor_type="adcp",
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
        sensor_type="adcp",
        # long_name="", #  the long_name should be added later
        sdn_parameter_urn="SDN:P01::TEMPPR01",
        sdn_parameter_name="Temperature of the water body",
        sdn_uom_urn="SDN:P06::UPAA",
        sdn_uom_name="Celsius degree",
        legacy_GF3_code="SDN:GF3::te90",
    ),
    DISTTRAN=dict(
        units="m",
        sensor_type="adcp",
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
    PPSAADCP=dict(  # this also refers to depth vector, mesured by adcp
        standard_name="depth",
        positive="down",  # depth as standard_name implies positive "down"
        units="m",
        sensor_type="adcp",
        # long_name="instrument depth", # this is wrong
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
        sensor_type="adcp",
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
    ADEPZZ01=dict(
        standard_name="depth",  # depth as standard_name implies positive "down"
        positive="down",
        units="m",
        sensor_type="adcp",
        long_name="depth",
        sdn_parameter_urn="SDN:P01::ADEPZZ01",
        sdn_parameter_name=(
            "Depth (spatial coordinate) relative " "to water surface in the water body"
        ),
        Sdn_uom_urn="SDN:P06::ULAA",
        sdn_uom_name="Metres",
        legacy_GF3_code="SDN:GF3::DEPH",
    ),
)


if __name__ == "__main__":
    file_name = "BODC_attributes.json"
    make_json_file(file_name, variables_attrs)

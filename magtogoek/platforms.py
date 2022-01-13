"""
author: Jérôme Guay
date: Feb. 22, 2021

This script makes platform template
:TODO:
-:everything:
"""
from magtogoek.utils import dict2json


def make_platform_template(filename):
    dict2json(filename, platform_template())


def platform_template() -> dict:
    """FIXME"""
    return dict(__enter_a_platform_id_here__=_add_platform())


def _add_platform() -> dict:
    return dict(
        platform_name=None,
        platform_type=None,
        paltform_model=None,
        sounding=None,
        longitude=None,
        latitude=None,
        description=None,
        buoy_specs=_add_buoy_specs(),
        sensors=dict(__enter_a_sensor_ID_here=_add_sensors()),
    )


def _add_buoy_specs() -> dict:
    return dict(
        type=None,
        model=None,
        height=None,
        diameter=None,
        weight=None,
        description=None,
    )


def _add_sensors()->dict:
    return dict(
        sensor_type=None,
        sensor_depth=None,
        serial_number=None,
        manufacturer=None,
        model=None,
        firmware_version=None,
        chief_scientist=None,
        description=None,
        comments=None,
    )

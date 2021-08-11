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


def platform_template():
    """FIXME"""
    return dict(__enter_a_platform_id_here__=_add_platform())


def _add_platform():
    return dict(
        platform_name=None,
        platform_type=None,
        paltform_model=None,
        mooring_number=None,
        sounding=None,
        longitude=None,
        latitude=None,
        platform_specs=_add_platform_specs(),
        sensors=dict(__enter_a_sensor_ID_here=_add_sensors()),
    )


def _add_platform_specs():
    return dict(
        name=None,
        type=None,
        model=None,
        height=None,
        diameter=None,
        weight=None,
        description=None,
    )


def _add_sensors():
    return dict(
        sensor_type=None,
        sensor_depth=None,
        serial_number=None,
        manufacturer=None,
        model=None,
        firmware_version=None,
        chief_scientist=None,
        comments=None,
    )

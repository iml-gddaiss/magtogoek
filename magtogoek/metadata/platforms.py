"""
author: Jérôme Guay
date: Feb. 22, 2021

This script makes platform template
:TODO:
-:everything:
"""
from magtogoek.metadata.toolbox import dict2json


def make_platform_template(filename):
    dict2json(filename, platform_template())


def platform_template():
    """FIXME"""
    return dict(__Enter_a_platform_ID__=_add_platform())


def _add_platform():
    return dict(
        platform_name="",
        platform_type="",
        intruments=dict(__Enter_a_sensor_ID__=_add_sensors()),
    )


def _add_sensors():
    return dict(
        sensor_type="",
        sensor_depth="",
        serial_number="",
        manufacturer="",
        model="",
        firmware_version="",
        chief_scientist="",
        description="",
    )

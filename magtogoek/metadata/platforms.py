"""
author: Jérôme Guay
date: Feb. 22, 2021

This script makes platform template
:TODO:
-:everything:
"""
from toolbox import dict2json


def make_platform_template(filename):
    dict2json(filename, platform_template())


def platform_template():
    """FIXME"""
    return dict(
        platform_id="Required",
        platform_name="NA",
        platform_type="(buoy/mooring/vessel/drifter)",  # optionnal
        intruments=_sensors_tempate(),
    )


def _sensors_tempate():
    return dict(
        sensor_id="Requiered (str: sensor identifier)",
        sensor_type="Requred (str: match processing type)",
        sensor_depth="Required (numerical: int or float)",
        manufacturer="Optional",
        model="Optional",
        firmware_version="Optional",
        chief_scientist="Optional",
        description="Optional",
    )

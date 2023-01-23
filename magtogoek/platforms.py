"""
author: Jérôme Guay
date: Feb. 22, 2021

This script makes platform template
:TODO:
-:everything:
"""

from dataclasses import dataclass, fields
from magtogoek import SENSOR_TYPES, PLATFORM_TYPES
import magtogoek.logger as l
from magtogoek.utils import dict2json, json2dict

import xarray as xr



def make_platform_template(filename):
    dict2json(filename, platform_template())


def platform_template() -> dict:
    return dict(__enter_a_platform_id_here__=_add_platform())


def _add_platform() -> dict:
    return dict(
        platform_name=None,
        platform_type=None,
        platform_model=None,
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


def _add_sensors() -> dict:
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


@dataclass(unsafe_hash=True)
class PlatformMetadata:
    platform_id: str = None
    platform_name: str = None
    platform_type: str = None
    platform_model: str = None
    sounding: str = None
    longitude: str = None
    latitude: str = None
    description: str = None

    def __post_init__(self):
        if self.platform_type not in PLATFORM_TYPES:
            l.warning(f"Invalid platform_type `{self.platform_type}` in platform file for sensor_id `{self.platform_id}`")


@dataclass(unsafe_hash=True)
class BuoySpecifications:
    type: str = None
    model: str = None
    height: str = None
    diameter: str = None
    weight: str = None
    description: str = None


@dataclass(unsafe_hash=True)
class Sensor:
    sensor_id: str = None
    sensor_type: str = None
    sensor_depth: str = None
    serial_number: str = None
    manufacturer: str = None
    model: str = None
    firmware_version: str = None
    chief_scientist: str = None
    description: str = None
    comments: str = None

    def __post_init__(self):
        if self.sensor_type not in SENSOR_TYPES:
            l.warning(f"Invalid sensor_type `{self.sensor_type}` in platform file for sensor_id `{self.sensor_id}`")


@dataclass
class Platform:
    platform_metadata: PlatformMetadata
    buoy_specs: BuoySpecifications
    sensor: Sensor

    def add_to(self, dataset: xr.Dataset, force = False):

        if force is True:
            for key, value in self.platform_metadata.__dict__.items():
                dataset.attrs[key] = value
            for key, value in self.sensor.__dict__.items():
                dataset.attrs[key] = value

            if self.sensor.sensor_depth is not None:
                l.log(f"`sensor_depth` value ({self.sensor.sensor_depth}) was set by the user.")

        else:
            for key, value in self.platform_metadata.__dict__.items():
                if key in dataset.attrs:
                    if not dataset.attrs[key]:
                        dataset.attrs[key] = value
                else:
                    dataset.attrs[key] = value

            for key, value in self.sensor.__dict__.items():
                if key in dataset.attrs:
                    if not dataset.attrs[key]:
                        dataset.attrs[key] = value
                else:
                    dataset.attrs[key] = value

        dataset.attrs['sensor_comments'] = dataset.attrs.pop('comments')
        dataset.attrs["platform"] = dataset.attrs.pop("platform_name")

        for v in ['longitude', 'latitude']:
            if self.platform_metadata.__dict__[v]:  # COMON IN PLATFORM
                dataset.attrs[v] = self.platform_metadata.__dict__[v]


def _make_dataclass(data_class: dataclass, values: dict):
    """Return an object of the instance `data_class` filtering extra arguments in values.
    """
    field_names = set(f.name for f in fields(data_class))
    return data_class(**{k: v for k, v in values.items() if k in field_names})


def load_platform_metadata(platform_file: str, platform_id: str, sensor_id: str):
    json_dict = json2dict(platform_file)

    platform_metadata = None
    sensor = None
    buoy_specs = None

    if platform_id in json_dict:
        platform_metadata = _make_dataclass(PlatformMetadata, json_dict[platform_id])
        if 'buoy_specs' in json_dict[platform_id]:
            buoy_specs = _make_dataclass(BuoySpecifications, json_dict[platform_id]['buoy_specs'])
        if 'sensors' in json_dict[platform_id]:
            if sensor_id in json_dict[platform_id]["sensors"]:
                json_dict[platform_id]['adcp_id'] = sensor_id
                sensor = _make_dataclass(Sensor, json_dict[platform_id]["sensors"][sensor_id])

    platform_metadata = Platform(**{'platform_metadata': platform_metadata, 'buoy_specs': buoy_specs, 'sensor': sensor})

    return platform_metadata



if __name__ == "__main__":
    filename = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/iml_platforms.json"
    platform_id = "IML6_2017"
    sensor_id = "ADCP_01"

    pm = load_platform_metadata(filename, platform_id, sensor_id)

    ds = xr.Dataset()
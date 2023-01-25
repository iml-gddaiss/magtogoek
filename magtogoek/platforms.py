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
    return {**Platform().__dict__,
            **{
                'buoy_specs': _add_buoy_specs(),
                'sensors': dict(__enter_a_sensor_ID_here=_add_sensors()),
            }}


def _add_buoy_specs() -> dict:
    return BuoySpecifications().__dict__


def _add_sensors() -> dict:
    return Sensor().__dict__


def _make_dataclass(data_class: dataclass, kwargs: dict):
    """Return an object of the instance `data_class` filtering extra arguments in values.
    """
    field_names = set(f.name for f in fields(data_class))
    return data_class(**{k: v for k, v in kwargs.items() if k in field_names})


@dataclass
class Platform:
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
            l.warning(f"Invalid platform_type: `{self.platform_type}` in platform file: `{self.platform_id}`")


@dataclass
class BuoySpecifications:
    type: str = None
    model: str = None
    height: str = None
    diameter: str = None
    weight: str = None
    description: str = None


@dataclass
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
            l.warning(f"Invalid sensor_type: `{self.sensor_type}` in platform file for sensor_id: `{self.sensor_id}`")


@dataclass
class PlatformMetadata:
    platform: Platform
    buoy_specs: BuoySpecifications

    def add_sensor(self, sensor_id: str, kwargs: dict):
        self.__setattr__(sensor_id, _make_dataclass(Sensor, kwargs))

    def add_to_dataset(self, dataset: xr.Dataset, sensor_id: str, force: bool = False):
        """Add values stored in Platform to dataset attributes.

        Rename attributes:
            `platform_type`   -> `platform`
            `sensor` -> `sensor_comments`

        Parameters
        ----------
        dataset:
            dataset to add attributes to.
        force:
            If True, will overwrite existing value of the same key.
        """

        if force is True:
            for key, value in self.platform.__dict__.items():
                dataset.attrs[key] = value
            if sensor_id in self.__dict__:
                for key, value in self.__dict__[sensor_id].__dict__.items():
                    dataset.attrs[key] = value

                if self.__dict__[sensor_id].sensor_depth is not None:
                    l.log(f"`sensor_depth` value ({self.__dict__[sensor_id].sensor_depth}) was set by the user.")

        else:
            for key, value in self.platform.__dict__.items():
                if key in dataset.attrs:
                    if not dataset.attrs[key]:
                        dataset.attrs[key] = value
                else:
                    dataset.attrs[key] = value
            if sensor_id in self.__dict__:
                for key, value in self.__dict__[sensor_id].__dict__.items():
                    if key in dataset.attrs:
                        if not dataset.attrs[key]:
                            dataset.attrs[key] = value
                    else:
                        dataset.attrs[key] = value

        dataset.attrs['sensor_comments'] = dataset.attrs.pop('comments')
        dataset.attrs["platform"] = dataset.attrs.pop("platform_name")


def load_platform_metadata(platform_file: str, platform_id: str):

    json_dict = json2dict(platform_file)

    if platform_id in json_dict:
        platform = _make_dataclass(Platform, json_dict[platform_id])
        if 'buoy_specs' in json_dict[platform_id]:
            buoy_specs = _make_dataclass(BuoySpecifications, json_dict[platform_id]['buoy_specs'])
        else:
            buoy_specs = BuoySpecifications()

        platform_metadata = PlatformMetadata(platform, buoy_specs)

        for sensor_id in json_dict[platform_id]['sensors']:
            platform_metadata.add_sensor(sensor_id, json_dict[platform_id]["sensors"][sensor_id])

        return platform_metadata
    return None # fix me


def default_platform_metadata(platform_type: str, sensor_id: str, sensor_type: str):
    platform_metadata = PlatformMetadata(
        Platform(platform_type=platform_type),
        BuoySpecifications()
    )
    platform_metadata.add_sensor(sensor_id, {'sensor_id': sensor_id, 'sensor_type': sensor_type})
    return platform_metadata


if __name__ == "__main__":
    filename = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/iml_platforms.json"
    _platform_id = "IML6_2017"
    _sensor_id = "ADCP_01"

    pm = load_platform_metadata(filename, _platform_id)

    ds = xr.Dataset()

    pm.add_to_dataset(ds,'ADCP_01')


"""
author: Jérôme Guay
date: Feb. 22, 2021

This script makes platform template
:TODO:
-:everything:
"""
import json
import sys

from typing import *
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
                'instruments': dict(__enter_an_instrument_ID_here__=_add_instrument()),
            }}


def _add_buoy_specs() -> dict:
    return BuoySpecifications().__dict__


def _add_instrument() -> dict:
    instrument = InstrumentMetadata()
    instrument.sensors = dict(__generic_sensor_id__=_add_sensor())
    return instrument.__dict__


def _add_sensor() -> dict:
    sensor = SensorMetadata()
    sensor.calibration = _add_calibration()
    return sensor.__dict__


def _add_calibration() -> dict:
    return Calibration().__dict__


@dataclass
class Platform:
    platform_name: str = None
    platform_type: str = None
    platform_model: str = None
    sounding: str = None
    longitude: str = None
    latitude: str = None
    description: str = None

    def __post_init__(self):
        if self.platform_type not in PLATFORM_TYPES:
            l.warning(f"Invalid platform_type: `{self.platform_type}`.")


@dataclass
class BuoySpecifications:
    type: str = None
    model: str = None
    height: str = None
    diameter: str = None
    weight: str = None
    description: str = None


@dataclass
class Calibration:
    date: str = None
    number_of_coefficients: str = None
    coefficients: str = None
    calibration_equation: str = None
    calibration_units: str = None
    archiving_units: str = None
    conversion_factor: str = None
    comments: str = None


@dataclass
class SensorMetadata:
    #paramter: str = None # to map to a generic_variable ??? FIXME
    name: str = None
    code: str = None
    description: str = None
    comments: str = None
    calibration: Calibration = None


@dataclass
class InstrumentMetadata:
    sensor_type: str = None
    sensor_height: str = None
    sensor_depth: str = None
    serial_number: str = None
    manufacturer: str = None
    model: str = None
    firmware_version: str = None
    chief_scientist: str = None # FIXME why is this not in the platform section ???
    description: str = None
    comments: str = None
    sensors: Dict[str, SensorMetadata] = None

    def __post_init__(self):
        if self.sensor_type not in SENSOR_TYPES:
            l.warning(f"Invalid sensor_type in platform file instrument: `{self.sensor_type}`.")
        if self.sensors is None:
            self.sensors = {}


@dataclass
class PlatformMetadata:
    """Object used to store platform metadata"""
    platform: Platform
    buoy_specs: BuoySpecifications
    instruments: Dict[str, InstrumentMetadata] = None

    def __post_init__(self):
        self.instruments = {}

    def add_instrument(self, instrument_id: str, instrument_meta: dict):
        self.instruments[instrument_id] = _filter_for_dataclass(InstrumentMetadata, instrument_meta)

        if 'sensors' in instrument_meta:
            sensors_metadata = {}
            for sensor, sensor_metadata in instrument_meta['sensors'].items():
                sensors_metadata[sensor] = _filter_for_dataclass(SensorMetadata, sensor_metadata)
                if 'calibration' in sensor_metadata:
                    sensors_metadata[sensor].calibration = _filter_for_dataclass(Calibration, sensor_metadata['calibration'])
            self.instruments[instrument_id].sensors = sensors_metadata

    # FIXME THIS IS ONLY USE FOR VIKING BUOY (METEOCE) no need to be here
    # EACH PROCESS SHOULD HAVE A SPECIFIC WAY TO DO IT (I guess)
    # except for the platform metadata.
    # def add_to_dataset(self, dataset: xr.Dataset, instruments_id: List[str], force: bool = False):
    #     """Add values stored in Platform for instrument_id in `sensors_to_instruments_id_map` to dataset attributes.
    #
    #     The <instrument_id> is added as a prefix to each values key in the sensor dataclass.
    #
    #     Rename attributes:
    #         `platform_name`  -> `platform`
    #
    #     Parameters
    #     ----------
    #     dataset :
    #         dataset to add attributes to.
    #     instruments_id :
    #         List of instruments id metadata to add to the dataset.
    #     force :
    #         If True, it will overwrite the existing value of the same key.
    #     """
    #     for key, value in self.platform.__dict__.items():
    #         if key in dataset.attrs and not force:
    #             if not dataset.attrs[key]:
    #                 dataset.attrs[key] = value
    #         else:
    #             dataset.attrs[key] = value
    #
    #     for s_id in instruments_id:
    #         if s_id in self.instruments:
    #             for key, value in self.instruments[s_id].__dict__.items():
    #                 if not isinstance(value, dict):
    #                     attr_key = "_".join([s_id, key])
    #                     if attr_key in dataset.attrs and not force:
    #                         if not dataset.attrs[attr_key]:
    #                             dataset.attrs[attr_key] = value
    #                     else:
    #                         dataset.attrs[attr_key] = value
    #
    #     dataset.attrs["platform"] = dataset.attrs.pop("platform_name")


def load_platform_metadata(platform_file: str, platform_id: str) -> PlatformMetadata:
    """Load json platform file into a PlatformMetadata dataclass.

    Will exit on json error or if the platform_id is not found in the platform_file.

    Parameters
    ----------
    platform_file: path to platform json file.
    platform_id: key for the platform.

    Returns
    -------

    """
    try:
        json_dict = json2dict(platform_file)
    except json.JSONDecodeError as err:
        print(
            f"ERROR. Could not load platform file (json): {platform_file}. \n"
            f"Error: {err}.\n"
            f"Aborting !"
        )
        sys.exit()

    try:
        platform_metadata_dict = _filter_for_dataclass(Platform, json_dict[platform_id])

        if 'buoy_specs' in json_dict[platform_id]:
            buoy_specs = _filter_for_dataclass(BuoySpecifications, json_dict[platform_id]['buoy_specs'])
        else:
            buoy_specs = BuoySpecifications()

        platform_metadata = PlatformMetadata(platform_metadata_dict, buoy_specs)

        for instrument_id in json_dict[platform_id]['instruments']:
            platform_metadata.add_instrument(instrument_id, json_dict[platform_id]["instruments"][instrument_id])

        return platform_metadata

    except KeyError:
        print(
            f"ERROR. `platform_id`: { platform_id} not found platform file: {platform_file}.\n"
            f"Aborting !"
        )
        sys.exit()


def _filter_for_dataclass(data_class: dataclass, raw_json_dict: dict):
    """Return an object of the instance `data_class` filtering extra arguments in values.
    """
    field_names = set(f.name for f in fields(data_class))
    return data_class(**{k: v for k, v in raw_json_dict.items() if k in field_names})


def default_platform_metadata(platform_type: str, instrument_id: str, sensor_type: str):
    platform_metadata = PlatformMetadata(
        Platform(platform_type=platform_type),
        BuoySpecifications()
    )
    platform_metadata.add_instrument(instrument_id, {'instrument_id': instrument_id, 'sensor_type': sensor_type})
    return platform_metadata


if __name__ == "__main__":
    filename = "/home/jeromejguay/ImlSpace/Projects/magtogoek/tests/files/iml_platforms.json"
    _platform_id = "IML6_2017"
    _sensor_id = "ADCP_01"

    pm = load_platform_metadata(filename, _platform_id)

    ds = xr.Dataset()

    pm.add_to_dataset(ds, ['ADCP_01'])


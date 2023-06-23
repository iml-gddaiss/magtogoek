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
from dataclasses import dataclass
from magtogoek import SENSOR_TYPES, PLATFORM_TYPES, DEFAULT_PLATFORM_TYPE
import magtogoek.logger as l
from magtogoek.utils import dict2json, json2dict


def make_platform_template(filename):
    dict2json(filename, platform_template())


def platform_template() -> dict:
    return dict(__enter_a_platform_id_here__=_add_platform())


def _add_platform() -> dict:
    return {**{k: v for k, v in Platform().__dict__.items()},
            **{
                'buoy_specs': _add_buoy_specs(),
                'instruments': dict(__enter_an_instrument_ID_here__=_add_instrument()),
            }}


def _add_buoy_specs() -> dict:
    return {k: v for k, v in BuoySpecifications().__dict__.items()}


def _add_instrument() -> dict:
    instrument = InstrumentMetadata()
    instrument.sensors = dict(__generic_sensor_id__=_add_sensor())
    return {k: v for k, v in instrument.__dict__.items()}


def _add_sensor() -> dict:
    sensor = SensorMetadata()
    sensor.calibration = _add_calibration()
    return {k: v for k, v in sensor.__dict__.items()}


def _add_calibration() -> dict:
    return {k: v for k, v in Calibration().__dict__.items()}


@dataclass
class Platform:
    platform_type: str = DEFAULT_PLATFORM_TYPE
    platform_name: str = None
    platform_model: str = None
    sounding: str = None
    longitude: str = None
    latitude: str = None
    description: str = None
    chief_scientist: str = None

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key == "platform_type":
            if value not in PLATFORM_TYPES and value is not None:
                l.warning(f"Invalid platform_type: `{value}`.")


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
    chief_scientist: str = None
    description: str = None
    comments: str = None
    sensors: Dict[str, SensorMetadata] = None

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key == "sensor_type":
            if value not in SENSOR_TYPES and value is not None:
                l.warning(f"Invalid sensor_type in platform file instrument: `{value}`.")


@dataclass
class PlatformMetadata:
    """Object used to store platform metadata"""
    platform: Platform = Platform()
    buoy_specs: BuoySpecifications = BuoySpecifications()
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
        sys.exit()  # TODO this should not be here.

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
        sys.exit()  # TODO this should not be here.


def _filter_for_dataclass(data_class: dataclass, raw_json_dict: dict):
    """Return an object of the instance `data_class` filtering extra arguments in values.
    """
    #field_names = set(f.name for f in fields(data_class))
    field_names = data_class.__dataclass_fields__.keys()
    values_dict = {k: v for k, v in raw_json_dict.items() if k in field_names}
    return data_class(**values_dict)

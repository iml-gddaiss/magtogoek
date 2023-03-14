from pathlib import Path
from magtogoek.logger import Logger
import magtogoek.logger
from magtogoek.adcp import SENSOR_TYPES as ADCP_SENSOR_TYPES
from magtogoek.wps import SENSOR_TYPES as WPS_SENSOR_TYPES
from magtogoek.utils import json2dict

logger.set_level(0)

VERSION = "0.0.1"

TERMINAL_WIDTH = 80

PROCESSES = ['adcp', 'viking']

SENSOR_TYPES = ADCP_SENSOR_TYPES + WPS_SENSOR_TYPES

PLATFORM_TYPES = ["buoy", "mooring", "ship", "lowered"]



### QUALITY CONTROL ###

# Global impossible parameter values

IMPOSSIBLE_PARAMETERS_VALUES_FILE_PATH = "files/impossible_parameter_values.json"
IMPOSSIBLE_PARAMETERS_VALUES_FILE_PATH = (
    Path(__file__).resolve().parent.joinpath(IMPOSSIBLE_PARAMETERS_VALUES_FILE_PATH).resolve()
)

IMPOSSIBLE_PARAMETERS_VALUES = json2dict(IMPOSSIBLE_PARAMETERS_VALUES_FILE_PATH)
# TODO convert to proper units.
# TODO Make a loader

SPIKE_DETECTION_PARAMETERS_FILE_PATH = "files/spike_thresholds.json"
SPIKE_DETECTION_PARAMETERS_FILE_PATH = (
    Path(__file__).resolve().parent.joinpath(SPIKE_DETECTION_PARAMETERS_FILE_PATH).resolve()
)

SPIKE_DETECTION_PARAMETERS = json2dict(SPIKE_DETECTION_PARAMETERS_FILE_PATH)

# Flag attributes

FLAG_REFERENCE = "BODC SeaDataNet"
FLAG_VALUES = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
FLAG_MEANINGS = (
    "no_quality_control",
    "good_value",
    "probably_good_value",
    "probably_bad_value",
    "bad_value",
    "changed_value",
    "value_below_detection",
    "value_in_excess",
    "interpolated_value",
    "missing_value",
)

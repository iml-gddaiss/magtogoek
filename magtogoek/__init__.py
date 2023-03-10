from magtogoek.logger import Logger
import magtogoek.logger
from magtogoek.adcp import SENSOR_TYPES as ADCP_SENSOR_TYPES
from magtogoek.wps import SENSOR_TYPES as WPS_SENSOR_TYPES

logger.set_level(0)

VERSION = "0.0.1"

TERMINAL_WIDTH = 80

PROCESSES = ['adcp', 'viking']

SENSOR_TYPES = ADCP_SENSOR_TYPES + WPS_SENSOR_TYPES

PLATFORM_TYPES = ["buoy", "mooring", "ship", "lowered"]



### QUALITY CONTROL ###

# Global impossible parameter values

IMPLAUSIBLE_VEL_TRESHOLD = 15  # meter per second

MIN_TEMPERATURE = -2.5  # Celcius
MAX_TEMPERATURE = 35  # Celcius

MIN_SALINITY = 0  # PSU
MAX_SALINITY = 40  # PSU

MIN_PRESSURE = 0  # dbar
MAX_PRESSURE = 10000  # dbar (mariana trench pressure)

MIN_DISSOLVED_OXYGEN = 0  # umol/L and or 0 mL/L
MAX_DISSOLVED_OXYGEN = 491.26 # umol/L or 11  # mL/L

MIN_PH = 6
MAX_PH = 9.3


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

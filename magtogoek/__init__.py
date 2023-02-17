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



###  GLOBAL IMPOSSIBLE PARAMETER VALUES ###
# For Quality Control | Impossible Value #

IMPLAUSIBLE_VEL_TRESHOLD = 15  # meter per second

MIN_TEMPERATURE = -2.5  # Celcius
MAX_TEMPERATURE = 35  # Celcius

MIN_SALINITY = 0  # PSU
MAX_SALINITY = 40  # PSU

MIN_PRESSURE = 0  # dbar
MAX_PRESSURE = 10000  # dbar (mariana trench pressure)


MIN_DISSOLVED_OXYGEN = 0  # mL/L
MAX_DISSOLVED_OXYGEN = 11  # mL/L

MIN_PH = 6
MAX_PH = 9.3


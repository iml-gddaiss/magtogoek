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
import os
import platform
from pathlib import Path
import magtogoek.logger

from magtogoek.utils import resolve_relative_path
from magtogoek.adcp import SENSOR_TYPES as ADCP_SENSOR_TYPES
from magtogoek.wps import SENSOR_TYPES as WPS_SENSOR_TYPES

logger.set_level(0)

VERSION = "0.0.1"

TERMINAL_WIDTH = 80

PROCESSES = ['adcp', 'meteoce']

SENSOR_TYPES = ADCP_SENSOR_TYPES + WPS_SENSOR_TYPES

PLATFORM_TYPES = ["buoy", "mooring", "ship", "lowered"]


### MAGTOGOEK CONFIGURATION FILES PATH ###
DEFAULT_CONFIGURATION_PATH = resolve_relative_path("files/", __file__)

if platform.system() == 'Windows':
    LOCAL_CONFIGURATION_PATH = Path(os.getenv('LOCALAPPDATA') + '/magtogoek/')
else:
    LOCAL_CONFIGURATION_PATH = Path(os.getenv('HOME') + '/magtogoek/')

LOCAL_CONFIG_EXISTS = False
if Path(LOCAL_CONFIGURATION_PATH).is_dir():
    LOCAL_CONFIG_EXISTS = True
    if os.listdir(LOCAL_CONFIGURATION_PATH) == os.listdir(DEFAULT_CONFIGURATION_PATH):
        CONFIGURATION_PATH = LOCAL_CONFIGURATION_PATH
    else:
        print('\n\t!!! Warning. Local magtogoek configuration is missing some files. Reverting to default configurations. !!!\n')
else:
    CONFIGURATION_PATH = DEFAULT_CONFIGURATION_PATH

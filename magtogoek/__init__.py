import os
import platform
from pathlib import Path

from magtogoek.__version__ import VERSION
import magtogoek.logger as l
from magtogoek.utils import resolve_relative_path

from magtogoek.adcp import SENSOR_TYPES as ADCP_SENSOR_TYPES, GENERIC_PARAMETERS as ADCP_GENERIC_PARAMETERS
from magtogoek.wps import SENSOR_TYPES as WPS_SENSOR_TYPES
from magtogoek.meteoce import SENSOR_TYPES as METEOCE_SENSOR_TYPES, GENERIC_PARAMETERS as METEOCE_GENERIC_PARAMTERS

l.set_level(0)

REPOSITORY_ADDRESS = "https://github.com/iml-gddaiss/magtogoek"

TERMINAL_WIDTH = 80

PROCESSES = ['adcp', 'meteoce']

SENSOR_TYPES = ADCP_SENSOR_TYPES + WPS_SENSOR_TYPES + METEOCE_SENSOR_TYPES

GENERIC_PARAMETERS = list(
    dict.fromkeys(ADCP_GENERIC_PARAMETERS + METEOCE_GENERIC_PARAMTERS)
)


PLATFORM_TYPES = ["buoy", "mooring", "ship", "lowered"]
DEFAULT_PLATFORM_TYPE = "buoy"


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

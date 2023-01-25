import os
from magtogoek.config_handler import load_configfile
from magtogoek.adcp.process import process_adcp

CONFIG_FILENAME = "files/adcp_iml4_2017.ini"
OUTPUT_FILES = ["iml4_2017_sw.nc", "iml4_2017_sw.nc"]


def test_process_adcp():
    configuration, sensor_type = load_configfile(CONFIG_FILENAME)

    process_adcp(configuration, headless=False)

    for fn in OUTPUT_FILES:
        os.remove(fn)



import os
from pathlib import Path
from magtogoek.config_handler import load_configfile, cli_options_to_config
from magtogoek.adcp.process import process_adcp

CONFIG_FILENAME = "files/adcp_iml4_2017.ini"
PROCESS_OUTPUT_FILES = ["files/iml4_2017_sw.nc", "files/iml4_2017_sw.log"]

RAW_ADCP_FILE = "data/raw_adcp_data/iml6_2017_wh.000"
QUICK_OUTPUT_FILES = ["data/raw_adcp_data/iml6_2017_wh.nc"]


def test_process_adcp():
    configuration = load_configfile(CONFIG_FILENAME)

    process_adcp(configuration, drop_empty_attrs=False, headless=False)

    for fn in PROCESS_OUTPUT_FILES:
        os.remove(fn)


def test_quick_adcp():

    options = {"input_files": RAW_ADCP_FILE,
               "process": "adcp",
               "sonar": "wh", "no_fig": True,
               "bodc_name": True}
    configuration = cli_options_to_config('adcp', options, cwd=str(Path().cwd()))

    process_adcp(configuration, drop_empty_attrs=True, headless=False)

    for fn in QUICK_OUTPUT_FILES:
        os.remove(fn)



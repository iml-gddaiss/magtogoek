"""
author: Jérôme Guay
date: Feb. 22, 2021
"""
import configparser


def make_config_file(filename: str, sensor_type: str):
    """make empty config_files in local directory"""
    config = base_config()
    config["PROCESSING"]


def configparser2ini(config, filename):
    """make ini file"""
    with open(filename, "w") as configfile:
        config.write(configfile)


def base_config():
    """return base commands config"""
    config = configparser.ConfigParser(allow_no_value=True)
    config["PROCESSING"]
    config["DATA_FILES"] = {
        "input_file": "Required",
        "output_file": "Required",
    }
    config["PLATFORM"] = {"platform_file": "Required"}
    config["PROJECT"] = {
        "; none value will be omited": None,
        "project": "None",
        "sea_name": "None",
        "sea_code": "None",
    }
    config["CRUISE"] = {
        "; None value will be omited": None,
        "country_institue_code": "None",
        "cuirse_number": "None",
        "organization": "None",
        "; if not specified here, chief scientist is taken in the platform file": None,
        "chief_scientist": "None",
        "; date format: YYYY-MM-DDTHH:MM:SS FIXME ": None,
        "start_date": "None",
        "end_date": "None",
    }
    config["ADDITIONAL_GLOBAL_ATTRIBUTES"] = {
        "; Everything put here will be set as global attributes.": None
    }
    return config

"""
author: Jérôme Guay
date: Feb. 19, 2021

This script stores variables names that have datatype dependancy.
sensor_type dictionnary keys are the name of those dependancy ie: sensor_type = adcp.
The resulting dictionnary are exported in .json file which will be used to set attributes.
:Note:
-:sensor_type needs to be set before long_names.
:TODO:
-:everything
"""
import typing as tp
from toolbox import dict2json

sensors_type = dict(adcp=["TEMPR01", "SVELCV01", "PRESPR01", "ADEPZZ01"])

if __name__ == "__main__":
    file_name = "files/long_name.json"
    dict2json(file_name, sensors_type)

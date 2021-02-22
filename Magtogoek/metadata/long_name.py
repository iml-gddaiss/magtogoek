"""
author: Jérôme Guay
date: Feb. 19, 2021

This script stores long_name that have instruments or other sorts of dependancy.
long_name dictionnary keys are the name of those dependancy ie: sensor_type = adcp.
The resulting dictionnary are exported in .json file which will be used to set attributes.

TODO:
-everything
"""
import typing as tp
from toolbox import dict2json

long_name = dict()

if __name__ == "__main__":
    file_name = "files/long_name.json"
    dict2json(file_name, long_name)

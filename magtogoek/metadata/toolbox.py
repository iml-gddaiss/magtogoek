"""
author: Jérôme Guay
date: Feb. 19, 2021

Functions toolbox.

NOTE: move somewhere else ?
"""
import typing as tp
import json


def dict2json(file_name: str, dictionnary: tp.Dict, indent: int = 4) -> None:
    """Makes json file from dictionnary
    Parameters:
    -----------
    indent:
        argument is passed to json.dump(..., indent=indent)
    """
    with open(file_name, "w") as f:
        json.dump(dictionnary, f, indent=indent)


def json2dict(json_file: str):
    """Open json file as a dictionnary."""
    with open(json_file) as f:
        dictionary = json.load(f)
    return dictionary

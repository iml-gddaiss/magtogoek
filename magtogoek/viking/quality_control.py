"""
TODO
"""

from typing import *
import xarray as xr
from magtogoek import logger as l


def no_meteoce_quality_control(dataset: xr.Dataset):
    l.warning('NO QUALITY CONTROL AVAILABLE')
    return dataset


def meteoce_quality_control(dataset: xr.Dataset):
    l.warning('NO QUALITY CONTROL AVAILABLE')
    return dataset

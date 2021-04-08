"""
Script to process adcp data.

- Load
- Quality_Control
- MetaData
- Export -> .nc or .odf
"""
import typing as tp

import numpy as np
import pandas as pd
import xarray as xr
from magtogoek.utils import Logger, get_gps_bearing, vincenty

l = Logger(level=0)

from pathlib import Path

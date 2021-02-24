"""
author: Jérôme Guay
date: Feb. 22, 2021
"""

import xarray as xr
import numpy as np
from pycurrents.adcp.rdiraw import Multiread


def load_rdi_binary(
    files, adcptype, force_dw=False, force_up=False, min_depth=0, t_offset=0
):
    """
    Read Teledyne RDI binary ADCP data to xarray.
    Parameters
    ----------
    files : str or list of str
        File(s) to read in.
    adcptype : str
        Sensor type passed to pycurrents.Multiread. ('wh', 'os')
    force_dw : bool
        Process as downward looking ADCP.
    force_up : bool
        Process as upward looking ADCP.
    min_depth : float
        Require instrument depth be greater that this value in meters.
    Returns
    -------
    xarray.Dataset
        ADCP data.
    """

    data = Multiread(files, adcptype).read()

    dataset = xr.Dataset()

    return dataset


def init_dataset(depth, time):
    """FIXME"""
    size_depth = len(depth)
    size_time = len(time)
    dataset = xr.Dataset(
        data_vars={
            "u": (["Z", "T"], np.nan * np.ones((size_depth, size_time))),
            "v": (["Z", "T"], np.nan * np.ones((size_depth, size_time))),
            "w": (["Z", "T"], np.nan * np.ones((size_depth, size_time))),
            "e": (["Z", "T"], np.nan * np.ones((size_depth, size_time))),
            "lon": (["T"], np.nan * np.ones(size_time)),
            "lat": (["T"], np.nan * np.ones(size_time)),
            "temp": (["T"], np.nan * np.ones(size_time)),
            "depth": (["T"], np.nan * np.ones(size_time)),
            "roll_": (["T"], np.nan * np.ones(size_time)),
            "pitch": (["T"], np.nan * np.ones(size_time)),
            "heading": (["T"], np.nan * np.ones(size_time)),
            "uship": (["T"], np.nan * np.ones(size_time)),
            "vship": (["T"], np.nan * np.ones(size_time)),
            "u_bt": (["T"], np.nan * np.ones(size_time)),
            "v_bt": (["T"], np.nan * np.ones(size_time)),
            "w_bt": (["T"], np.nan * np.ones(size_time)),
            "amp": (["Z", "T"], np.nan * np.ones((size_depth, size_time))),
            "corr": (["Z", "T"], np.nan * np.ones((size_depth, size_time))),
            "pg": (["Z", "T"], np.nan * np.ones((size_depth, size_time))),
            "corr_bt": (["T"], np.nan * np.ones(size_time)),
            "pg_bt": (["T"], np.nan * np.ones(size_time)),
            "range_bt": (["T"], np.nan * np.ones(size_time)),
        },
        coords={"depth": (["Z"], depth), "time": (["T"], time)},
    )
    return dataset

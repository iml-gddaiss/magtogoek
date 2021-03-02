"""
author: Jérôme Guay
date: Feb. 22, 2021
based-on: https://github.com/jeanlucshaw/adcp2nc/.

This script contains functions to read adcp data
and to load them in xarray.Dataset.
CODAS Multiread class is used pycurrents package
is used to read RDI file formats.

Accepted files are:
-Teledyne RDI .000.(TODO .ENX, .ENS .LTA, etc.)
-Rowetch files: (seawatch TODO)

See Also
--------
   * pycurrents.adcp.rdiraw.Multiread

"""
import xarray as xr
import numpy as np
import typing as tp
from pycurrents.adcp.rdiraw import Multiread, rawfile


def read_rdi_binary(
    fnames: tp.Tuple[str, tp.List[str]], sonar: str, yearbase: int
) -> tp.Type[Multiread]:
    """Read Teledyne RDI binary ADCP data to xarray.

    Reads data with Multiread().read() and also with
    rawfile().read() to get the FixedLeader for all
    pings.

    Parameters
    ----------
    fnames :
        File(s) to read.
    sonar :
        sonar type passed to pycurrents.Multiread.
        ('nb', 'bb', 'wh', 'sv', 'pn', or 'os')
    yearbase :
        start year of the sampling.

    Returns
    -------
    data:
        ADCP data from Multiread.read() with the `FixedLeader` added

    Notes:
    ------
    Althought the fixed_leader is supposed to be
    fixed, there is occurence of change in the
    fixed_leader of some ping. A check up of some
    the fixed_leader parameters is done in the
    processing.
    """

    data = Multiread(fnames=fnames, sonar=sonar, yearbase=yearbase).read()

    # uses rawfile() to get the FixedLeader.
    if isinstance(fnames, list):
        fixed_leader = np.concatenate(
            [
                rawfile(fname=fname, sonar=sonar, yearbase=yearbase)
                .read()
                .raw.FixedLeader
                for fname in fnames
            ]
        )
    else:
        fixed_leader = (
            rawfile(fname=fnames, sonar=sonar, yearbase=yearbase).read().raw.FixedLeader
        )

    data["FixedLeader"] = fixed_leader

    return data


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


if __name__ == "__main__":
    fn_raw = (
        "/home/jeromejguay/ImlSpace/Projects/"
        + "pycurrents_ADCP_processing/"
        + "sample_data/a1_20050503_20050504_0221m.000"
    )

    data, fl = read_rdi_binary(fn_raw, "wh", 2018)

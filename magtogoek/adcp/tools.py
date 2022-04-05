"""
Set of functions and objects used for adcp processing
"""
import typing as tp
from datetime import datetime

import numpy as np
import xarray as xr
from nptyping import NDArray
from pandas import Timestamp, to_datetime
import warnings


def dday_to_datetime64(dday: np.ndarray, yearbase: int) -> tp.Tuple[NDArray, NDArray]:
    """Convert time recorded time to pandas time (np.datetime64[s]).

    Replace time coordinates with datetime64 in strftime='%Y-%m-%d %H:%M:%S'
    Add `time_string` variables to dataset (strftime='%Y-%m-%d %H:%M:%S')

    Parameters
    ----------
    yearbase:
    dday:

    """
    start_time = Timestamp(str(yearbase) + "-01-01")
    time = np.array(
        to_datetime(dday, unit="D", origin=start_time, utc=True).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        dtype="datetime64[s]",
    )
    time_string = time.astype(str)

    return time, time_string


def datetime_to_dday(
    datetimes: tp.List[tp.Type[datetime]], yearbase: int = None
) -> NDArray:
    """Convert sequence of datetime to an array of dday since yearbase

    If yearbase is none, default to the year of the first datetime.
    """
    yearbase = yearbase if yearbase else datetimes[0].year

    return (
        np.array([(t - datetime(yearbase, 1, 1)).total_seconds() for t in datetimes])
        * 1
        / (3600 * 24)
    )


def get_datetime_and_count(trim_arg: str):
    """Get datetime and count from trim_arg.

    If `trim_arg` is None, returns (None, None)
    If 'T' is a datetime or a count returns (Timestamp(trim_arg), None)
    Else returns (None, int(trim_arg))

    Returns:
    --------
    datetime:
        None or pandas.Timestamp
    count:
        None or int

    """

    if trim_arg:
        if "T" in trim_arg:
            return (Timestamp(trim_arg), None)
        else:
            return (None, int(trim_arg))
    else:
        return (None, None)


def regrid_dataset(dataset: xr.Dataset,
                   grid: tp.Union[str, list, np.ndarray],
                   method: str = 'interp',
                   dim: str = 'depth') -> xr.Dataset:
    """
    Regrid data to predefined depths.

    Parameters
    ----------
    dataset :
        Input data.
    grid :
        Path to a column text file or array-like of depths in meters.
    method :
        One of [`interp`, `bin`]. Regrid by bin-averaging or interpolation.
    dim :
        Name of the coordinate along which to regrid `dataset`.

    Returns
    -------
    regridded :
        The input data regridded on `grid` along `dim`.

    """
    # Read grid file
    if isinstance(grid, str):
        z = np.loadtxt(grid)
    elif isinstance(grid, (list, np.ndarray)):
        z = np.array(grid)
    else:
        raise ValueError('Grid must be path or array-like, not: %s' % type(grid))

    # Regrid by interpolation
    if method == 'interp':
        regridded = dataset.interp({dim: z})

    # Regrid by bin averaging
    elif method == 'bin':
        regridded = xr_bin(dataset, dim, z)

    # Error handling
    else:
        raise ValueError('Unrecognized regrid method: %s' % method)

    # Change data extent for the depth coordinate
    regridded[dim].attrs['data_min'] = z.min()
    regridded[dim].attrs['data_max'] = z.max()

    return regridded


def bin_centers_to_edges(centers: tp.Union[list, np.ndarray]) -> np.ndarray:
    """
    Get bin edges from bin centers.

    Bin centers can be irregularly spaced. Edges are halfway between
    one point and the next.

    Parameters
    ----------
    centers :
        Bin centers.

    Returns
    -------
    edges :
        Bin edges.

    """
    z = np.array(centers)
    dz = np.diff(centers)
    return np.r_[z[0]-dz[0]/2, z[1:]-dz/2, z[-1] + dz[-1]/2]


def bin_edges_to_centers(edges: tp.Union[list, np.ndarray]) -> np.ndarray:
    """
    Get bin centers from bin edges.

    Bin centers can be irregularly spaced. Edges are halfway between
    one point and the next.

    Parameters
    ----------
    edges : 1D array
        Bin edges.

    Returns
    -------
    centers :
        Bin centers.

    """
    edges = np.array(edges)
    return edges[:-1] + np.diff(edges) / 2


def xr_bin(dataset: tp.Union[xr.Dataset, xr.DataArray],
           dim: str,
           bins: np.ndarray,
           centers: bool = True) -> tp.Union[xr.Dataset, xr.DataArray]:
    """
    Bin dataset along `dim`.

    Convenience wrapper for the groupby_bins xarray method. Meant for
    simply binning xarray `dataset` to the values of dimension `dim`, and
    return values at bin centers (or edges) `bins`.

    Parameters
    ----------
    dataset :
        Dataset to operate on.
    dim :
        Name of dimension along which to bin.
    bins :
        Bin centers or edges if `centers` is False.
    centers :
        Parameter `bins` is the centers, otherwise it is the edges.

    Returns
    -------
    binned :
        Dataset binned at `binc` along `dim`.

    """
    # Bin type management
    if centers:
        edge = bin_centers_to_edges(bins)
        labels = bins
    else:
        edge = bins
        labels = bin_edges_to_centers(bins)

    # Skip for compatibility with DataArray
    if isinstance(dataset, xr.core.dataset.Dataset):
        # Save dimension orders for each variable
        dim_dict = dict()
        for key in dataset.keys():
            dim_dict[key] = dataset[key].dims

    # Avoids printing mean of empty slice warning
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=RuntimeWarning)

        # Bin reduction 
        output = (dataset.groupby_bins(dataset[dim], bins=edge, labels=labels)
                  .mean(dim=dim, keep_attrs=True)
                  .rename({dim+'_bins': dim}))

    # Skip for compatibility with DataArray
    if isinstance(dataset, xr.core.dataset.Dataset):
        # Restore dataset attributes
        output.attrs = dataset.attrs

        # Restore dimension order to each variable
        for key, dim_tuple in dim_dict.items():
            if dim not in dim_tuple:
                output[key] = dataset[key]
            else:
                output[key] = output[key].transpose(*dim_tuple)

    return output

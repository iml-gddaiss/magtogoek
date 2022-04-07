"""
This modules contains mathematical and scientific functions.
They are separated from utils.py due to longer import time.
"""
import typing as tp

import numpy as np
import xarray as xr
from nptyping import NDArray
from pygeodesy.ellipsoidalVincenty import LatLon
import warnings


def flag_data(dataset: xr.Dataset, var: str, flag_thres: int = 2, ancillary_variables: str = None):
    """

    Parameters
    ----------
    dataset :
        The variable `var` must be in the dataset along with `var+'_QC'`.
    var :
    ancillary_variables :
    flag_thres :

    Returns
    -------

    """
    if ancillary_variables is None:
        ancillary_variables = dataset[var].attrs["ancillary_variables"]

    return dataset[var].where(dataset[ancillary_variables].data <= flag_thres)


def round_up(x: float, scale: float=1):
    return np.ceil(np.asarray(x) * 1 / scale) * scale


def nans(shape: tp.Union[list, tuple, np.ndarray]) -> np.ndarray:
    """return array of nan of shape `shape`"""
    return np.full(shape, np.nan)


def polar_histo(dataset: xr.Dataset, x_vel: str, y_vel: str, r_max: float):
    u = flag_data(dataset, x_vel).data.flatten()
    v = flag_data(dataset, y_vel).data.flatten()
    ii = np.isfinite(u) & np.isfinite(v)

    azimut, radius = cartesian2northpolar(u[ii], v[ii])

    rN, aN = 30, 180
    rbins, abins = np.linspace(0, r_max, rN), np.linspace(0, 2 * np.pi, aN)

    return np.histogram2d(azimut, radius, bins=(abins, rbins))


def cartesian2northpolar(x, y):
    """Return the azimut (north clockwise)  and the radius from x, y vector."""
    return (np.arctan2(x, y) + 2 * np.pi) % (2 * np.pi), np.hypot(x, y)


def circular_distance(a1, a2, units="rad"):
    """
    Function circdist usage:
        d   =   circdist(a1,a2,units='rad')

    Returns to 'd' the distance between angles a1 and a2
    expected to be radians by default, or degrees if units
    is specified to 'deg'.
    Parameters
    ----------
    a1, a2 : float
        Input angle.
    units : str
        Units of input angles ('deg', 'rad')
    Returns
    -------
    float
        Angular distance between `a1` and `a2`.

    Notes
    -----
    Taken from jeanlucshaw adcp2nc: https://github.com/jeanlucshaw/adcp2nc/
    """
    if units == "deg":
        a1 = np.pi * a1 / 180
        a2 = np.pi * a2 / 180

    if np.isscalar(a1) and np.isscalar(a2):
        v1 = np.array([np.cos(a1), np.sin(a1)])
        v2 = np.array([np.cos(a2), np.sin(a2)])
        dot = np.dot(v1, v2)
    elif not np.isscalar(a1) and np.isscalar(a2):
        a2 = np.tile(a2, a1.size)
        v1 = np.array([np.cos(a1), np.sin(a1)]).T
        v2 = np.array([np.cos(a2), np.sin(a2)]).T
        dot = (v1 * v2).sum(-1)
    else:
        v1 = np.array([np.cos(a1), np.sin(a1)]).T
        v2 = np.array([np.cos(a2), np.sin(a2)]).T
        dot = (v1 * v2).sum(-1)

    res = np.arccos(np.clip(dot, -1.0, 1.0))

    if units == "deg":
        res = 180 * res / np.pi

    return res


def vincenty(p0: tp.Tuple[float, float], p1: tp.Tuple[float, float]) -> float:
    """Calculate the distance between 2 coordinates with pygeodesy.ellipsoidalVincenty.LatLon

    Great Circule Distance with Datum = WGS84

    Parameters
    ----------
    p0 :
       (longitude, latitude) of the first points in decimal degrees
    p1 :
       (longitude, latitude) of the second points in decimal degrees

    Returns
    -------
    distance :
        distance between the two points in meters.
    """

    return LatLon(p0[1], p0[0]).distanceTo(LatLon(p1[1], p1[0]))


def get_gps_bearing(p0: tp.Tuple[float, float], p1: tp.Tuple[float, float]) -> float:
    """Calculate the bearing between two coordinates with pygeodesy.ellipsoidalVincenty.LatLon

    Datum = WGS84

    Parameters
    ----------
    p0 :
       (longitude, latitude) of the first points in decimal degrees
    p1 :
       (longitude, latitude) of the second points in decimal degrees

    Returns
    -------
    bearing in degrees [0, 360]
    """

    return LatLon(p0[1], p0[0]).initialBearingTo(LatLon(p1[1], p1[0]))


def rotate_2d_vector(
    X: NDArray, Y: NDArray, angle: float
) -> tp.Tuple[NDArray, NDArray]:
    """Rotates the X and Y component of the velocities anti-clockwise.

    [X_r]  = [cos(angle), -sin(angle)][X]
    [Y_r]  = [sin(angle),  cos(angle)][Y]

    Parameters
    ----------
    X:
       Velocity components of velocities along X

    Y:
       Velocity components of velocities along Y

    angle:
        Angle of rotation in decimal degree

    Returns
    -------
    X_r :
        Rotated velocity components along X_r.
    Y_r :
        Rotated velocity components along Y_r.
    """

    angle_rad = np.deg2rad(angle)

    X_r = np.cos(angle_rad) * X - np.sin(angle_rad) * Y
    Y_r = np.sin(angle_rad) * X + np.cos(angle_rad) * Y

    return X_r, Y_r


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

    Note
    ----
    The `interp` method performs linear interpolation. The `bin` method
    performs averaging of input data strictly within the bin boundaries
    and with equal weights for all data inside each bin.
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
        regridded = _xr_bin(dataset, dim, z)

    # Error handling
    else:
        raise ValueError('Unrecognized regrid method: %s' % method)

    # Change data extent for the depth coordinate
    regridded[dim].attrs['data_min'] = z.min()
    regridded[dim].attrs['data_max'] = z.max()

    return regridded


def _bin_centers_to_edges(centers: tp.Union[list, np.ndarray]) -> np.ndarray:
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


def _bin_edges_to_centers(edges: tp.Union[list, np.ndarray]) -> np.ndarray:
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


def _xr_bin(dataset: tp.Union[xr.Dataset, xr.DataArray],
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
    print("Passing through _xr_bin")
    # Bin type management
    if centers:
        edge = _bin_centers_to_edges(bins)
        labels = bins
    else:
        edge = bins
        labels = _bin_edges_to_centers(bins)

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


def _isin_along_axis(array: tp.Union[np.ndarray, xr.DataArray],
                     elements: tp.Union[int, float, list, np.ndarray],
                     axis: int = 0) -> tp.Union[np.ndarray, xr.DataArray]:
    """
    Check if `elements` are in `array` along `axis`.

    Parameters
    ----------
    array :
        In which to look for elements (m by n by l by ...).
    elements :
        Elements to look for (k by 1).
    axis :
        Index of the dimension along which look for `elements` in `array`.

    Returns
    -------
    bool_array :
        True if element was found, False otherwise. Of same size as
        `array` except dimension `axis`. For example, if `axis = 1`
        `bool_array` is of size m by k by l by (...). Dimension `axis`
        `bool_array` represents if element was found in `array` along
        dimension `axis` for each element in `elements`.

    """
    # Compute result for ndarray
    _func = lambda a, elements: np.isin(elements, a)
    result = np.apply_along_axis(_func, axis, array, elements)

    # Form into DataArray if input is DataArray
    if isinstance(array, xr.DataArray):
        shape, dims = [], []
        for i_, (dim_size, dim_name) in enumerate(zip(array.shape, array.dims)):
            if i_ != axis:
                shape.append(dim_size)
                dims.append(dim_name)
        result = xr.DataArray(result.reshape(*shape), dims=dims)

    return result


def _new_flags_bin_regrid(flags: xr.DataArray,
                          bin_depths: np.ndarray,
                          dim: str = 'depth',
                          axis: int = 0) -> xr.DataArray:
    """
    Quality flag transfer function for bin average regridding.

    Parameters
    ----------
    flags :
        Flags prepared for regridding (5, 8, 9).
    bin_depths :
        Center of the regridding averaging bins (meters).
    dim :
        Name of the dimension along which the binning is done.
    axis :
        Index of the dimension along which the binning is done.

    Returns
    -------
    new_flags :
        Quality flags for the regridded data.

    """
    bin_edges = _bin_centers_to_edges(bin_depths)

    # Determine if bins contained 5 or 8 flags
    grouped = flags.groupby_bins(dim, bin_edges, labels=bin_depths)
    contains_8 = grouped.map(_isin_along_axis, args=(8, axis,))
    contains_5 = grouped.map(_isin_along_axis, args=(5, axis,))

    # Make new flag array
    new_flags = xr.where(contains_5, 5, 9)  # contains 5 or 8 -> 5, not -> 9
    new_flags = xr.where(contains_8, 8, new_flags)  # contains 8 -> 8

    return new_flags


def _new_flags_interp_regrid(dataset: xr.Dataset, variable: str) -> xr.DataArray:
    """
    Quality flag transfer function for interpolation regridding.

    Parameters
    ----------
    flags :
        Dataset being regridded.
    variable :
        Name of the variable for which flags are being transfered.

    Returns
    -------
    new_flags :
        Quality flags for the regridded data variable.

    """
    condition_null = dataset[f"{variable}"].isnull()
    condition_good = (dataset[f"{variable}_QC"] == 8) & ~condition_null
    condition_changed = (dataset[f"{variable}_QC"] == 5) & condition_null
    new_flags = dataset[f"{variable}_QC"].copy()
    new_flags.loc[:] = 9
    new_flags = xr.where(condition_changed, 5, new_flags)
    new_flags = xr.where(condition_good, 8, new_flags)

    return new_flags


def _prepare_flags_for_regrid(flags: xr.DataArray) -> xr.DataArray:
    """
    Format quality control flags for input to regridding transfer schemes.

    Parameters
    ----------
    flags :
        Quality control flags [0, 1, 2, 3, 4, 5, 9].

    Returns
    -------
    new_flags :
        Quality control flags [5, 8, 9].

    Notes
    -----
    The rationale for this transformation is that after interpolation or
    averaging missing values should remain flagged as `missing`, good values
    should be flagged as `interpolated` and questionable values should be
    flagged as `modified`. All flag values are therefore funneled into
    these three types before regridding to simplify the transfer algorithms.
    """
    new_flags = xr.where(flags < 9, 5, 9)
    new_flags = xr.where(flags < 3, 8, new_flags)
    return new_flags

"""
Basicaly all from jeanlucshaw.
"""
import datetime
import glob
import os
import warnings

import numpy as np
import pandas as pd
import xarray as xr
# from magtogoek.adcp.utils import *
from rti_python.Codecs.BinaryCodec import BinaryCodec
from rti_python.Ensemble.EnsembleData import *
from scipy.stats import circmean
from tqdm import tqdm

# Constants
DELIMITER = b"\x80" * 16


def load_rtb_binary(files):
    """
    Read Rowetech RTB binary ADCP data to xarray.

    Parameters
    ----------
    files : str or list of str
        File name or expression designating .ENS files, or list or file names.

    Returns
    -------
    xarray.Dataset
        ADCP data as organized by mxtoolbox.read.adcp.adcp_init .

    """

    # Make list of files to read
    if isinstance(files, str):
        adcp_files = glob.glob(files)
    else:
        adcp_files = files

    # Make xarray from file list
    if len(adcp_files) > 1:
        # xarray_datasets = [read_rtb_file(f) for f in adcp_files if f[-3:]=='ENS']
        xarray_datasets = [read_rtb_file(f) for f in adcp_files]
        ds = xr.concat(xarray_datasets, dim="time")

        # Find average depths by bin
        bins = np.arange(0, ds.z.max() + ds.bin_size, ds.bin_size)
        lbb = bins - 0.5 * ds.bin_size
        ubb = bins + 0.5 * ds.bin_size
        z_bins = np.array(
            [
                ds.z.where((ds.z < ub) & (ds.z > lb)).mean().values
                for lb, ub in zip(lbb, ubb)
            ]
        )
        z_bins = z_bins[np.isfinite(z_bins)]

        # Bin to these depths for uniformity
        ds = xr_bin(ds, "z", z_bins)
    else:
        ds = read_rtb_file(*adcp_files)

    return ds


def read_rtb_file(file_path):
    """
    Read data from one RTB .ENS file into xarray.

    Parameters
    ----------
    file_path : str
        File name and path.

    Returns
    -------
    xarray.Dataset
        As organized by mxtoolbox.read.adcp.adcp_init .

    """
    # Index the ensemble starts
    idx, enl, data = index_rtb_data(file_path)

    chunk = data[idx[0] : idx[1]]
    if BinaryCodec.verify_ens_data(chunk):
        ens = BinaryCodec.decode_data_sets(chunk)

    # Get coordinate sizes
    ens_count = len(idx)
    bin_count = ens.EnsembleData.NumBins
    bin_size = ens.AncillaryData.BinSize

    data = dict()

    # ---------- #
    # read_chunk #
    # ---------- #

    # Read and store ensembles
    with tqdm(
        total=len(idx) - 1, desc="Processing " + file_path, unit=" ensembles"
    ) as pbar:
        for ii in range(len(idx)):

            # Get data binary chunck for one ensemble
            chunk = data[idx[ii] : idx[ii] + enl[ii]]

            # Check that chunk looks ok
            if BinaryCodec.verify_ens_data(chunk):

                # Decode data variables
                ens = BinaryCodec.decode_data_sets(chunk)

                CORR = np.array(ens.Correlation.Correlation)
                AMP = np.array(ens.Amplitude.Amplitude)
                PG = np.array(ens.GoodEarth.GoodEarth)

                time[ii] = ens.EnsembleData.datetime()
                ds.u.values[:, ii] = np.array(ens.EarthVelocity.Velocities)[:, 0]
                ds.v.values[:, ii] = np.array(ens.EarthVelocity.Velocities)[:, 1]
                ds.w.values[:, ii] = np.array(ens.EarthVelocity.Velocities)[:, 2]
                ds.temp.values[ii] = ens.AncillaryData.WaterTemp
                ds.depth.values[ii] = ens.AncillaryData.TransducerDepth
                ds.heading.values[ii] = ens.AncillaryData.Heading
                ds.pitch.values[ii] = ens.AncillaryData.Pitch
                ds.roll_.values[ii] = ens.AncillaryData.Roll
                ds.corr.values[:, ii] = np.nanmean(CORR, axis=-1)
                ds.amp.values[:, ii] = np.nanmean(AMP, axis=-1)
                ds.pg.values[:, ii] = PG[:, 3]

                # Bottom track data
                if ens.IsBottomTrack:
                    ds.u_bt[ii] = np.array(ens.BottomTrack.EarthVelocity)[0]
                    ds.v_bt[ii] = np.array(ens.BottomTrack.EarthVelocity)[1]
                    ds.w_bt[ii] = np.array(ens.BottomTrack.EarthVelocity)[2]
                    ds.pg_bt[ii] = np.nanmean(ens.BottomTrack.BeamGood, axis=-1)
                    ds.corr_bt[ii] = np.nanmean(ens.BottomTrack.Correlation, axis=-1)
                    ds.range_bt[ii] = np.nanmean(ens.BottomTrack.Range, axis=-1)
            pbar.update(1)

    # --------------- #
    # Make a function #
    # --------------- #
    # Determine up/down configuration
    mean_roll = circmean(np.radians(data["roll"]))
    data["orientation"] = "up" if abs(mean_roll) < np.radians(30) else "down"

    # --------------- #
    # Make a function #
    # --------------- #
    # Determine bin depths
    data["dep"] = ens.AncillaryData.FirstBinRange + np.arange(
        0, bin_count * bin_size, bin_size
    )
    if data["orientation"] == "up":
        z = np.asarray(np.median(data["depth"]) - data["dep"]).round(2)
    else:
        z = np.asarray(np.median(data["depth"]) + data["dep"]).round(2)

    # Roll near zero means downwards (like RDI)
    roll_ = ds.roll_.values + 180
    roll_[roll_ > 180] -= 360
    ds["roll_"].values = roll_

    # Correlation between 0 and 255 (like RDI)
    ds["corr"].values *= 255

    # Set coordinates and attributes
    z_attrs, t_attrs = ds.z.attrs, ds.time.attrs
    ds = ds.assign_coords(z=z, time=time)
    ds["z"].attrs = z_attrs
    ds["time"].attrs = t_attrs

    # Get beam angle
    if ens.EnsembleData.SerialNumber[1] in "12345678DEFGbcdefghi":
        ds.attrs["beam_angle"] = 20
    elif ens.EnsembleData.SerialNumber[1] in "OPQRST":
        ds.attrs["beam_angle"] = 15
    elif ens.EnsembleData.SerialNumber[1] in "IJKLMNjklmnopqrstuvwxy":
        ds.attrs["beam_angle"] = 30
    elif ens.EnsembleData.SerialNumber[1] in "9ABCUVWXYZ":
        ds.attrs["beam_angle"] = 0
    else:
        raise ValueError("Could not determine beam angle.")

    # Manage coordinates and remaining attributes
    data["bin_size"] = bin_size
    data["instrument_serial"] = ens.EnsembleData.SerialNumber
    data["ping_frequency"] = ens.SystemSetup.WpSystemFreqHz

    return ds


def read_rtb_ensemble(file_path, N=0):
    """
    Read one ensemble from a RTB .ENS file.

    Parameters
    ----------
    file_path : str
        Name and path of the RTB file.
    N : int
        Index value of the ensemble to read.

    Returns
    -------
    rti_python.Ensemble.Ensemble
        Ensemble data object.

    """
    ensemble_starts, ensemble_lengths, data = index_rtb_data(file_path)

    chunk = data[ensemble_starts[N] : ensemble_starts[N] + ensemble_lengths[N]]
    if BinaryCodec.verify_ens_data(chunk):
        ens = BinaryCodec.decode_data_sets(chunk)
    else:
        ens = []

    return ens


def index_rtb_data(file_path):
    """
    Read binary as byte stream. Find ensemble locations and sizes.

    Parameters
    ----------
    file_path : str
        File path and name.

    Returns
    -------
    1D array
        Ensemble start index values.
    1D array
        Ensemble data lengths.
    1D array
        Data as byte stream.

    """
    # Open binary
    with open(file_path, "rb") as df:

        # Read data file
        data = df.read()
        ensemble_starts = []
        ensemble_lengths = []

        # Get payload size of first ensemble
        payloadsize = int.from_bytes(data[24:27], "little")

        # Get individual ensemble starts and lengths
        ii = 0
        while ii < len(data) - payloadsize - 32 - 4:
            if data[ii : ii + 16] == DELIMITER:
                ensemble_starts.append(ii)
                ensemble_lengths.append(payloadsize + 32 + 4)

                # Increment by payload size, plus header plus checksum
                ii += payloadsize + 32 + 4
            else:
                print("Data format bad")
                break

            # Get payload size of next ensemble
            payloadsize = int.from_bytes(data[ii + 24 : ii + 27], "little")

    return ensemble_starts, ensemble_lengths, data


def bine2center(bine):
    """
    Get bin centers from bin edges.

    Bin centers can be irregularly spaced. Edges are halfway between
    one point and the next.

    Parameters
    ----------
    bine : 1D array
        Bin edges.

    Returns
    -------
    1D array
        Bin centers.

    See Also
    --------

       * convert.binc2edge
    """
    return bine[:-1] + np.diff(bine) / 2


def binc2edge(z):
    """
    Get bin edges from bin centers.

    Bin centers can be irregularly spaced. Edges are halfway between
    one point and the next.

    Parameters
    ----------
    z : numpy.array, pandas.DatetimeIndex, pandas.Series
        Bin centers.

    Returns
    -------
    numpy.array, pandas.DatetimeIndex, pandas.Series
        Bin edges.

    See Also
    --------

       * convert.bine2center

    """
    if type(z) is pd.core.indexes.datetimes.DatetimeIndex:
        TIME = pd.Series(z)
        DT = TIME.diff()[1:].reset_index(drop=True)

        # Extend time vector
        TIME = TIME.append(TIME.take([-1])).reset_index(drop=True)

        # Make offset pandas series
        OS = pd.concat(
            (-0.5 * pd.Series(DT.take([0])), -0.5 * DT, 0.5 * pd.Series(DT.take([-1])))
        ).reset_index(drop=True)

        # Make bin edge vector
        EDGES = TIME + OS
    elif type(z) is pd.core.series.Series:
        DT = z.diff()[1:].reset_index(drop=True)

        # Extend time vector
        z = z.append(z.take([-1])).reset_index(drop=True)

        # Make offset pandas series
        OS = pd.concat(
            (-0.5 * pd.Series(DT.take([0])), -0.5 * DT, 0.5 * pd.Series(DT.take([-1])))
        ).reset_index(drop=True)

        # Make bin edge vector
        EDGES = z + OS
    else:
        dz = np.diff(z)
        EDGES = np.r_[z[0] - dz[0] / 2, z[1:] - dz / 2, z[-1] + dz[-1] / 2]

    return EDGES


def xr_bin(dataset, dim, bins, centers=True, func=np.nanmean):
    """
    Bin dataset along `dim`.

    Convenience wrapper for the groupby_bins xarray method. Meant for
    simply binning xarray `dataset` to the values of dimension `dim`, and
    return values at bin centers (or edges) `bins`.

    Parameters
    ----------
    dataset : xarray.Dataset or xarray.DataArray
        Dataset to operate on.
    dim: str
        Name of dimension along which to bin.
    bins: array_like
        Bin centers or edges if `centers` is False.
    centers: bool
        Parameter `bins` is the centers, otherwise it is the edges.
    func: Object
        Function used to reduce bin groups.

    Returns
    -------
    xarray.Dataset
        Dataset binned at `binc` along `dim`.
    """
    # Bin type management
    if centers:
        edge = binc2edge(bins)
        labels = bins
    else:
        edge = bins
        labels = bine2center(bins)

    # Skip for compatibility with DataArray
    if isinstance(dataset, xr.core.dataset.Dataset):
        # Save dimension orders for each variable
        dim_dict = dict()
        for key in dataset.keys():
            dim_dict[key] = dataset[key].dims

        # Save dataset attributes
        attributes = dataset.attrs

        # Save variable attributes
        var_attributes = dict()
        for v in dataset.data_vars:
            var_attributes[v] = dataset[v].attrs

        # Save variable attributes
        coord_attributes = dict()
        for c in dataset.coords:
            coord_attributes[c] = dataset[c].attrs

    # Avoids printing mean of empty slice warning
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)

        # Bin reduction
        output = (
            dataset.groupby_bins(dataset[dim], bins=edge, labels=labels)
            .reduce(func, dim=dim)
            .rename({dim + "_bins": dim})
        )

    # Skip for compatibility with DataArray
    if isinstance(dataset, xr.core.dataset.Dataset):
        # Restore dataset attributes
        output.attrs = attributes

        # Restore variable
        for v in output.data_vars:
            output[v].attrs = var_attributes[v]

        # Restore variable
        for c in output.coords:
            output[c].attrs = coord_attributes[c]

        # Restore dimension order to each variable
        for key, dim_tuple in dim_dict.items():
            if dim not in dim_tuple:
                output[key] = dataset[key]
            else:
                output[key] = output[key].transpose(*dim_tuple)

    return output


def xr_unique(dataset, dim):
    """
    Remove duplicates along dimension `dim`.

    Parameters
    ----------
    dataset : xarray.Dataset
        Dataset to operate on.
    dim : str
        Name of dimension to operate along.

    Returns
    -------
    xarray.Dataset
        Dataset with duplicates removed along `dim`.
    """
    _, index = np.unique(dataset[dim], return_index=True)
    return dataset.isel({dim: index})

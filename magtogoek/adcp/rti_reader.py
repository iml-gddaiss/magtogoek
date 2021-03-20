"""
Basicaly all from jeanlucshaw.
"""
import glob
# import os
import warnings
from datetime import datetime
from multiprocessing import Pool, cpu_count
from pathlib import Path

import numpy as np
import pandas as pds  # func not used
import xarray as xr  # func not used
# from magtogoek.adcp.utils import *
from rti_python.Codecs.BinaryCodec import BinaryCodec
from rti_python.Ensemble.EnsembleData import *
from scipy.constants import convert_temperature
from scipy.stats import circmean
from tqdm import tqdm


# Bunch Class was copied from pycurrents.adcp.rdiraw
class Bunch(dict):
    """
    A dictionary that also provides access via attributes.

    This version is specialized for this module; see also
    the version in pycurrents.system.misc, which has extra
    methods for handling parameter sets.
    """

    def __init__(self, *args, **kwargs):
        dict.__init__(self)
        self.__dict__ = self
        for arg in args:
            self.__dict__.update(arg)
        self.__dict__.update(kwargs)

    def __str__(self):
        ## fix the formatting later
        slist = ["Dictionary with access to the following as attributes:"]
        keystrings = [str(key) for key in self.keys()]
        slist.append("\n".join(keystrings))
        return "\n".join(slist) + "\n"

    def split(self, var):
        """
        Method specialized for splitting velocity etc. into
        separate arrays for each beam.
        """
        n = self[var].shape[-1]
        for i in range(n):
            self["%s%d" % (var, i + 1)] = self[var][..., i]


# --------------------CONSTANTS------------------------- #
DELIMITER = b"\x80" * 16
# ------------------------------------------------------ #


class RtiReader:
    def __init__(self, filenames):
        self.filenames = filenames

    def read(self):
        """FIXME"""
        if isinstance(self.filenames, str):
            p = Path(self.filenames)
            if p.is_file():
                self.adcp_files = [self.filenames]
            else:
                self.adcp_files = sorted(map(str, p.parent.glob(self.filenames.name)))
        else:
            self.adcp_files = self.filenames

        if len(self.adcp_files) > 1:
            bunch_list = []
            for f in adcp_files:
                bunch_list.append(self.read_rtb_file(f))
            return self.concatenate_files_bunch(bunch_list)

        else:
            return self.read_rtb_file(self.adcp_files[0])

    def read_rtb_file(self, filename):
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
        self.filename = filename
        # Index the ensemble starts
        self.idx, self.enl, self.data = self.index_rtb_data()

        # decode data from the first chunck
        chunk = self.data[self.idx[0] : self.idx[1]]
        if BinaryCodec.verify_ens_data(chunk):
            ens = BinaryCodec.decode_data_sets(chunk)

        # Get coordinate sizes
        pd = Bunch()

        pd.ens_count = len(self.idx)
        pd.nbin = ens.EnsembleData.NumBins
        pd.CellSize = ens.AncillaryData.BinSize
        pd.Bin1Dist = ens.AncillaryData.FirstBinRange
        pd.dep = pd.Bin1Dist + np.arange(0, pd.nbin * pd.CellSize, pd.CellSize)

        # pd.blank = None
        pd.NBeams = ens.EnsembleData.NumBeams
        # pd.pingtype = None
        pd.yearbase = ens.EnsembleData.Year
        pd.instrument_serial = ens.EnsembleData.SerialNumber

        pd.sysconfig = dict(
            angle=self._beam_angle(pd.instrument_serial),
            kHz=ens.SystemSetup.WpSystemFreqHz,
            convex=True,  # Rowetech adcp seems to be convex.
            up=None,
        )

        pd.trans = dict(coordsystem="beam")
        if ens.IsInstrumentVelocity:
            pd.trans["coordsytem"] = "xyz"
        if ens.IsEarthVelocity:
            pd.trans["coordsytem"] = "earth"

        ppd = self.read_chunks()
        for k in ppd:
            pd[k] = ppd[k]
            if k == "dday":
                pd[k] = np.array(
                    [(t - datetime(pd.yearbase, 1, 1)).total_seconds() for t in ppd[k]]
                )
                pd[k] *= 1 / (3600 * 24)

        # Determine up/down configuration
        mean_roll = circmean(np.radians(pd.roll))
        pd.sysconfig["up"] = True if abs(mean_roll) < np.radians(30) else False

        # Roll near zero means downwards (like RDI)
        pd.roll = pd.roll + 180
        pd.roll[pd.roll > 180] -= 360

        # Determine bin depths
        if pd.sysconfig["up"] is True:
            pd.dep = np.asarray(np.median(pd.XducerDepth) - pd.dep).round(2)
        else:
            pd.dep = np.asarray(np.median(pd.XducerDepth) + pd.dep).round(2)

        return pd

    def read_chunks(self):
        """FIXME"""
        # cutting the file in chunks and putting them in a list
        chunk_list = []
        for ii in range(len(self.idx)):
            chunk_list.append(
                (ii, self.data[self.idx[ii] : self.idx[ii] + self.enl[ii]])
            )
        # free some memory
        del self.data, self.idx, self.enl

        # spliting the reading workload on multiple cpu
        cpu = cpu_count() - 1
        print("Reading chunks")
        t0 = datetime.now()
        with Pool(cpu) as p:
            self.data_list = p.starmap(self.read_single_chunk, tqdm(chunk_list))
        print(
            len(chunk_list),
            "chunks read in",
            round((datetime.now() - t0).total_seconds(), 3),
            "s",
        )
        # sorting the data_list with the idx position then droping the indx.
        self.data_list.sort()
        self.data_list = [data for _, data in self.data_list]

        ppd = Bunch()
        for k in self.data_list[0]:
            chunks = [p[k] for p in self.data_list]
            ppd[k] = np.stack(chunks, axis=0)

            if ppd[k].ndim == 3:
                ppd.split(k)

        return ppd

    @staticmethod
    def read_single_chunk(ii, chunk):
        """
        Correlation are multipled by 255 to be between 0 and 255 (like RDI).
        Pressure is divided by 10. Pascal to decapascal(like RDI).
        """
        ppd = Bunch()
        # ii, chucnk = chunk

        # Get data binary chunck for one ensemble
        # chunk = data[idx[ii] : idx[ii] + enl[ii]]

        # Check that chunk looks ok
        if BinaryCodec.verify_ens_data(chunk):

            # Decode data variables
            ens = BinaryCodec.decode_data_sets(chunk)

            ppd.dday = ens.EnsembleData.datetime()  # transform to dday later

            ppd.cor = np.array(ens.Correlation.Correlation) * 255
            ppd.amp = np.array(ens.Amplitude.Amplitude)

            if ens.IsGoodEarth:
                ppd.pg = np.array(ens.GoodEarth.GoodEarth)

            if ens.IsGoodBeam:
                ppd.pg = np.array(ens.GoodBeam.GoodBeam)

            if ens.IsBeamVelocity:
                ppd.vel = np.array(ens.BeamVelocity.Velocities)

            if ens.IsInstrumentVelocity:
                ppd.vel = np.array(ens.InstrumentVelocity.Velocities)

            if ens.IsEarthVelocity:
                ppd.vel = np.array(ens.EarthVelocity.Velocities)

            if ens.IsAncillaryData:
                ppd.temperature = convert_temperature(
                    np.array(ens.AncillaryData.WaterTemp),
                    "fahrenheit",
                    "celsius",
                )
                ppd.salinity = np.array(ens.AncillaryData.Salinity)
                # pascal to decapascal

                ppd.pressure = np.array(ens.AncillaryData.Pressure) / 10
                ppd.XducerDepth = np.array(ens.AncillaryData.TransducerDepth)
                ppd.heading = np.array(ens.AncillaryData.Heading)
                ppd.pitch = np.array(ens.AncillaryData.Pitch)
                ppd.roll = np.array(ens.AncillaryData.Roll)

            if ens.IsBottomTrack:
                ppd.bt_vel = np.array(ens.BottomTrack.EarthVelocity)
                ppd.bt_pg = np.array(ens.BottomTrack.BeamGood)
                ppd.bt_cor = np.array(ens.BottomTrack.Correlation) * 255
                ppd.bt_range = np.array(ens.BottomTrack.Range)

        return ii, ppd

    def index_rtb_data(self):
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
        with open(self.filename, "rb") as df:

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

    def read_rtb_ensemble(self, N=0):
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
        ensemble_starts, ensemble_lengths, data = index_rtb_data(self.filename)

        chunk = data[ensemble_starts[N] : ensemble_starts[N] + ensemble_lengths[N]]
        if BinaryCodec.verify_ens_data(chunk):
            ens = BinaryCodec.decode_data_sets(chunk)
        else:
            ens = []

        return ens

    @staticmethod
    def _beam_angle(serial_number):
        """"""
        if serial_number[1] in "12345678DEFGbcdefghi":
            return 20
        elif serial_number[1] in "OPQRST":
            return (15,)
        elif serial_number[1] in "IJKLMNjklmnopqrstuvwxy":
            return 30
        elif "9ABCUVWXYZ":
            return 0
        else:
            print("Could not determine beam angle. FIXME")
            return None

    @staticmethod
    def concatenate_files_bunch(bunch_list):
        """"""
        pd = Bunch()
        b0 = bunch_list[0]
        pd.dep = b0.dep
        for k in b0:
            if k == "dep" or not isinstance(b0[k], np.ndarray):
                pd[k] = b0[k]
            chunks = [p[k] for p in bunch_list]
            pd[k] = np.concatenate(chunks)


##### FUNCTIONS BELOW ARE NOT YET USED #####
def bine2center(bin_edge):
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
    return bin_edge[:-1] + np.diff(bin_edge) / 2


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
    if type(z) is pds.core.indexes.datetimes.DatetimeIndex:
        TIME = pds.Series(z)
        DT = TIME.diff()[1:].reset_index(drop=True)

        # Extend time vector
        TIME = TIME.append(TIME.take([-1])).reset_index(drop=True)

        # Make offset pandas series
        OS = pds.concat(
            (
                -0.5 * pds.Series(DT.take([0])),
                -0.5 * DT,
                0.5 * pds.Series(DT.take([-1])),
            )
        ).reset_index(drop=True)

        # Make bin edge vector
        EDGES = TIME + OS
    elif type(z) is pds.core.series.Series:
        DT = z.diff()[1:].reset_index(drop=True)

        # Extend time vector
        z = z.append(z.take([-1])).reset_index(drop=True)

        # Make offset pandas series
        OS = pds.concat(
            (
                -0.5 * pds.Series(DT.take([0])),
                -0.5 * DT,
                0.5 * pds.Series(DT.take([-1])),
            )
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


if __name__ == "__main__":
    fn = "../../test/files/rowetech_seawatch.ens"
    data = RtiReader(fn).read()

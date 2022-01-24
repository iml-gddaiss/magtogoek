"""
RTI readers for Rowetech ENS files based on rti_tools by jeanlucshaw and rti_python.
Only tested on SeaWatch adcp.

Uses rti_python Ensemble and Codecs to read and decode data. The data are then loaded in a
`Bunch` object taken from pycurrents. This allows us to use to same loader for RDI and RTI data.

Usage:
data = RtiReader(filenames).read()
filenames: path/to/filename or list(path/to/filenames) or path/to/regex.

ens.EnsembleData.ActualPingCount # ping_per_ensemble.

"""
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Dict, List, Tuple, Union

import numpy as np
from scipy.interpolate import griddata
from scipy.stats import circmean
from tqdm import tqdm

from magtogoek.adcp.tools import datetime_to_dday
from magtogoek.utils import Logger, get_files_from_expression
from rti_python.Codecs.BinaryCodec import BinaryCodec
from rti_python.Ensemble.EnsembleData import *

DELIMITER = b"\x80" * 16  # RTB ensemble delimiter
BLOCK_SIZE = 4096  # Number of bytes read at a time
RTI_FILL_VALUE = 88.88800048828125
RDI_FILL_VALUE = -32768.0

l = Logger(level=0)


class FilesFormatError(Exception):
    pass


class BinDepMismatch(Exception):
    pass


class Bunch(dict):
    """
    A dictionary that also provides access via attributes.

    This version is specialized for this module; see also
    the version in pycurrents.system.misc, which has extra
    methods for handling parameter sets.

    Notes
    -----
       Bunch Class was copied from UHDAS pycurrents.adcp.rdiraw
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


class RtiReader:
    """Class to read RTI .ENS files.

    Parameters
    ----------
    filenames
        path/to/filename or list(path/to/filenames) or path/to/regex

    Methods
    -------
    check_files(self) :
        Prints info about the .ENS files; ensemble counts, number of bin, bin size, etc.

    read(start_index, stop_index) :
      Return a Bunch object with the read data.

        Parameters
        ----------
        start_index :
           Trim leading chunks by start_index.

        stop_index :
           Trim trailing chunks by stop_index.

        Returns
        -------
            data :
    """

    def __init__(self, filenames: Union[str, List[str]]):
        """
        Parameters
        ----------
        filenames :
            path/to/filename or list(path/to/filenames) or path/to/regex
        """
        self.filenames = get_files_from_expression(filenames)

        self.start_index = None
        self.stop_index = None

        self.files_ens_count = None
        self.files_start_stop_index = None
        self.ens_chunks = None
        self.current_file = None

        l.reset()

    def check_files(self):
        """Check files for ensemble count and bin depths."""

        self.get_files_ens_count()

        for filename in self.filenames:
            self.current_file = filename
            self.get_ens_chunks()
            first_ens = BinaryCodec.decode_data_sets(self.ens_chunks[0][1])
            last_time = BinaryCodec.decode_data_sets(self.ens_chunks[-1][1]).EnsembleData.datetime()

            print("-" * 40)
            print("File:", Path(filename).name)
            print("start time:", first_ens.EnsembleData.datetime())
            print("last time:", last_time)
            print("Number of ens:", len(self.ens_chunks))
            print("Number of beams:", first_ens.EnsembleData.NumBeams)
            print("Number of bins:", first_ens.EnsembleData.NumBins)
            print("Binsize:", first_ens.AncillaryData.BinSize)
            print("Distance first bin:", round(first_ens.AncillaryData.FirstBinRange, 3), "m")
            print("Beam angle:", _beam_angle(first_ens.EnsembleData.SerialNumber))
            print("Frequency:", int(first_ens.SystemSetup.WpSystemFreqHz), "hz")

    def read(self, start_index: int = None, stop_index: int = None) -> Bunch:
        """Return a Bunch object with the read data.

        Parameters
        -----------
        start_index :
           Trim leading chunks by start_index.

        stop_index :
           Trim trailing chunks by stop_index.

        Returns
        --------
            data
        TODO add inline comments
        """
        if start_index:
            if start_index < 0:
                raise ValueError("Start index must be positive integer.")
            else:
                self.start_index = int(start_index)

        if stop_index:
            if stop_index < 0:
                raise ValueError("Stop index must be positive integer.")
            else:
                self.stop_index = int(stop_index)

        self.get_files_ens_count()
        self.drop_empty_files()

        if len(self.filenames) == 0:
            raise ValueError("No file left to read. ")

        if self.start_index:
            if np.sum(self.files_ens_count) < self.start_index:
                raise ValueError("Start_index is greater than the number of ensemble.")
        if self.stop_index:
            if np.sum(self.files_ens_count) < self.stop_index:
                raise ValueError("Stop_index is greater than the number of ensemble")
        if self.start_index and self.stop_index:
            if np.sum(self.files_ens_count) < self.start_index + self.stop_index:
                raise ValueError(
                    "Start_index + stop_index is greater than the number of ensemble"
                )

        self.get_files_start_stop_index()

        files_bunch = []
        for filename in self.filenames:
            start, stop = self.files_start_stop_index[filename]
            self.current_file = filename
            self.get_ens_chunks()
            self.ens_chunks = self.ens_chunks[start:stop]
            files_bunch.append(self.read_file())

        data: Bunch = self.concatenate_files_bunch(files_bunch)

        return data

    def get_files_ens_count(self):
        """Read each files to find the number of ensemble in each file."""
        self.files_ens_count = []
        buff = bytes()
        self.ens_chunks = []

        for filename in self.filenames:
            count = 0
            with open(filename, "rb") as f:
                data = f.read(BLOCK_SIZE)
                while data:
                    buff += data
                    if DELIMITER in buff:
                        chunks = buff.split(DELIMITER)
                        buff = chunks.pop()
                        for chunk in chunks:
                            if BinaryCodec.verify_ens_data(DELIMITER + chunk):
                                count += 1
                    data = f.read(BLOCK_SIZE)
                # check the remaining bytes in buffer
                if BinaryCodec.verify_ens_data(DELIMITER + buff):
                    count += 1
            self.files_ens_count.append(count)

    def drop_empty_files(self):
        """Drop the files with 0 ensemble from self.filenames"""
        counts = np.array(self.files_ens_count)
        for filename in np.array(self.filenames)[counts == 0]:
            print(f"No data found in {filename}. File dropped")
        self.filenames = np.array(self.filenames)[counts != 0].tolist()
        self.files_ens_count = counts[counts != 0].tolist()

    def get_files_start_stop_index(self):
        """Get the start and stop index for the files

        Drops files if they have less counts thant index to trims.

        Takes into account multiple inputs files with varying
        ensemble counts.
        """
        counts = np.array(self.files_ens_count)
        cumsum = np.cumsum(counts)
        start_index, stop_index = None, None
        start_file, stop_file = None, None

        if self.start_index:
            # finds the first files with enough ens and the start index
            diff_start = cumsum - self.start_index
            start_index = counts[diff_start > 0][0] - diff_start[diff_start > 0][0]
            start_file = np.array(self.filenames)[diff_start > 0][0]
            # remove files with less leading ens than start_index
            self.filenames = np.array(self.filenames)[diff_start > 0].tolist()

        if self.stop_index:
            # finds the first files with enough ens and the start index
            diff_stop = cumsum - cumsum.max() + self.stop_index
            stop_index = counts[diff_stop > 0][0] - diff_stop[diff_stop > 0][0] + 1
            stop_file = np.array(self.filenames)[diff_stop > 0][0]
            # keep files with more trailing ens than stop_index
            self.filenames = np.array(self.filenames)[diff_stop < 0].tolist()
            self.filenames.append(stop_file)

        self.files_start_stop_index = dict()
        for filename in self.filenames:
            start, stop = None, None
            if filename == start_file:
                start = start_index
            if filename == stop_file:
                stop = stop_index
            self.files_start_stop_index[filename] = (start, stop)

    def get_ens_chunks(self):
        """Read the binary ens file and get ensemble (chunk/ping)

        makes attributes chunk_list: List[(chunk_idx, chunk)]

        """
        buff = bytes()
        ii = 0
        self.ens_chunks = []

        with open(self.current_file, "rb") as f:
            data = f.read(BLOCK_SIZE)
            while data:
                buff += data
                if DELIMITER in buff:
                    chunks = buff.split(DELIMITER)
                    buff = chunks.pop()
                    for chunk in chunks:
                        if BinaryCodec.verify_ens_data(DELIMITER + chunk):
                            self.ens_chunks.append((ii, DELIMITER + chunk))
                            ii += 1

                data = f.read(BLOCK_SIZE)

            # check the remaining bytes in buffer
            if BinaryCodec.verify_ens_data(DELIMITER + buff):
                self.ens_chunks.append((ii, DELIMITER + buff))
                ii += 1

    def read_file(self) -> Bunch:
        """Read data from one RTB .ENS file put them into a Bunch object

        Returns
        -------
        Bunch :
            bunch with the read data.

        """
        # Get `static` data from the first ensemble.
        ens = BinaryCodec.decode_data_sets(self.ens_chunks[0][1])

        # Get coordinate sizes
        ppd = Bunch()
        ppd.filename = Path(self.current_file).name
        ppd.ens_count = len(self.ens_chunks)

        ppd.nbin = ens.EnsembleData.NumBins
        ppd.NBeams = ens.EnsembleData.NumBeams
        ppd.yearbase = ens.EnsembleData.Year
        ppd.SerialNumber = ens.EnsembleData.SerialNumber
        ppd.NPings = ens.EnsembleData.ActualPingCount

        ppd.CellSize = ens.AncillaryData.BinSize
        ppd.Blank = round(ens.AncillaryData.FirstBinRange, 3)
        ppd.Bin1Dist = ppd.Blank + ppd.CellSize / 2

        ppd.dep = ppd.Bin1Dist + np.arange(0, ppd.nbin * ppd.CellSize, ppd.CellSize)

        ppd.pingtype = ens.SystemSetup.WpBroadband
        ppd.sysconfig = {'angle': _beam_angle(ppd.SerialNumber), 'kHz': ens.SystemSetup.WpSystemFreqHz / 1000,
                         'convex': True,
                         'up': False}
        ppd.FL = dict()
        ppd.FL["FWV"] = int(
            str(ens.EnsembleData.SysFirmwareMajor)
            + str(ens.EnsembleData.SysFirmwareMinor)
        )
        ppd.FL["FWR"] = ens.EnsembleData.SysFirmwareRevision
        ppd.FL["Pulse"] = ens.SystemSetup.WpLagLength * 100  # meters to centimeters

        if ens.IsBeamVelocity:
            ppd.trans = dict(coordsystem="beam")
        if ens.IsInstrumentVelocity:
            ppd.trans = dict(coordsystem="xyz")
        if ens.IsEarthVelocity:
            ppd.trans = dict(coordsystem="earth")

        # Read chunks and data of ens to ppd.
        ppd = Bunch(**ppd, **self.read_chunks())

        # Determine up/down configuration
        mean_roll = circmean(np.radians(ppd.roll))
        if abs(mean_roll) < np.radians(30):
            ppd.sysconfig["up"] = True

        # Determine bin depths
        if ppd.sysconfig["up"] is True:
            ppd.dep = np.asarray(np.median(ppd.XducerDepth) - ppd.dep).round(2)
        else:
            ppd.dep = np.asarray(np.median(ppd.XducerDepth) + ppd.dep).round(2)

        # Roll near zero means downwards (like RDI)
        ppd.roll = ppd.roll + 180
        ppd.roll[ppd.roll > 180] -= 360

        ppd.dday = datetime_to_dday(ppd["datetime"])

        if "gps_datetime" in ppd:
            ppd.rawnav = self.format_rawnav(ppd)

        return ppd

    def read_chunks(self) -> Bunch:
        """Read and decode chunks over multiple process

        Notes
        -----
        This could be somewhat faster if the tqdm was removed. It takes ~.25 additional seconds
        (~5s total) for ~4000 chunks. Exiting the processes to output progress could be time consuming
        for bigger files.
        """
        # spliting the reading workload on multiple cpu
        number_of_cpu = cpu_count() - 1

        print(f"Reading {self.current_file}")
        time0 = datetime.now()

        with Pool(number_of_cpu) as p:  # test
            decoded_chunks = p.starmap(self.decode_chunk, tqdm(self.ens_chunks))  # test

        time1 = datetime.now()
        print(
            len(self.ens_chunks),
            " chuncks read in",
            round((time1 - time0).total_seconds(), 3),
            "s",
        )

        # sorting the decoded_chunks with the index position then dropping the index.
        decoded_chunks.sort()
        decoded_chunks = [data for _, data in decoded_chunks]

        # Merging bunches into a single one.
        # Splitting beam data into new individual variable e.g. vel -> vel1,...,vel4
        ppd = Bunch()

        for k in decoded_chunks[0]:
            chunks = [p[k] for p in decoded_chunks]
            ppd[k] = np.stack(chunks, axis=0)

            if k == "vel":
                #  change de vel fill values to the one used by teledyne.
                ppd.vel[ppd.vel == RTI_FILL_VALUE] = RDI_FILL_VALUE

            if ppd[k].ndim == 3:
                ppd.split(k)
        if "bt_vel" in ppd:
            #  change de vel fill values to the one used by teledyne.
            ppd.bt_vel[ppd.bt_vel == RTI_FILL_VALUE] = RDI_FILL_VALUE

        return ppd

    @staticmethod
    def decode_chunk(ii: int, chunk: str) -> Tuple[int, Bunch]:
        """Decode single chunk of data.

        Parameters
        ----------
        ii :
            Index of the chunk in the file. It is passed one with the Bunch
        chunk :
            chunk of binary data containing one ensemble.

        Notes
        -----
        Correlation are multiplied by 255 to be between 0 and 255 (like RDI).
        Pressure is divided by 10. Pascal to decapascal(like RDI).
        """
        ppd = Bunch()

        ens = BinaryCodec.decode_data_sets(chunk)

        if ens.IsEnsembleData:
            ppd.datetime = np.array(ens.EnsembleData.datetime())

        if ens.IsCorrelation:
            ppd.cor = np.array(ens.Correlation.Correlation) * 255

        if ens.IsAmplitude:
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
            ppd.temperature = ens.AncillaryData.WaterTemp
            ppd.salinity = np.array(ens.AncillaryData.Salinity)
            pressure = np.array(ens.AncillaryData.Pressure) / 10  # pascal to decapascal
            ppd.VL = np.array(pressure, {"names": ["Pressure"], "formats": [np.float]})
            ppd.XducerDepth = np.array(ens.AncillaryData.TransducerDepth)
            ppd.heading = np.array(ens.AncillaryData.Heading)
            ppd.pitch = np.array(ens.AncillaryData.Pitch)
            ppd.roll = np.array(ens.AncillaryData.Roll)

        if ens.IsBottomTrack:
            if ens.IsInstrumentVelocity:
                ppd.bt_vel = np.array(ens.BottomTrack.InstrumentVelocity)
            if ens.IsEarthVelocity:
                ppd.bt_vel = np.array(ens.BottomTrack.EarthVelocity)
            ppd.bt_pg = np.array(ens.BottomTrack.BeamGood)
            ppd.bt_cor = np.array(ens.BottomTrack.Correlation) * 255
            ppd.bt_depth = np.array(ens.BottomTrack.Range)

        if ens.IsNmeaData:
            ppd.longitude = np.array(ens.NmeaData.longitude)
            ppd.latitude = np.array(ens.NmeaData.latitude)
            ppd.gps_datetime = np.array(ens.NmeaData.datetime)

        return ii, ppd

    @staticmethod
    def format_rawnav(data: Bunch) -> Dict:
        """Format rawnav to pycurent rawnav.

        Interpolates longitude and latitude on adcp dday.
        """

        gps_dday = datetime_to_dday(data.gsp_datetime)

        rawnav = dict(
            Lon1_BAM4=griddata(gps_dday, data.longitude, data.dday) / (180.0 / 2 ** 31),
            Lat1_BAM4=griddata(gps_dday, data.latitude, data.dday) / (180.0 / 2 ** 31),
        )
        return rawnav

    def concatenate_files_bunch(self, bunches: List[Bunch]) -> Bunch:
        """Concatenante the file bunches.

        Uses the first file bunch data for static values ( e.g. dep,
        orientation, frequency, beam angle, etc)

        Parameters
        ----------
        bunches :
            List of the files bunches to concatenate.
        Returns
        --------
        ppd :
            Bunch fo the concatenate files.
        Raise
        -----
        DepLengthMismatch: (check_mismatch_depth())
            Bin depth vector lenght mismatch.
            Lenght, thus values, of the dep vector can change through files.
            In that case, files need the be processed individually.

        """
        self.check_mismatch_dep(bunches)

        ppd = Bunch()
        b0: Bunch = bunches[0]
        ppd.dep = b0.dep

        for k in b0:
            if k == "dep" or not isinstance(b0[k], np.ndarray):
                ppd[k] = b0[k]
            else:
                chunks = [p[k] for p in bunches]
                ppd[k] = np.concatenate(chunks)

        return ppd

    @staticmethod
    def check_mismatch_dep(bunches: List[Bunch]):
        """Look for mismatch in bin depth.

        Parameters
        ----------
        bunches :
            List of the files bunches to concatenante.

        Raises
        ------
        DepLengthMismatch : (check_mismatch_depth())
            Bin depth vector lenght mismatch.
            Lenght, thus values, of the dep vector can change through files.
            In that case, files need the be processed individually.

        """
        filenames = [b.filename for b in bunches]
        deps = [len(b.dep) for b in bunches]
        if np.diff(deps).any() != 0:
            msg = "\n".join([f"{f} has {d} bin" for f, d in zip(filenames, deps)])
            raise BinDepMismatch("\n" + msg)

        bin1dists = [b.Bin1Dist for b in bunches]
        l.log(
            f"First bin distance was taken from {filenames[0]}. For each files, first bin distances were : "
        )
        for d, f in zip(bin1dists, filenames):
            l.log(f"  {f} : {np.round(d, 3)} meters")


def _beam_angle(serial_number):
    """Get the beam angle from the serial number"""
    if serial_number[1] in "12345678DEFGbcdefghi":
        return 20
    elif serial_number[1] in "OPQRST":
        return 15
    elif serial_number[1] in "IJKLMNjklmnopqrstuvwxy":
        return 30
    elif serial_number[1] in "9ABCUVWXYZ":
        return 0
    print("Could not determine beam angle.")
    return None

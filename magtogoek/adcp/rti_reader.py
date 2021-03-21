"""
Basicaly all from jeanlucshaw.
"""

import warnings
from datetime import datetime
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Dict, List, Tuple, Type

import numpy as np
import pandas as pd  # func not used
import xarray as xr  # func not used
from rti_python.Codecs.BinaryCodec import BinaryCodec
from rti_python.Ensemble.EnsembleData import *
from scipy.constants import convert_temperature
from scipy.stats import circmean
from tqdm import tqdm


# Bunch Class was copied from UHDAS pycurrents.adcp.rdiraw
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
BLOCK_SIZE = 4096
# ------------------------------------------------------ #


class RtiReader:
    def __init__(self, filenames: Tuple[str, List]):
        """
        Parameters
        ----------
        filenames
            path/to/filename or list(path/to/filenames) or path/to/regex
        """
        # NOT TESTED #
        self.filenames = filenames

        # looks for regex and transform to list.
        if isinstance(self.filenames, str):
            p = Path(self.filenames)
            if p.is_file():
                self.filenames = [self.filenames]
            else:
                self.filenames = sorted(map(str, p.parent.glob(p.name)))
                if len(self.filenames) == 0:
                    raise FileNotFoundError(
                        f"Expression `{p}` does not match any files."
                    )

    def read(self):
        """Call read_rt_file.
        return a Bunch object with the read data."""
        bunch_list = []
        for filename in self.filenames:
            bunch_list.append(self.read_file(filename))

        data = self.concatenate_files_bunch(bunch_list)
        data["dday"] = datetimes2dday(data["datetime"])
        # ["rawnav"]["Lon1_BAM4"] * 180.0 / 2 ** 31
        # TODO interp lon, lat and convert #
        # adds fill values for velocities -32768.0

        return data

    def read_file(self, filename: str) -> Type[Bunch]:
        """Read data from one RTB .ENS file put them into a Bunch object

        Parameters
        ----------
        filename
            path/to/filename

        Returns
        -------
        Bunch:
            bunch with the read data.

        """
        # error with ENS from IML4
        # read the binary data
        with open(filename, "rb") as df:
            self.ens_data = df.read()
        self.ens_index, self.ens_lenght = self.index_ens_data()

        first_chunk = self.ens_data[
            self.ens_index[0] : self.ens_index[0] + self.ens_lenght[0]
        ]
        if BinaryCodec.verify_ens_data(first_chunk):
            ens = BinaryCodec.decode_data_sets(first_chunk)

        # Get coordinate sizes
        ppd = Bunch()
        ppd.filename = filename
        ppd.ens_count = len(self.ens_index)
        ppd.nbin = ens.EnsembleData.NumBins
        ppd.CellSize = ens.AncillaryData.BinSize
        ppd.Bin1Dist = ens.AncillaryData.FirstBinRange
        ppd.dep = ppd.Bin1Dist + np.arange(0, ppd.nbin * ppd.CellSize, ppd.CellSize)

        # ppd.blank = None
        ppd.NBeams = ens.EnsembleData.NumBeams
        # ppd.pingtype = None
        ppd.yearbase = ens.EnsembleData.Year
        ppd.instrument_serial = ens.EnsembleData.SerialNumber

        ppd.sysconfig = dict(
            angle=self._beam_angle(ppd.instrument_serial),
            kHz=ens.SystemSetup.WpSystemFreqHz,
            convex=True,  # Rowetech adcp seems to be convex.
            up=None,
        )

        ppd.trans = dict(coordsystem="beam")
        if ens.IsInstrumentVelocity:
            ppd.trans["coordsytem"] = "xyz"
        if ens.IsEarthVelocity:
            ppd.trans["coordsytem"] = "earth"

        # reading all the chucnks.
        ppd = Bunch(**ppd, **self.read_chunks())

        # Determine up/down configuration
        mean_roll = circmean(np.radians(ppd.roll))
        ppd.sysconfig["up"] = True if abs(mean_roll) < np.radians(30) else False

        # Roll near zero means downwards (like RDI)
        ppd.roll = ppd.roll + 180
        ppd.roll[ppd.roll > 180] -= 360

        # Determine bin depths
        if ppd.sysconfig["up"] is True:
            ppd.dep = np.asarray(np.median(ppd.XducerDepth) - ppd.dep).round(2)
        else:
            ppd.dep = np.asarray(np.median(ppd.XducerDepth) + ppd.dep).round(2)

        return ppd

    def read_chunks(self):
        """Read the chunks in multple process
        Notes:
        ------
        This could be somewhat faster if the tqdm was removed. It takes ~.25 additional sec
        (~5s total) 4000 chunks. Exiting the process to ouput progress could time consuming
        for bigger files.
        """
        # cutting the file in chunks and putting them in a list
        chunk_list = []
        for ii in range(len(self.ens_index)):
            chunk_list.append(
                (
                    ii,
                    self.ens_data[
                        self.ens_index[ii] : self.ens_index[ii] + self.ens_lenght[ii]
                    ],
                )
            )
        # free some memory
        del self.ens_data, self.ens_index, self.ens_lenght

        # spliting the reading workload on multiple cpu
        number_of_cpu = cpu_count() - 1

        print("Reading chunks")
        time0 = datetime.now()

        with Pool(number_of_cpu) as p:  # test
            self.data_list = p.starmap(self.decode_chunk, tqdm(chunk_list))  # test

        time1 = datetime.now()
        print(
            len(chunk_list),
            " chuncks read in",
            round((time1 - time0).total_seconds(), 3),
            "s",
        )

        # sorting the data_list with the index position then droping the indx.
        self.data_list.sort()
        self.data_list = [data for _, data in self.data_list]

        # Merging bunches into a single one.
        # Splitting beam data into new individual variable e.g. vel -> vel1,...,vel4
        ppd = Bunch()
        for k in self.data_list[0]:
            chunks = [p[k] for p in self.data_list]
            ppd[k] = np.stack(chunks, axis=0)

            if ppd[k].ndim == 3:
                ppd.split(k)

        return ppd

    @staticmethod
    def decode_chunk(ii: int, chunk: str):
        """Read single chunk of data.

        Parameters:
        -----------
        ii:
            Index of the chunk in the file. It is passed one with the Bunch
        Correlation are multipled by 255 to be between 0 and 255 (like RDI).
        Pressure is divided by 10. Pascal to decapascal(like RDI).
        """
        ppd = Bunch()

        # Check that chunk looks ok
        if BinaryCodec.verify_ens_data(chunk):

            # Decode data variables
            ens = BinaryCodec.decode_data_sets(chunk)

            ppd.datetime = np.array(ens.EnsembleData.datetime())

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

            if ens.IsNmeaData:
                ppd.longitude = np.array(ens.NmeaData.longitude)
                ppd.latitude = np.array(ens.NmeaData.latitude)
                ppd.gps_datetime = np.array(ens.NmeaData.datetime)

        return ii, ppd

    def index_ens_data(self):
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

        ensemble_starts = []
        ensemble_lengths = []

        # Get payload size of first ensemble
        payloadsize = int.from_bytes(self.ens_data[24:27], "little")

        # Get individual ensemble starts and lengths
        ii = 0
        while ii < len(self.ens_data) - payloadsize - 32 - 4:
            if self.ens_data[ii : ii + 16] == DELIMITER:
                ensemble_starts.append(ii)
                ensemble_lengths.append(payloadsize + 32 + 4)

                # Increment by payload size, plus header plus checksum
                ii += payloadsize + 32 + 4
            else:
                print("Data format bad")
                break

            # Get payload size of next ensemble
            payloadsize = int.from_bytes(self.ens_data[ii + 24 : ii + 27], "little")

        return ensemble_starts, ensemble_lengths

    def get_chunks(self, ens_file_path):
        #### FIXME

        # Get the total file size to keep track of total bytes read and show progress
        file_size = os.path.getsize(ens_file_path)  # NOTE use path
        bytes_read = 0

        # Create a buffer
        buff = bytes()

        with open(ens_file_path, "rb") as f:

            # Read in the file
            # for chunk in iter(lambda: f.read(4096), b''):
            #    self.adcp_codec.add(chunk)

            data = f.read(BLOCK_SIZE)  # Read in data

            # Keep track of bytes read
            bytes_read += BLOCK_SIZE
            self.file_progress(bytes_read, file_size, ens_file_path)

            while data:  # Verify data was found
                buff += data  # Accumulate the buffer
                if DELIMITER in buff:  # Check for the delimiter
                    chunks = buff.split(
                        DELIMITER
                    )  # If delimiter found, split to get the remaining buffer data
                    buff = chunks.pop()  # Put the remaining data back in the buffer

                    for chunk in chunks:  # Take out the ens data
                        self.process_playback_ens(
                            DELIMITER + chunk
                        )  # Process the binary ensemble data

                data = f.read(BLOCK_SIZE)  # Read the next batch of data

                # Keep track of bytes read
                bytes_read += BLOCK_SIZE
                # self.file_progress(bytes_read, file_size, ens_file_path)
                self.file_progress(BLOCK_SIZE, file_size, ens_file_path)

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
            print("Could not determine beam angle.")
            return None

    @staticmethod
    def concatenate_files_bunch(bunches):
        """"""
        pd = Bunch()
        b0 = bunches[0]
        pd.dep = b0.dep
        for bunch in bunches:
            dep_diff = (bunch.dep - b0.dep).mean()
            if dep_diff != 0:
                print(
                    f"There is {dep_diff} m difference between the first file {b0.filename} and {bunch.filename} bin depths."
                )
        for k in b0:
            if k == "dep" or not isinstance(b0[k], np.ndarray):
                pd[k] = b0[k]
            else:
                chunks = [p[k] for p in bunches]
                pd[k] = np.concatenate(chunks)

        return pd


def datetimes2dday(datetimes: List[Type[datetime]], yearbase: int = None):
    """Convert sequence of datetime to an array of dday since yearbase

    If yearbase is none, default to the year of the first datetime.
    """
    yearbase = yearbase if yearbase else datetimes[0].year

    return (
        np.array([(t - datetime(yearbase, 1, 1)).total_seconds() for t in datetimes])
        * 1
        / (3600 * 24)
    )


if __name__ == "__main__":
    #    fn = "../../test/files/rowetech_seawatch.ens"
    fn = "../../test/files/"
    data = RtiReader([fn + "rowetech_seawatch.ens"]).read()

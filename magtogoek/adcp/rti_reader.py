"""
RTI readers for Rowetech ENS files based on rti_tools by jeanlucshaw and rti_python.
Only tested on SeaWatch adcp.

Uses rti_python Ensemble and Codecs to read and decode data. The data are then loaded in a
`Bunch` object taken from pycurrents. This allows us to use to same loader for RDI and RTI data.

Usage:
data = RtiReader(filenames).read()
filenames: path/to/filename or list(path/to/filenames) or path/to/regex.

"""

import logging
from datetime import datetime
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Dict, List, Tuple, Type

import numpy as np
from magtogoek.adcp.utils import datetime_to_dday, get_files_from_expresion
from rti_python.Codecs.BinaryCodec import BinaryCodec
from rti_python.Ensemble.EnsembleData import *
from scipy.constants import convert_temperature
from scipy.interpolate import griddata
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


class RtiReader:
    def __init__(self, filenames: Tuple[str, List]):
        """
        Parameters
        ----------
        filenames
            path/to/filename or list(path/to/filenames) or path/to/regex
        """
        self.filenames = get_files_from_expresion(filenames)

        self.DELIMITER = b"\x80" * 16  # RTB ensemble delimiter
        self.BLOCK_SIZE = 4096  # Size of the Bytes Block Read at a time

    def read(self, start_index: int = 0, stop_index: int = 0):
        """Call read_file.
        return a Bunch object with the read data."""

        self.start_index = start_index
        self.stop_index = stop_index
        files_index = dict()
        for filename in self.filenames:
            ens_count = self.check_file_for_ens
            if ens_count == 0:
                filenames.remove(filename)
            elif ens_count < self.start_index:
                filenames.remove(filename)
                self.start_index -= ens_count
            elif ens_count > self.start_index:
                files_index[filenames] = (self.start_index, ens_count)
                self.start_index = 0

        bunch_list = []
        for filename in self.filenames:
            self.ens_file_path = filename
            self.get_ens_chunks()
            start_index, stop_index = files_index[filename]
            self.chunk_list = self.chunk_list[start_index:stop_index]

            bunch_list.append(self.read_file_chunks())

        data = self.concatenate_files_bunch(bunch_list)

        return data

    def get_ens_chunks(self):
        """Read the binary ens file and get ensemble (chunk/ping)

        makes attributes chunk_list: List[(chunk_idx, chunk)]

        """
        buff = bytes()
        ii = 0
        self.chunk_list = []

        with open(self.ens_file_path, "rb") as f:

            data = f.read(self.BLOCK_SIZE)

            while data:
                buff += data
                if self.DELIMITER in buff:
                    chunks = buff.split(self.DELIMITER)
                    buff = chunks.pop()
                    for chunk in chunks:
                        if BinaryCodec.verify_ens_data(self.DELIMITER + chunk):
                            self.chunk_list.append((ii, self.DELIMITER + chunk))
                            ii += 1

                data = f.read(self.BLOCK_SIZE)

            # check the remaining bytes in buffer
            if BinaryCodec.verify_ens_data(self.DELIMITER + buff):
                self.chunk_list.append((ii, self.DELIMITER + buff))
                ii += 1

    def check_file_for_ens(self):
        """Read the binary ens file and count the number of chunks"""
        buff = bytes()
        ii = 0

        with open(self.ens_file_path, "rb") as f:

            data = f.read(self.BLOCK_SIZE)

            while data:
                buff += data
                if self.DELIMITER in buff:
                    chunks = buff.split(self.DELIMITER)
                    buff = chunks.pop()
                    for chunk in chunks:
                        if BinaryCodec.verify_ens_data(self.DELIMITER + chunk):
                            ii += 1

                data = f.read(self.BLOCK_SIZE)

            # check the remaining bytes in buffer
            if BinaryCodec.verify_ens_data(self.DELIMITER + buff):
                ii += 1

        self.number_of_chunks = ii

        if len(self.chunk_list) == 0:
            print(f"No data found in {self.ens_file_path}")

    def read_file_chunks(self) -> Type[Bunch]:
        """Read data from one RTB .ENS file put them into a Bunch object

        Parameters
        ----------
        ens_file_path
            path/to/ens_file_path

        Returns
        -------
        Bunch:
            bunch with the read data.

        """
        # Get `static` data from the first ensemble.
        ens = BinaryCodec.decode_data_sets(self.chunk_list[0][1])

        # Get coordinate sizes
        ppd = Bunch()
        ppd.filename = Path(self.ens_file_path).name
        ppd.ens_count = len(self.chunk_list)

        ppd.nbin = ens.EnsembleData.NumBins
        ppd.NBeams = ens.EnsembleData.NumBeams
        ppd.yearbase = ens.EnsembleData.Year
        ppd.instrument_serial = ens.EnsembleData.SerialNumber

        ppd.CellSize = ens.AncillaryData.BinSize
        ppd.Bin1Dist = ens.AncillaryData.FirstBinRange

        ppd.dep = ppd.Bin1Dist + np.arange(0, ppd.nbin * ppd.CellSize, ppd.CellSize)

        ppd.pingtype = ens.SystemSetup.WpBroadband
        ppd.sysconfig = dict(
            angle=self._beam_angle(ppd.instrument_serial),
            kHz=ens.SystemSetup.WpSystemFreqHz,
            convex=True,  # Rowetech adcp seems to be convex.
            up=None,
        )
        if ens.IsBeamVelocity:
            ppd.trans = dict(coordsystem="beam")
        if ens.IsInstrumentVelocity:
            ppd.trans = dict(coordsystem="xyz")
        if ens.IsEarthVelocity:
            ppd.trans = dict(coordsystem="earth")

        # reading all the chucnks.
        ppd = Bunch(**ppd, **self.read_chunks())

        # Determine up/down configuration
        mean_roll = circmean(np.radians(ppd.roll))
        ppd.sysconfig["up"] = True if abs(mean_roll) < np.radians(30) else False

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

    def read_chunks(self) -> Type[Bunch]:
        """Read chunks over multple process

        Notes:
        ------
        This could be somewhat faster if the tqdm was removed. It takes ~.25 additional seconds
        (~5s total) for ~4000 chunks. Exiting the processes to output progress could be time consuming
        for bigger files.
        """
        # spliting the reading workload on multiple cpu
        number_of_cpu = cpu_count() - 1

        print(f"Reading {self.ens_file_path}")
        time0 = datetime.now()

        with Pool(number_of_cpu) as p:  # test
            self.data_list = p.starmap(self.decode_chunk, tqdm(self.chunk_list))  # test

        time1 = datetime.now()
        print(
            len(self.chunk_list),
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

            if k == "vel":
                #  change de vel fill values to the one used by teledyne.
                ppd.vel[ppd.vel == 88.88800048828125] = -32768.0

            if ppd[k].ndim == 3:
                ppd.split(k)
        if "bt_vel" in ppd:
            #  change de vel fill values to the one used by teledyne.
            ppd.bt_vel[ppd.bt_vel == 88.88800048828125] = -32768.0

        return ppd

    @staticmethod
    def decode_chunk(ii: int, chunk: str) -> Type[Bunch]:
        """Read single chunk of data.

        Parameters:
        -----------
        ii:
            Index of the chunk in the file. It is passed one with the Bunch
        chunk:
            chunk of binary data containing one ensemble.

        Notes:
        ------
        Correlation are multipled by 255 to be between 0 and 255 (like RDI).
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
            ppd.temperature = convert_temperature(
                np.array(ens.AncillaryData.WaterTemp),
                "fahrenheit",
                "celsius",
            )
            ppd.salinity = np.array(ens.AncillaryData.Salinity)
            pressure = np.array(ens.AncillaryData.Pressure) / 10  # pascal to decapascal
            ppd.VL = np.array(pressure, {"names": ["Pressure"], "formats": [np.float]})
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

    @staticmethod
    def _beam_angle(serial_number):
        """Get the beam angle from the serial number"""
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
    def format_rawnav(data: Type[Bunch]) -> Dict:
        """Format rawnav to pycurent rawnav.

        Interpolates longitude and latitude on adcp dday.
        """

        gps_dday = datetime_to_dday(data.gsp_datetime)

        rawnav = dict(
            Lon1_BAM4=griddata(gps_dday, data.longitude, data.dday) / (180.0 / 2 ** 31),
            Lat1_BAM4=griddata(gps_dday, data.latitude, data.dday) / (180.0 / 2 ** 31),
        )
        return rawnav

    @staticmethod
    def concatenate_files_bunch(bunches):
        """"""
        ppd = Bunch()
        b0 = bunches[0]
        ppd.dep = b0.dep
        dist1bin_list = []
        filename_list = []
        for bunch in bunches:
            dist1bin_list.append(bunch.Bin1Dist - b0.Bin1Dist)
            filename_list.append(bunch.filename)

        dist1bin_list = np.array(dist1bin_list)
        if dist1bin_list.any() != 0:
            print(f"Bin depth computed from {b0.ens_file_path}")
            for d, f in zip(dist1bin_list, filename_list):
                if d != 0:
                    print(f"Distance of the first bin in file {f} differs by {d} m")

        for k in b0:
            if k == "dep" or not isinstance(b0[k], np.ndarray):
                ppd[k] = b0[k]
            else:
                chunks = [p[k] for p in bunches]
                ppd[k] = np.concatenate(chunks)

        return ppd


if __name__ == "__main__":
    fp = "../../test/files/"
    fn = "rowetech_seawatch.ens"

    # fp0 = '/media/sf_Shared_Folder/IML4_2017_ENS/'
    #    data = RtiReader(fp + "*.ens").read()

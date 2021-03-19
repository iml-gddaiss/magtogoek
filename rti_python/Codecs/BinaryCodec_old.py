import struct
import abc
import copy
from rti_python.Utilities.events import EventHandler

from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Ensemble.BeamVelocity import BeamVelocity
from rti_python.Ensemble.InstrumentVelocity import InstrumentVelocity
from rti_python.Ensemble.EarthVelocity import EarthVelocity
from rti_python.Ensemble.Amplitude import Amplitude
from rti_python.Ensemble.Correlation import Correlation
from rti_python.Ensemble.GoodBeam import GoodBeam
from rti_python.Ensemble.GoodEarth import GoodEarth
from rti_python.Ensemble.EnsembleData import EnsembleData
from rti_python.Ensemble.AncillaryData import AncillaryData
from rti_python.Ensemble.BottomTrack import BottomTrack
from rti_python.Ensemble.NmeaData import NmeaData
from rti_python.Ensemble.RangeTracking import RangeTracking
from rti_python.Ensemble.SystemSetup import SystemSetup
from PyCRC.CRCCCITT import CRCCCITT
import logging
from threading import Thread, Condition
import threading

class WaveBurstInfo:
    """
    Information about the waves burst setup.
    """

    def __init__(self):
        self.SamplesPerBurst = 0
        self.Lat = ""
        self.Lon = ""
        self.Bin1 = 0
        self.Bin2 = 0
        self.Bin3 = 0


class BinaryCodecOld(Thread):
    """
    Decode RoweTech ADCP Binary data.
    """

    # Use for publish and subscribe event
    __metaclass__ = abc.ABCMeta

    def __init__(self):

        Thread.__init__(self)
        self.thread_alive = True
        self.thread_lock = Condition()
        #self.start()

        self.buffer = bytearray()

        self.MAX_TIMEOUT = 5
        self.timeout = 0
        self.DELIMITER = b'\x80'*16

        self.EnsembleEvent = EventHandler(self)

    def shutdown(self):
        """
        Shutdown the thread.
        :return:
        """
        self.thread_alive = False
        self.thread_lock.acquire()
        self.thread_lock.notify()
        self.thread_lock.release()
        if self.is_alive():
            self.join()

    def add(self, data):
        """
        Add to buffer and Decode
        :param data: Raw byte data.
        """
        self.thread_lock.acquire()                                      # Lock the buffer
        self.buffer.extend(data)                                        # Set the data to the buffer

        # Check if enough data is in the buffer to process
        if len(self.buffer) > Ensemble.HeaderSize + Ensemble.ChecksumSize + 200:
            self.thread_lock.notify()                                   # Notify to process the buffer

        self.thread_lock.release()                                      # Unlock buffer

    def run(self):
        """
        Find the start of an ensemble.  Then find the end of the ensemble.
        Then remove the ensemble from the buffer and process the raw data.
        :return:
        """

        while self.thread_alive:
            # Lock to look for the data
            self.thread_lock.acquire()

            # Create a buffer to hold the ensemble
            bin_ens_list = []
            timeout = 0

            # Wait for the next ensemble added to the buffer
            self.thread_lock.wait()

            # Look for first 16 bytes of header
            ens_start = self.buffer.find(self.DELIMITER)

            # Verify enough data is in the buffer for an ensemble header
            while ens_start >= 0 and len(self.buffer) > Ensemble().HeaderSize + ens_start:
                # Decode the Ensemble
                bin_ens = self.decode_ensemble(ens_start)

                # Add the data to the list or count for timeout
                if len(bin_ens) > 0:
                    # Add it to the list
                    bin_ens_list.append(bin_ens)
                else:
                    # Timeout if we are only getting bad data
                    timeout += 1
                    if timeout > 5:
                        logging.warning("Find good ensemble timeout")
                        break

                # Search if there is a new start location
                ens_start = self.buffer.find(self.DELIMITER)

            self.thread_lock.release()

            # If data was found for an ensemble
            # Process the ensemble binary data
            for ens in bin_ens_list:
                if len(ens) > 0:
                    # Decode data
                    ensemble = BinaryCodec.decode_data_sets(ens)

                    if ensemble:
                        # Publish the ensemble
                        self.process_ensemble(ensemble)
                else:
                    logging.debug("No Ensemble data found")

    def decode_ensemble(self, ensStart):
        """
        Decode the raw ensemble data.  This will check the checksum and verify it is correct,
        then decode each datasets.  Then remove the data from the buffer.
        :param ensStart: Stare of the ensemble in the buffer.
        """
        bin_ens = []

        # Check Ensemble number
        ens_num = struct.unpack("I", self.buffer[ensStart+16:ensStart+20])

        # Check ensemble size
        payload_size = struct.unpack("I", self.buffer[ensStart+24:ensStart+28])

        # Ensure the entire ensemble is in the buffer
        if len(self.buffer) >= ensStart + Ensemble().HeaderSize + payload_size[0] + Ensemble().ChecksumSize:
            # Reset timeout
            self.timeout = 0

            # Check checksum
            checksumLoc = ensStart + Ensemble().HeaderSize + payload_size[0]
            checksum = struct.unpack("I", self.buffer[checksumLoc:checksumLoc + Ensemble().ChecksumSize])

            # Calculate Checksum
            # Use only the payload for the checksum
            ens = self.buffer[ensStart + Ensemble().HeaderSize:ensStart + Ensemble().HeaderSize + payload_size[0]]
            calcChecksum = CRCCCITT().calculate(input_data=bytes(ens))
            #print("Calc Checksum: ", calcChecksum)
            #print("Checksum: ", checksum[0])
            #print("Checksum good: ", calcChecksum == checksum[0])

            if checksum[0] == calcChecksum:
                logging.debug(ens_num[0])
                try:
                    # Make a deep copy of the ensemble data
                    bin_ens = copy.deepcopy(self.buffer[ensStart:ensStart + Ensemble().HeaderSize + payload_size[0]])

                    # Remove ensemble from buffer
                    ens_end = ensStart + Ensemble().HeaderSize + payload_size[0] + Ensemble().ChecksumSize
                    del self.buffer[0:ens_end]

                except Exception as e:
                    logging.error("Error processing ensemble. ", e)
        else:
            logging.warning("Not a complete buffer.  Waiting for data")

            # Give it a couple tries to see if more data will come in to make a complete header
            self.timeout += 1

            # Check for timeout
            if self.timeout > self.MAX_TIMEOUT:
                del self.buffer[0]
                logging.warning("Buffered data did not have a good header.  Header search TIMEOUT")
                self.timeout = 0

        return bin_ens

    @abc.abstractmethod
    def process_ensemble(self, ens):
        # Pass to event handler
        self.EnsembleEvent(ens)
        logging.debug("Ensemble Processed")

    @staticmethod
    def verify_ens_data(ens_data, ens_start=0):
        """
        This will check the checksum and verify it is correct.
        :param ens_data: Ensemble data.
        :param ens_start: Start location in the ens_data
        """
        try:
            # Ensemble Length
            ens_len = len(ens_data)

            # Verify at least the minimum number of bytes are available to verify the ensemble
            if ens_len <= Ensemble().HeaderSize + Ensemble().ChecksumSize:
                return False

            # Check Ensemble number
            ens_num = struct.unpack("I", ens_data[ens_start + 16:ens_start + 20])

            # Check ensemble size
            payload_size = struct.unpack("I", ens_data[ens_start + 24:ens_start + 28])

            # Ensure the entire ensemble is in the buffer
            if ens_len >= ens_start + Ensemble().HeaderSize + payload_size[0] + Ensemble().ChecksumSize:

                # Check checksum
                checksum_loc = ens_start + Ensemble().HeaderSize + payload_size[0]
                checksum = struct.unpack("I", ens_data[checksum_loc:checksum_loc + Ensemble().ChecksumSize])

                # Calculate Checksum
                # Use only the payload for the checksum
                ens = ens_data[ens_start + Ensemble().HeaderSize:ens_start + Ensemble().HeaderSize + payload_size[0]]
                calc_checksum = CRCCCITT().calculate(input_data=bytes(ens))

                # Verify checksum
                if checksum[0] == calc_checksum:
                    logging.debug(ens_num[0])
                    return True
                else:
                    return False
            else:
                #logging.warning("Not a complete ensemble.")
                return False

        except Exception as e:
            logging.error("Error verifying Ensemble.  " + str(e))
            return False

        return False

    @staticmethod
    def decode_data_sets(ens):
        """
        Decode the datasets in the ensemble.

        Use verify_ens_data if you are using this
        as a static method to verify the data is correct.
        :param ens: Ensemble data.  Decode the dataset.
        :return: Return the decoded ensemble.
        """
        #print(ens)
        packetPointer = Ensemble().HeaderSize
        type = 0
        numElements = 0
        elementMultiplier = 0
        imag = 0
        nameLen = 0
        name = ""
        dataSetSize = 0
        ens_len = len(ens)

        # Create the ensemble
        ensemble = Ensemble()

        # Add the raw data to the ensemble
        #ensemble.AddRawData(ens)

        try:

            # Decode the ensemble datasets
            for x in range(Ensemble().MaxNumDataSets):
                # Check if we are at the end of the payload
                if packetPointer >= ens_len - Ensemble.ChecksumSize - Ensemble.HeaderSize:
                    break

                try:
                    # Get the dataset info
                    ds_type = Ensemble.GetInt32(packetPointer + (Ensemble.BytesInInt32 * 0), Ensemble().BytesInInt32, ens)
                    num_elements = Ensemble.GetInt32(packetPointer + (Ensemble.BytesInInt32 * 1), Ensemble().BytesInInt32, ens)
                    element_multiplier = Ensemble.GetInt32(packetPointer + (Ensemble.BytesInInt32 * 2), Ensemble().BytesInInt32, ens)
                    image = Ensemble.GetInt32(packetPointer + (Ensemble.BytesInInt32 * 3), Ensemble().BytesInInt32, ens)
                    name_len = Ensemble.GetInt32(packetPointer + (Ensemble.BytesInInt32 * 4), Ensemble().BytesInInt32, ens)
                    name = str(ens[packetPointer+(Ensemble.BytesInInt32 * 5):packetPointer+(Ensemble.BytesInInt32 * 5)+8], 'UTF-8')
                except Exception as e:
                    logging.warning("Bad Ensemble header" + str(e))
                    break

                # Calculate the dataset size
                data_set_size = Ensemble.GetDataSetSize(ds_type, name_len, num_elements, element_multiplier)

                # Beam Velocity
                if "E000001" in name:
                    logging.debug(name)
                    bv = BeamVelocity(num_elements, element_multiplier)
                    bv.decode(ens[packetPointer:packetPointer+data_set_size])
                    ensemble.AddBeamVelocity(bv)

                # Instrument Velocity
                if "E000002" in name:
                    logging.debug(name)
                    iv = InstrumentVelocity(num_elements, element_multiplier)
                    iv.decode(ens[packetPointer:packetPointer+data_set_size])
                    ensemble.AddInstrumentVelocity(iv)

                # Earth Velocity
                if "E000003" in name:
                    logging.debug(name)
                    ev = EarthVelocity(num_elements, element_multiplier)
                    ev.decode(ens[packetPointer:packetPointer+data_set_size])
                    ensemble.AddEarthVelocity(ev)

                # Amplitude
                if "E000004" in name:
                    logging.debug(name)
                    amp = Amplitude(num_elements, element_multiplier)
                    amp.decode(ens[packetPointer:packetPointer+data_set_size])
                    ensemble.AddAmplitude(amp)

                # Correlation
                if "E000005" in name:
                    logging.debug(name)
                    corr = Correlation(num_elements, element_multiplier)
                    corr.decode(ens[packetPointer:packetPointer+data_set_size])
                    ensemble.AddCorrelation(corr)

                # Good Beam
                if "E000006" in name:
                    logging.debug(name)
                    gb = GoodBeam(num_elements, element_multiplier)
                    gb.decode(ens[packetPointer:packetPointer+data_set_size])
                    ensemble.AddGoodBeam(gb)

                # Good Earth
                if "E000007" in name:
                    logging.debug(name)
                    ge = GoodEarth(num_elements, element_multiplier)
                    ge.decode(ens[packetPointer:packetPointer+data_set_size])
                    ensemble.AddGoodEarth(ge)

                # Ensemble Data
                if "E000008" in name:
                    logging.debug(name)
                    ed = EnsembleData(num_elements, element_multiplier)
                    ed.decode(ens[packetPointer:packetPointer+data_set_size])
                    ensemble.AddEnsembleData(ed)

                # Ancillary Data
                if "E000009" in name:
                    logging.debug(name)
                    ad = AncillaryData(num_elements, element_multiplier)
                    ad.decode(ens[packetPointer:packetPointer+data_set_size])
                    ensemble.AddAncillaryData(ad)

                # Bottom Track
                if "E000010" in name:
                    logging.debug(name)
                    bt = BottomTrack(num_elements, element_multiplier)
                    bt.decode(ens[packetPointer:packetPointer + data_set_size])
                    ensemble.AddBottomTrack(bt)

                # NMEA data
                if "E000011" in name:
                    logging.debug(name)
                    nd = NmeaData(num_elements, element_multiplier)
                    nd.decode(ens[packetPointer:packetPointer + data_set_size])
                    ensemble.AddNmeaData(nd)

                # System Setup
                if "E000014" in name:
                    logging.debug(name)
                    ss = SystemSetup(num_elements, element_multiplier)
                    ss.decode(ens[packetPointer:packetPointer + data_set_size])
                    ensemble.AddSystemSetup(ss)

                # Range Tracking
                if "E000015" in name:
                    logging.debug(name)
                    rt = RangeTracking(num_elements, element_multiplier)
                    rt.decode(ens[packetPointer:packetPointer + data_set_size])
                    ensemble.AddRangeTracking(rt)

                # Move to the next dataset
                packetPointer += data_set_size

        except Exception as e:
            logging.warning("Error decoding the ensemble.  " + str(e))
            return None

        return ensemble






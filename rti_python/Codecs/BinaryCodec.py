import logging
from obsub import event
from threading import Thread, Condition
import struct
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
import binascii

# Buffer to hold the incoming data
buffer = bytearray()

# Condition to protect the buffer and make the threads sleep.
global_condition = Condition()


class BinaryCodec:
    """
    Use the 2 threads, AddDataThread and ProcessDataThread
    to buffer the streaming data and decode it.

    Subscribe to ensemble_event to receive the latest
    decoded data.
    bin_codec.ensemble_event += event_handler

    event_handler(self, sender, ens)

     AddDataThread will buffer the data.
     ProcessDataThread will decode the buffer.
    """

    def __init__(self):
        """
        Start the two threads.
        """
        # Start the Add Data Thread
        self.add_data_thread = AddDataThread()
        self.add_data_thread.start()

        # Start the Processing Data Thread
        self.process_data_thread = ProcessDataThread()
        self.process_data_thread.ensemble_event += self.receive_ens
        self.process_data_thread.start()

    def shutdown(self):
        """
        Shutdown the two threads.
        :return:
        """
        self.add_data_thread.shutdown()
        self.process_data_thread.shutdown()

    @event
    def ensemble_event(self, ens):
        """
        Event to subscribe to receive the latest ensemble data.
        :param ens: Ensemble object
        :return:
        """
        if ens.IsEnsembleData:
            logging.debug(str(ens.EnsembleData.EnsembleNumber))

    def receive_ens(self, sender, ens):
        """
        Event handler for ProcessDataThread to receive the latest ensembles.
        :param sender: Not Used
        :param ens: Ensemble data
        :return:
        """
        # Pass to the ensemble to subscribers of this object
        self.ensemble_event(ens)

    def add(self, data):
        """
        Add data to the AddDataThread.  This will start the
        processing of the data.
        :param data: Data to start decoding.
        :return:
        """
        self.add_data_thread.add(data)

    def buffer_size(self):
        """
        Monitor the buffer size.
        :return: Buffer size to monitor.
        """
        global buffer
        return len(buffer)

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
                calc_checksum = binascii.crc_hqx(ens, 0)

                # Verify checksum
                if checksum[0] == calc_checksum:
                    logging.debug(ens_num[0])
                    return True
                else:
                    logging.warning("Ensemble fails checksum. {:#04x} {:#04x}".format(checksum[0], calc_checksum))
                    return False
            else:
                logging.warning("Incomplete ensemble.")
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


class AddDataThread(Thread):
    """
    Receive all incoming data.  Buffer the data
    and wakeup ProcessDataThread with "condition".
    """

    def __init__(self):
        """
        Initialize the thread.
        """
        Thread.__init__(self)
        self.name = "Binary Codec Add Data Thread"
        self.internal_condition = Condition()
        self.alive = True
        self.temp_data = bytes()

    def shutdown(self):
        """
        Shutdown the object.  Stop the thread.
        :return:
        """
        self.alive = False
        with self.internal_condition:
            self.internal_condition.notify()

        if self.is_alive():
            self.join()

    def add(self, data):
        """
        Add data to the buffer.  Then wakeup the internal thread with the "internal_condition".
        :param data: Data to buffer.
        :return:
        """

        # Store the data to be buffered
        with global_condition:
            self.temp_data = self.temp_data + data

        # Wakeup the thread
        with self.internal_condition:
            self.internal_condition.notify()

    def run(self):
        """
        Take the data from the temp location and place it the buffer.
        Then wakeup the ProcessDataThread with "condition".
        :return:
        """
        # Get the global buffer
        # It is shared with the 2 threads
        global buffer

        # Verify the thread is still alive
        while self.alive:

            with self.internal_condition:
                # Wait to wakeup when data arrives
                self.internal_condition.wait()

            with global_condition:
                buffer += self.temp_data             # Set the data to the buffer
                #print("Buffer: " + str(len(buffer)))

                # Clear the temp data
                self.temp_data = bytes()

                # Check if enough data is in the buffer to process
                if len(buffer) > Ensemble.HeaderSize + Ensemble.ChecksumSize + 200:
                    global_condition.notify()          # Notify to process the buffer


class ProcessDataThread(Thread):
    """
    Process the incoming data.  This will take the shared buffer.
    The AddDataThread will wakeup this thread with "condition".  It
    will then process the incoming data in the buffer and look for
    ensemble data.  When ensemble data is decoded it will passed to the
    subscribers of the event "ensemble_event".
    """

    def __init__(self):
        """
        Initialize this object as a thread.
        """
        Thread.__init__(self)
        self.name = "Binary Codec Process Data Thread"
        self.alive = True
        self.MAX_TIMEOUT = 5
        self.timeout = 0
        self.DELIMITER = b'\x80' * 16

    def shutdown(self):
        """
        Shutdown this object.
        :return:
        """
        self.alive = False
        with global_condition:
            global_condition.notify()

        if self.is_alive():
            self.join()

    @event
    def ensemble_event(self, ens):
        """
        Event to subscribe to receive decoded ensembles.
        :param ens: Ensemble object.
        :return:
        """
        if ens.IsEnsembleData:
            logging.debug(str(ens.EnsembleData.EnsembleNumber))

    def run(self):
        """
        Get the global buffer that is shared with the AddDataThread.

        When data is received, the this thread will be unblocked with "condition".
        Process the incoming data.  Look for ensemble data. Verify and decode the binary data.
        Once an ensemble is processed, pass it to event.  All subscribers of the event will
        receive the ensemble.
        :return:
        """
        # Get the global buffer
        # It is shared with the 2 threads
        global buffer

        # Verify the thread is still alive
        while self.alive:
            # Wait for data
            with global_condition:
                if self.DELIMITER in buffer:                                # Check for the delimiter
                    chunks = buffer.split(self.DELIMITER)                   # If delimiter found, split to get the remaining buffer data
                    buffer = chunks.pop()                                   # Put the remaining data back in the buffer

                    for chunk in chunks:                                    # Take out the ens data
                        self.verify_and_decode(self.DELIMITER + chunk)      # Process the binary ensemble data

    def verify_and_decode(self, ens_bin):
        # Verify the ENS data is good
        # This will check that all the data is there and the checksum is good
        if BinaryCodec.verify_ens_data(ens_bin):
            # Decode the ens binary data
            ens = BinaryCodec.decode_data_sets(ens_bin)

            # Pass the ensemble
            if ens:
                self.ensemble_event(ens)


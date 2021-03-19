import os
import re
import logging
import numpy as np
import struct
import binascii


class RtbRowe(object):
    """
    Class to read data from RTB files

    Single file to read in RTB data, then create an list of objects.  The lists will contain all the
    data from the file.

    This file was specifically created to work in QRevPy to decode RTI data and follow QRevPy's data format.
    """

    # Prevent Magic Numbers
    HEADER_SIZE = 32                    # Header size in bytes
    CHECKSUM_SIZE = 4                   # Checksum size in bytes
    MAX_DATASETS = 20                   # Maximum number of datasets in an ensemble
    BYTES_IN_INT32 = 4                  # Bytes in Int32
    BYTES_IN_FLOAT = 4                  # Bytes in Float
    NUM_DATASET_HEADER_ELEMENTS = 6     # Number of elements in dataset header
    BAD_VEL = 88.888                    # RTB Bad Velocity
    PD0_BAD_VEL = -32768                # PD0 Bad Velocity
    PD0_BAD_AMP = 255                   # PD0 Bad Amplitude

    def __init__(self, file_path: str, use_pd0_format: bool = False):
        """
        Constructor initializing instance variables.
        Set the use_pd0_format value if you want the values stored as a PD0 file.
        PD0 uses different scales for its values compared to RTB.

        :param file_path: Full Path of RTB file to be read
        :param use_pd0_format: Determine if the data should be decoded as RTB or PD0 scales.
        """

        # File path
        self.file_name = file_path
        self.use_pd0_format = use_pd0_format

        # List of all the ensemble data decoded
        self.Cfg = Cfg(pd0_format=use_pd0_format)
        self.Sensor = Sensor(pd0_format=use_pd0_format)
        self.Amp = Amplitude(pd0_format=use_pd0_format)
        self.Corr = Correlation(pd0_format=use_pd0_format)
        self.BeamVel = BeamVelocity(pd0_format=use_pd0_format)
        self.InstrVel = InstrVelocity(pd0_format=use_pd0_format)
        self.EarthVel = EarthVelocity(pd0_format=use_pd0_format)
        self.GdB = GoodBeam(pd0_format=use_pd0_format)
        self.GdE = GoodEarth(pd0_format=use_pd0_format)
        self.Rt = RT(pd0_format=use_pd0_format)
        self.Bt = BT(pd0_format=use_pd0_format)
        self.Nmea = Nmea(pd0_format=use_pd0_format)
        self.Gage = Gage(pd0_format=use_pd0_format)
        self.Gps = []
        self.Gps2 = []
        self.Surface = []
        self.AutoMode = []
        self.Wt = []
        self.River_BT = RiverBT(pd0_format=use_pd0_format)

        # Read in the given file path
        self.rtb_read(file_path=file_path, use_pd0_format=self.use_pd0_format)

    @staticmethod
    def count_ensembles(file_path: str):
        """
        Get the file information like the number of ensembles in the file.
        """
        # RTB ensemble delimiter
        DELIMITER = b'\x80' * 16

        # Block size to read in data
        BLOCK_SIZE = 4096

        # Keep count of the number of ensembles found
        ens_count = 0

        # Search for the number of ensembles by looking for the delimiter
        # Check to ensure file exists
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read(BLOCK_SIZE)  # Read in data

                # Verify data was found
                while data:
                    # Check for the delimiter
                    if DELIMITER in data:
                        ens_count += 1

                    # Read the next batch of data
                    data = f.read(BLOCK_SIZE)

        return ens_count

    def get_file_info(self, file_path: str):
        """
        Get the file information like the number of ensembles,
        number of beams and number of bins.
        This only counts 3 or 4 beam ensembles.  Vertical beams
        will be merged with 4 beam ensembles.

        :param file_path File path to inspect.
        :return NumEnsembles, NumBeams, NumBins
        """
        # RTB ensemble delimiter
        DELIMITER = b'\x80' * 16

        # Block size to read in data
        BLOCK_SIZE = 4096

        # Create a buffer
        buff = bytes()

        # Keep count of the number of ensembles found
        ens_count = 0
        num_beams = 0
        num_bins = 0

        # Search for the number of ensembles by looking for the delimiter
        # Check to ensure file exists
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read(BLOCK_SIZE)  # Read in data

                # Verify data was found
                while data:
                    # Accumulate the buffer
                    buff += data

                    # Check for the delimiter
                    if DELIMITER in buff:
                        # If delimiter found, split at the delimiter to get the remaining buffer data
                        chunks = buff.split(DELIMITER)

                        # Put the remaining data back in the buffer
                        buff = chunks.pop()

                        # Take out the ens data
                        for chunk in chunks:
                            # Process the binary ensemble data
                            # Verify the ENS data is good
                            # This will check that all the data is there and the checksum is good
                            if self.verify_ens_data(DELIMITER + chunk):
                                # Get the ensemble info
                                bin_count, beams_count = self.get_ens_info(DELIMITER + chunk)

                                # Verify we have 3 or 4 beam data ensemble
                                # Vertical beam is not counted and is merged with 4 beam ensembles
                                if beams_count > 2:
                                    ens_count += 1

                                    # Set the largest beam and bin number
                                    num_beams = max(beams_count, num_beams)
                                    num_bins = max(bin_count, num_bins)

                    # Read the next batch of data
                    data = f.read(BLOCK_SIZE)

            # Process whatever is remaining in the buffer
            # Verify the ENS data is good
            # This will check that all the data is there and the checksum is good
            if self.verify_ens_data(DELIMITER + buff):
                # Get the ensemble info
                bin_count, beams_count = self.get_ens_info(DELIMITER + buff)

                # Verify we have 3 or 4 beam data ensemble
                # Vertical beam is not counted and is merged with 4 beam ensembles
                if beams_count > 2:
                    ens_count += 1

                    # Set the largest beam and bin number
                    num_beams = max(beams_count, num_beams)
                    num_bins = max(bin_count, num_bins)

        return ens_count, num_beams, num_bins

    def rtb_read(self, file_path: str, wr2: bool = False, use_pd0_format: bool = False):
        """
        Reads the binary RTB file and assigns values to object instance variables.
        :param file_path: Full file path
        :param wr2: Determines if WR2 processing should be applied to GPS data
        :param use_pd0_format: Determine if data should be RTB or PD0 format.  Convert values to PD0 values.
        """

        # RTB ensemble delimiter
        DELIMITER = b'\x80' * 16

        # Block size to read in data
        BLOCK_SIZE = 4096

        # Get the total file size to keep track of total bytes read and show progress
        file_size = os.path.getsize(file_path)
        bytes_read = 0

        # Create a buffer
        buff = bytes()

        # Assign default values
        n_velocities = 4
        max_surface_bins = 5

        # Check to ensure file exists
        if os.path.exists(file_path):
            file_info = os.path.getsize(file_path)

            with open(file_path, "rb") as f:
                data = f.read(BLOCK_SIZE)  # Read in data

                # Keep track of bytes read
                #bytes_read += BLOCK_SIZE
                #self.file_progress(bytes_read, file_size, fullname)

                # Verify data was found
                while data:
                    # Accumulate the buffer
                    buff += data

                    # Check for the delimiter
                    if DELIMITER in buff:
                        # If delimiter found, split at the delimiter to get the remaining buffer data
                        chunks = buff.split(DELIMITER)

                        # Put the remaining data back in the buffer
                        buff = chunks.pop()

                        # Take out the ens data
                        for chunk in chunks:
                            # Process the binary ensemble data
                            self.decode_ens(DELIMITER + chunk, use_pd0_format=use_pd0_format)

                    # Read the next batch of data
                    data = f.read(BLOCK_SIZE)

                    # Keep track of bytes read
                    bytes_read += BLOCK_SIZE
                    # self.file_progress(bytes_read, file_size, ens_file_path)
                    #self.file_progress(BLOCK_SIZE, file_size, fullname)

            # Process whatever is remaining in the buffer
            self.decode_ens(DELIMITER + buff, use_pd0_format=use_pd0_format)

    def get_ens_info(self, ens_bytes: list):
        """
        Decode the datasets to an ensemble to get the general information about the ensemble.
        This includes the number of beams and bins.
        Use verify_ens_data if you are using this
        as a static method to verify the data is correct.
        :param ens_bytes: Ensemble binary data.  Decode the dataset.
        :return: Return number of beam and number of bins.
        """
        packetPointer = self.HEADER_SIZE
        ens_len = len(ens_bytes)

        num_elements = 0
        element_multiplier = 0

        # Decode the ensemble datasets
        # Limit the number of attempts to look for new datasets
        for x in range(self.MAX_DATASETS):
            # Check if we are at the end of the payload
            if packetPointer >= ens_len - RtbRowe.CHECKSUM_SIZE - RtbRowe.HEADER_SIZE:
                break

            # Get the dataset info
            ds_type = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 0), RtbRowe.BYTES_IN_INT32, ens_bytes)
            num_elements = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 1), RtbRowe.BYTES_IN_INT32, ens_bytes)
            element_multiplier = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 2), RtbRowe.BYTES_IN_INT32, ens_bytes)
            image = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 3), RtbRowe.BYTES_IN_INT32, ens_bytes)
            name_len = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 4), RtbRowe.BYTES_IN_INT32, ens_bytes)
            name = str(ens_bytes[packetPointer + (RtbRowe.BYTES_IN_INT32 * 5):packetPointer + (RtbRowe.BYTES_IN_INT32 * 5) + 8], 'UTF-8')

            # Beam velocity will contain all the information we need
            if "E000001" in name:
                # Return the number bins and number of beams
                return num_elements, element_multiplier

        return num_elements, element_multiplier

    def decode_ens(self, ens_bytes: list, use_pd0_format: bool = False):
        """
        Attempt to decode the ensemble.  This will verify the checksum passes.
        If the checksum is good, then decode the data.
        When the data is decoded, automatically add it to list of ensembles.
        :param ens_bytes: Ensemble byte array to decode.
        :param use_pd0_format: Flag if the data should be decoded to PD0 format.
        :return
        """

        # Verify the ENS data is good
        # This will check that all the data is there and the checksum is good
        if self.verify_ens_data(ens_bytes):
            # Decode the ens binary data
            logging.debug("Decoding binary data to ensemble: " + str(len(ens_bytes)))

            # Decode the data
            self.decode_data_sets(ens_bytes, use_pd0_format=use_pd0_format)

            # Add the ensemble to the list
            #self.ens.append(ens)

    def verify_ens_data(self, ens_bytes: list, ens_start: int = 0):
        """
        Get the ensemble number and the ensemble size.  Verify
        we have all the ensemble bytes in the buffer by comparing aginst
        the ensemble size.  Then check the checksum and verify it is correct.
        :param ens_bytes: Ensemble binary data.
        :param ens_start: Start location in the ens_data
        :return True if the ensemble is good and checksum passes.
        """
        try:
            # Ensemble Length
            ens_len = len(ens_bytes)

            # Verify at least the minimum number of bytes are available to verify the ensemble
            if ens_len <= self.HEADER_SIZE + self.CHECKSUM_SIZE:
                return False

            # Check Ensemble number
            ens_num = struct.unpack("I", ens_bytes[ens_start + 16:ens_start + 20])

            # Check ensemble size
            payload_size = struct.unpack("I", ens_bytes[ens_start + 24:ens_start + 28])

            # Ensure the entire ensemble is in the buffer
            if ens_len >= ens_start + self.HEADER_SIZE + payload_size[0] + self.CHECKSUM_SIZE:

                # Check checksum
                checksum_loc = ens_start + self.HEADER_SIZE + payload_size[0]
                checksum = struct.unpack("I", ens_bytes[checksum_loc:checksum_loc + self.CHECKSUM_SIZE])

                # Calculate Checksum
                # Use only the payload for the checksum
                ens = ens_bytes[ens_start + self.HEADER_SIZE:ens_start + self.HEADER_SIZE + payload_size[0]]
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

    def decode_data_sets(self, ens_bytes: list, use_pd0_format: bool = False):
        """
        Decode the datasets to an ensemble.
        Use verify_ens_data if you are using this
        as a static method to verify the data is correct.
        :param ens_bytes: Ensemble binary data.  Decode the dataset.
        :param use_pd0_format: Flag to decode and convert data to PD0 format.
        :return: Return the decoded ensemble.
        """
        packetPointer = self.HEADER_SIZE
        ens_len = len(ens_bytes)

        # Flag if BT data found
        bt_data_found = False
        bt_adcp3_data_found = False
        ancillary_adcp3_found = False

        # Create a new config and sensor object
        # Multiple datasets are needed to populate these objects
        cfg = Cfg(pd0_format=use_pd0_format)
        sensor = Sensor(pd0_format=use_pd0_format)

        # Decode the ensemble datasets
        # Limit the number of attempts to look for new datasets
        for x in range(self.MAX_DATASETS):
            # Check if we are at the end of the payload
            if packetPointer >= ens_len - RtbRowe.CHECKSUM_SIZE - RtbRowe.HEADER_SIZE:
                break

            # Get the dataset info
            ds_type = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 0), RtbRowe.BYTES_IN_INT32, ens_bytes)
            num_elements = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 1), RtbRowe.BYTES_IN_INT32, ens_bytes)
            element_multiplier = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 2), RtbRowe.BYTES_IN_INT32, ens_bytes)
            image = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 3), RtbRowe.BYTES_IN_INT32, ens_bytes)
            name_len = RtbRowe.get_int32(packetPointer + (RtbRowe.BYTES_IN_INT32 * 4), RtbRowe.BYTES_IN_INT32, ens_bytes)
            name = str(ens_bytes[packetPointer + (RtbRowe.BYTES_IN_INT32 * 5):packetPointer + (RtbRowe.BYTES_IN_INT32 * 5) + 8], 'UTF-8')

            # Calculate the dataset size
            data_set_size = RtbRowe.get_data_set_size(ds_type, name_len, num_elements, element_multiplier)

            # Beam Velocity
            if "E000001" in name:
                logging.debug(name)
                self.BeamVel.decode(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                    num_elements=num_elements,
                                    element_multiplier=element_multiplier,
                                    name_len=name_len)

            # Instrument Velocity
            if "E000002" in name:
                logging.debug(name)
                self.InstrVel.decode(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                     num_elements=num_elements,
                                     element_multiplier=element_multiplier,
                                     name_len=name_len)

            # Earth Velocity
            if "E000003" in name:
                logging.debug(name)
                self.EarthVel.decode(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                     num_elements=num_elements,
                                     element_multiplier=element_multiplier,
                                      name_len=name_len)

            # Amplitude
            if "E000004" in name:
                logging.debug(name)
                self.Amp.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                num_elements=num_elements,
                                element_multiplier=element_multiplier,
                                name_len=name_len)

            # Correlation
            if "E000005" in name:
                logging.debug(name)

                # Get code repeats for accurate conversion for PD0
                num_repeats = None
                if self.Cfg.wp_repeat_n and len(self.Cfg.wp_repeat_n):
                    pings_per_ens = self.Cfg.wp_repeat_n[-1]

                self.Corr.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                 num_elements=num_elements,
                                 element_multiplier=element_multiplier,
                                 num_repeats=num_repeats,
                                 name_len=name_len)

            # Good Beam
            if "E000006" in name:
                logging.debug(name)

                # Get the number of pings used in the ensemble
                pings_per_ens = 1
                if self.Cfg.actual_ping_count and len(self.Cfg.actual_ping_count):
                    pings_per_ens = self.Cfg.actual_ping_count[-1]

                self.GdB.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                num_elements=num_elements,
                                element_multiplier=element_multiplier,
                                pings_per_ens=pings_per_ens,
                                name_len=name_len)

            # Good Earth
            if "E000007" in name:
                logging.debug(name)

                # Get the number of pings used in the ensemble
                pings_per_ens = 1
                if self.Cfg.actual_ping_count and len(self.Cfg.actual_ping_count):
                    pings_per_ens = self.Cfg.actual_ping_count[-1]

                self.GdE.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                num_elements=num_elements,
                                element_multiplier=element_multiplier,
                                pings_per_ens=pings_per_ens,
                                name_len=name_len)

            # Ensemble Data
            if "E000008" in name:
                logging.debug(name)
                # Check if the Cfg is already created from other dataset
                # This will be added to the list at the end of all decoding
                self.Cfg.decode_ensemble_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                              name_len=name_len)

            # Ancillary Data
            if "E000009" in name:
                logging.debug(name)

                # Configuration data
                # Check if the Cfg is already created from other dataset
                # This will be added to the list at the end of all decoding
                self.Cfg.decode_ancillary_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                               name_len=name_len)

                # Sensor data
                # Check if the Sensor is already created from other dataset
                # This will be added to the list at the end of all decoding
                self.Sensor.decode_ancillary_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                  name_len=name_len)

                if num_elements > 19:
                    self.Sensor.decode_ancillary_adcp3_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                            name_len=name_len)
                    self.Cfg.decode_ancillary_adcp3_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                         name_len=name_len)
                    ancillary_adcp3_found = True

            # Bottom Track
            if "E000010" in name:
                logging.debug(name)
                # Populate Bottom Track data
                self.Bt.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                               name_len=name_len)
                bt_data_found = True

                # Populate Config data
                self.Cfg.decode_bottom_track_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                  name_len=name_len)

                # Populate Sensor data
                self.Sensor.decode_bottom_track_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                     name_len=name_len)

                # Check if ADCP 3 data is available
                # Number of elements.  74 for 4 Beam system, 59 for 3 beam, 29 for 1 beam
                if num_elements > 74:
                    self.Sensor.decode_bottom_track_adcp3_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                               name_len=name_len)
                    # Set flag that data found
                    bt_adcp3_data_found = True


            # NMEA data
            if "E000011" in name:
                logging.debug(name)
                self.Nmea.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                 name_len=name_len)

            # System Setup
            if "E000014" in name:
                logging.debug(name)
                # Configuration data
                # Check if the Cfg is already created from other dataset
                self.Cfg.decode_systemsetup_data(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                                 name_len=name_len)

                self.Sensor.decode_systemsetup_data(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                                    name_len=name_len)

            # Range Tracking
            if "E000015" in name:
                logging.debug(name)
                self.Rt.decode(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                               name_len=name_len)

            if "E000016" in name:
                logging.debug(name)
                self.Gage.decode_data(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                      name_len=name_len)

            if "R000001" in name:
                logging.debug(name)
                self.River_BT.decode_data(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                          name_len=name_len)

            if "R000002" in name:
                logging.debug(name)
                #RiverTimeStamp

            if "R000003" in name:
                logging.debug(name)
                #RiverNmea

            if "R000004" in name:
                logging.debug(name)
                #RiverBThump

            if "R000005" in name:
                logging.debug(name)
                #RiverStationID

            if "R000006" in name:
                logging.debug(name)
                #RiverTransectID

            # Move to the next dataset
            packetPointer += data_set_size

        # Check if Bottom Track data was never found
        # If not fill values with NAN
        if not bt_data_found and self.Cfg:
            self.Bt.empty_init(num_ens=len(self.Cfg.num_beams),
                               num_beams=self.Cfg.num_beams)
            self.Cfg.empty_bt_init(num_beams=len(self.Cfg.num_beams))
            self.Sensor.empty_bt_init(num_beams=len(self.Cfg.num_beams))

        if not bt_adcp3_data_found and self.Cfg:
            self.Sensor.empty_bt_adcp3_init(num_beams=len(self.Cfg.num_beams))

        if not ancillary_adcp3_found:
            self.Sensor.empty_ancillary_adcp3_init()
            self.Cfg.empty_ancillary_adcp3_init()

    @staticmethod
    def get_data_set_size(ds_type: int, name_len: int, num_elements: int, element_multiplier: int):
        """
        Get the dataset size.
        :param ds_type: Dataset type. (Int, float, ...)
        :param name_len: Length of the name.
        :param num_elements: Number of elements.
        :param element_multiplier: Element element multiplier.
        :return: Size of the dataset in bytes.
        """

        # Number of bytes in the data type
        datatype_size = 4
        if ds_type == 50:      # Byte Datatype
            datatype_size = 1
        elif ds_type == 20:    # Int Datatype
            datatype_size = 4
        elif ds_type == 10:    # Float Datatype
            datatype_size = 4

        return ((num_elements * element_multiplier) * datatype_size) + RtbRowe.get_base_data_size(name_len)

    @staticmethod
    def get_base_data_size(name_len: int):
        """
        Get the size of the header for a dataset.
        :param name_len: Length of the name.
        :return: Dataset header size in bytes.
        """
        return name_len + (RtbRowe.BYTES_IN_INT32 * (RtbRowe.NUM_DATASET_HEADER_ELEMENTS - 1))

    @staticmethod
    def is_float_close(a, b, rel_tol=1e-06, abs_tol=0.0):
        """
        Check if the float values are the same.
        :param a: First float value
        :param b: Second float value
        :param rel_tol: Value within this
        :param abs_tol: Absolute value within this
        :return:
        """
        return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

    @staticmethod
    def is_bad_velocity(vel):
        """
        Check if the velocity given is good or bad.
        :param vel: Velocity value to check.
        :return: True if Bad Velocity.
        """
        if vel >= RtbRowe.BAD_VEL:
            return True
        if RtbRowe.is_float_close(vel, RtbRowe.BAD_VEL):
            return True
        if vel is None:
            return True

        return False

    @staticmethod
    def get_int32(start: int, num_bytes: int, ens_bytes: list):
        """
        Convert the bytes given into an Int32.
        This will look in the ens given.
        :param start: Start location in the ens_bytes.
        :param num_bytes: Number of bytes in the int32.
        :param ens_bytes: Buffer containing the bytearray data.
        :return: Int32 of the data in the buffer.
        """
        try:
            return struct.unpack("i", ens_bytes[start:start + num_bytes])[0]
        except Exception as e:
            logging.error("Error creating a Int32 from bytes. " + str(e))
            return 0

    @staticmethod
    def get_float(start: int, num_bytes: int, ens: list):
        """
        Convert the bytes given into an int32.
        This will look in the ens given.
        :param start: Start location.
        :param num_bytes: Number of bytes in the float.
        :param ens: Buffer containing the bytearray data.
        :return: Float of the data in the buffer.
        """
        try:
            return struct.unpack("f", ens[start:start + num_bytes])[0]
        except Exception as e:
            logging.debug("Error creating a float from bytes. " + str(e))
            return 0.0

    @staticmethod
    def nans(num_ens: int):
        """
        Create a numpy array filled with NaN based on the number of
        ensembles given.
        @param num_ens: Number of ensembles
        """
        empty_arr = np.empty(num_ens, dtype=float)
        empty_arr.fill(np.nan)
        return empty_arr


class BeamVelocity:
    """
    Beam Velocity.
    Velocity data in the Beam Coordinate Transform. (Raw Velocity Data)
    """
    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the velocity scale will be mm/s instead of m/s.
        RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.vel = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8):
        """
        Decode the ensemble data for the Beam velocity.

        Initialize the list of velocity data.  [beam][bin]

        If PD0 format is selected, then change the beam order and scale to match PD0.
        RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1

        RTB is m/s
        PD0 is mm/s
        RTB Bad Value is 88.888
        PD0 Bad Value is -32768

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        #for beam in range(element_multiplier):
        #    self.vel[beam].append([None] * num_elements)
        if not self.pd0_format:
            vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    # Use the original value
                    vel[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Get the velocity data
                    pd0_vel = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

                    # Check for bad velocity and convert
                    if RtbRowe.is_bad_velocity(pd0_vel):
                        pd0_vel = RtbRowe.PD0_BAD_VEL
                    else:
                        # Convert from m/s to mm/s
                        pd0_vel = round(pd0_vel * 1000.0)

                    # Set the velocity based on the beam reassignment
                    if element_multiplier == 1:             # Vertical Beam
                        vel[0][bin_num] = pd0_vel
                    elif beam == 0:                         # RTB 0 - PD0 3
                        vel[3][bin_num] = pd0_vel
                    elif beam == 1:                         # RTB 1 - PD0 2
                        vel[2][bin_num] = pd0_vel
                    elif beam == 2:                         # RTB 2 - PD0 0
                        vel[0][bin_num] = pd0_vel
                    elif beam == 3:                         # RTB 3 - PD0 1
                        vel[1][bin_num] = pd0_vel

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_FLOAT

        # Add the ensemble to the list
        self.vel.append(vel)


class InstrVelocity:
    """
    Instrument Velocity.
    Velocity data in the Instrument Coordinate Transform.
    """

    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the velocity scale will be mm/s instead of m/s.
        RTB BEAM 0,1,2,3 = PD0 XYZ order 1,0,-2,3

        RTB is m/s
        PD0 is mm/s
        RTB Bad Value is 88.888
        PD0 Bad Value is -32768

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.vel = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8):
        """
        Decode the ensemble data for the Instrument velocity.

        Initialize the list of velocity data.  [beam][bin]

        If PD0 format is selected, then change the beam order and scale to match PD0.
        RTB BEAM 0,1,2,3 = PD0 XYZ order 1,0,-2,3

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    vel[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Get the velocity data
                    pd0_vel = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

                    # Check for bad velocity and convert
                    if RtbRowe.is_bad_velocity(pd0_vel):
                        pd0_vel = RtbRowe.PD0_BAD_VEL
                    else:
                        # Convert from m/s to mm/s
                        pd0_vel = round(pd0_vel * 1000.0)

                    # Set the velocity based on the beam reassignment
                    if element_multiplier == 1:                     # Vertical Beam
                        vel[0][bin_num] = pd0_vel
                    elif beam == 0:                                 # RTB 0 - PD0 1
                        vel[1][bin_num] = pd0_vel
                    elif beam == 1:                                 # RTB 1 - PD0 0
                        vel[0][bin_num] = pd0_vel
                    elif beam == 2:                                 # RTB 2 - PD0 -2
                        if pd0_vel != RtbRowe.PD0_BAD_VEL:
                            vel[2][bin_num] = pd0_vel * -1.0
                        else:
                            vel[2][bin_num] = pd0_vel
                    elif beam == 3:                                 # RTB 3 - PD0 3
                        vel[3][bin_num] = pd0_vel

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_FLOAT

        # Add the data to the lsit
        self.vel.append(vel)


class EarthVelocity:
    """
    Earth Velocity.
    Velocity data in the Earth Coordinate Transform.
    """

    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the velocity scale will be mm/s instead of m/s.
        RTB BEAM 0,1,2,3 = PD0 ENU order 0,1,2,3

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.vel = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8):
        """
        Decode the ensemble data for the Earth velocity.

        Initialize the list of velocity data.  [beam][bin]

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    vel[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Get the velocity data
                    pd0_vel = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

                    # Check for bad velocity and convert
                    if RtbRowe.is_bad_velocity(pd0_vel):
                        pd0_vel = RtbRowe.PD0_BAD_VEL
                    else:
                        # Convert from m/s to mm/s
                        pd0_vel = round(pd0_vel * 1000.0)

                    # Set the values
                    # No reassignment needed
                    vel[beam][bin_num] = pd0_vel

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_FLOAT

        # Add the data to the list
        self.vel.append(vel)


class Amplitude:
    """
    Amplitude.
    Amplitude data which reports signal strength.
    Amplitude values range from 0 dB - 140 dB.
    Values below 25dB is considered noise.  The noise floor
    with systems with high EMI can be as a 40dB.
    """
    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the scale will change from dB to counts. 0.5 dB per Count.
        RTB BEAM 0,1,2,3 = PD0 Amp 3,2,0,1

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.amp = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8):
        """
        Decode the ensemble data for the Amplitude data.

        Initialize the list of amplitude data.  [beam][bin]

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            amp = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            amp = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    amp[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Get the dB and convert to counts
                    pd0_amp = round(RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 2.0)

                    # Beam Reassignment
                    if element_multiplier == 1:                 # Vertical Beam
                        amp[beam][bin_num] = pd0_amp
                    elif beam == 0:                               # RTB 0 - PD0 3
                        amp[3][bin_num] = pd0_amp
                    elif beam == 1:                             # RTB 1 - PD0 2
                        amp[2][bin_num] = pd0_amp
                    elif beam == 2:                             # RTB 2 - PD0 0
                        amp[0][bin_num] = pd0_amp
                    elif beam == 3:                             # RTB 3 - PD0 1
                        amp[1][bin_num] = pd0_amp

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_FLOAT

        # Add data to the list
        self.amp.append(amp)


class Correlation:
    """
    Correlation data which reports data quality.
    Value is reported as a percentage 0% - 100%.
    Values below 25% are considered bad or noise.

    If using PD0, values are between 0-255 counts.
    """
    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the scale will change from percentage to counts.
        The value has to be converted from percentage to 0-255
        Scale 0%-100% to 0-255
        255 = 100%
        0   =   0%
        50% = 0.50 * 255 = 127.5 = 255/2

        RTB BEAM 0,1,2,3 = PD0 Corr 3,2,0,1

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.corr = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8, num_repeats: int = None):
        """
        Decode the ensemble data for the Correlation data.

        Initialize the list of correlation data.  [beam][bin]

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        :param num_repeats: Only used when converting to PD0 format.  Accurately converts to counts.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            corr = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            corr = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    corr[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Verify a number of code repeats is given
                    if num_repeats:
                        # Verify a good value for num_repeats
                        if num_repeats == 0:
                            num_repeats = 1

                        # Calculate code repeats used
                        repeats = (num_repeats - 1.0) / num_repeats
                        if repeats == 0.0:
                            repeats = 1.0

                        # Get the correlation percentage and convert to counts
                        pd0_corr = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 128.0
                        pd0_corr = round(pd0_corr / repeats)
                    else:
                        # If no repeats given, use this calculation
                        pd0_corr = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 255.0

                    # Beam Reassignment
                    if element_multiplier == 1:                 # Vertical Beam
                        corr[beam][bin_num] = RtbRowe.get_float(packet_pointer, RtbRowe.BYTES_IN_FLOAT, ens_bytes) * 255.0
                    elif beam == 0:                               # RTB 0 - PD0 3
                        corr[3][bin_num] = pd0_corr
                    elif beam == 1:                             # RTB 1 - PD0 2
                        corr[2][bin_num] = pd0_corr
                    elif beam == 2:                             # RTB 2 - PD0 0
                        corr[0][bin_num] = pd0_corr
                    elif beam == 3:                             # RTB 3 - PD0 1
                        corr[1][bin_num] = pd0_corr

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_FLOAT

        # Add data to the list
        self.corr.append(corr)


class GoodBeam:
    """
    Good Beam Pings.  This give a number of pings
    that were used when averaging pings together.
    This will give a number of pings, so you will
    need to look at the settings to know the actual number
    of pings attempted.

    If using PD0, values are in percentage.
    """

    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the scale will change from the number of pings to percentage good.

        RTB GoodBeam 0,1,2,3 = PD0 GoodBeam 3,2,0,1

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.pings = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8, pings_per_ens: int = 1):
        """
        Decode the ensemble data for the Good Beam Ping data.

        Initialize the list of Good Beam data.  [beam][bin]

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        :param pings_per_ens: Only used when converting to PD0 format.  Number of pings in the ensemble
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)
        else:
            pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    pings[beam][bin_num] = RtbRowe.get_int32(packet_pointer, RtbRowe.BYTES_IN_INT32, ens_bytes)
                else:
                    # Verify a good value for pings_per_ens
                    if pings_per_ens == 0:
                        pings_per_ens = 1

                    # Get the Good Beam number of good pings and convert to percentage
                    pd0_gb = round((RtbRowe.get_int32(packet_pointer, RtbRowe.BYTES_IN_INT32, ens_bytes) * 100) / pings_per_ens)

                    # Beam Reassignment
                    if element_multiplier == 1:                 # Vertical Beam
                        pings[beam][bin_num] = pd0_gb
                    elif beam == 0:                               # RTB 0 - PD0 3
                        pings[3][bin_num] = pd0_gb
                    elif beam == 1:                             # RTB 1 - PD0 2
                        pings[2][bin_num] = pd0_gb
                    elif beam == 2:                             # RTB 2 - PD0 0
                        pings[0][bin_num] = pd0_gb
                    elif beam == 3:                             # RTB 3 - PD0 1
                        pings[1][bin_num] = pd0_gb

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_INT32

        # Add data to the list
        self.pings.append(pings)


class GoodEarth:
    """
    Good Earth Pings.  This give a number of pings
    that were used when averaging pings together.
    This will give a number of pings, so you will
    need to look at the settings to know the actual number
    of pings attempted.

    If using PD0, values are in percentage.
    """

    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the scale will change from the number of pings to percentage good.

        RTB GoodEarth 0,1,2,3 = PD0 GoodEarth 0,1,2,3

        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.pings = []
        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, num_elements: int, element_multiplier: int, name_len: int = 8, pings_per_ens: int = 1):
        """
        Decode the ensemble data for the Good Earth Ping data.

        Initialize the list of Good Beam data.  [beam][bin]

        :param ens_bytes: Byte array containing the ensemble data.
        :param element_multiplier: Number of beams.
        :param num_elements; Number of bins.
        :param name_len: Length of the name of the dataset.
        :param pings_per_ens: Only used when converting to PD0 format.  Number of pings in the ensemble
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)
        else:
            pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    pings[beam][bin_num] = RtbRowe.get_int32(packet_pointer, RtbRowe.BYTES_IN_INT32, ens_bytes)
                else:
                    # Verify a good value for pings_per_ens
                    if pings_per_ens == 0:
                        pings_per_ens = 1

                    # Get the Good Earth number of good pings and convert to percentage
                    # No reassignment needed
                    pings[beam][bin_num] = round((RtbRowe.get_int32(packet_pointer, RtbRowe.BYTES_IN_INT32, ens_bytes) * 100) / pings_per_ens)

                # Move the pointer
                packet_pointer += RtbRowe.BYTES_IN_INT32

        # Add data to the list
        self.pings.append(pings)


class Cfg:
    """
    System configuration data is all the data that describes the ADCP configuration and date and time.
    This includes the bin size, blank and number of bins, the ensemble number, date and time.
    """

    def __init__(self, pd0_format: bool = False):
        """
        Initialize all the values
        Set the flag if using PD0 format data.  This will change the year from 2000+ date to year-2000


        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.pd0_format = pd0_format

        self.ens_num = []                    # Ensemble number
        self.num_bins = []                   # Number of bins
        self.num_beams = []                  # Number of beams
        self.desired_ping_count = []         # Avg Ping Count configured in seconds
        self.actual_ping_count = []          # Avg Ping Count actually output in seconds
        self.serial_num = []                # Serial Number
        self.firm_major = []                 # Firmware Major Number
        self.firm_minor = []                 # Firmware Minor Number
        self.firm_rev = []                   # Firmware Revision
        self.subsystem_code = []            # Subsystem Code (Indentifier of frequency and orientation)
        self.subsystem_config = []           # Subsystem Config.  System allows multiple configures of the same frequency.  This identifies each configuration
        self.status = []                     # Status code
        self.year = []                       # Year
        self.month = []                      # Month
        self.day = []                        # Day
        self.hour = []                       # Hour
        self.minute = []                     # Minute
        self.second = []                     # Second
        self.hsec = []                       # Hundredth Second

        # ADCP 3 values
        self.current_system = []
        self.status_2 = []
        self.burst_index = []

        self.blank = []                    # Blank.  Depth to the first bin in meters.
        self.bin_size = []                 # Size of a bin in meters.
        self.first_ping_time = []          # First Ping Time in seconds.
        self.last_ping_time = []           # Last Ping Time in seconds. (If averaging pings, this will be the last ping)
        self.salinity = []                 # Water Salinity set by the user in PPT
        self.speed_of_sound = []           # Speed of Sound in m/s.

        self.bt_first_ping_time = []
        self.bt_last_ping_time = []
        self.bt_speed_of_sound = []
        self.bt_status = []
        self.bt_num_beams = []
        self.bt_actual_ping_count = []

        self.bt_samples_per_second = []    # Bottom Track Samples Per Second
        self.bt_system_freq_hz = []        # Bottom Track System Frequency (Hz)
        self.bt_cpce = []                  # Bottom Track Cycles per Code Elements
        self.bt_nce = []                   # Bottom Track Number of Code Elements
        self.bt_repeat_n = []              # Bottom Track Number of Code Repeats
        self.wp_samples_per_second = []    # Water Profile Samples per Second
        self.wp_system_freq_hz = []        # Water Profile System Frequency (Hz)
        self.wp_cpce = []                  # Water Profile Cycles per Code Element
        self.wp_nce = []                   # Water Profile Number of Code Element
        self.wp_repeat_n = []              # Water Profile Number of Code Repeats
        self.wp_lag_samples = []           # Water Profile Lag Samples
        self.bt_broadband = []             # Bottom Track Broadband
        self.bt_lag_length = []            # Bottom Track Pulse to Pulse Lag (m)
        self.bt_narrowband = []            # Bottom Track Long Range Switch Depth (m)
        self.bt_beam_mux = []              # Bottom Track Beam Multiplex
        self.wp_broadband = []             # Water Profile Mode
        self.wp_lag_length = []            # Water Profile Lag Length
        self.wp_transmit_bandwidth = []    # Water Profile Transmit Bandwidth
        self.wp_receive_bandwidth = []     # Water Profile Receive Bandwidth
        self.wp_beam_mux = []              # WP Beam Mux

    def decode_ensemble_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ensemble data for the configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.ens_num.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 0, RtbRowe.BYTES_IN_INT32, ens_bytes))
        self.num_bins.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 1, RtbRowe.BYTES_IN_INT32, ens_bytes))
        self.num_beams.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 2, RtbRowe.BYTES_IN_INT32, ens_bytes))
        self.desired_ping_count.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 3, RtbRowe.BYTES_IN_INT32, ens_bytes))
        self.actual_ping_count.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 4, RtbRowe.BYTES_IN_INT32, ens_bytes))
        self.status.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 5, RtbRowe.BYTES_IN_INT32, ens_bytes))
        #self.year.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 6, RtbRowe.BYTES_IN_INT32, ens_bytes))
        self.month.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 7, RtbRowe.BYTES_IN_INT32, ens_bytes))
        self.day.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 8, RtbRowe.BYTES_IN_INT32, ens_bytes))
        self.hour.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 9, RtbRowe.BYTES_IN_INT32, ens_bytes))
        self.minute.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 10, RtbRowe.BYTES_IN_INT32, ens_bytes))
        self.second.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 11, RtbRowe.BYTES_IN_INT32, ens_bytes))
        self.hsec.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 12, RtbRowe.BYTES_IN_INT32, ens_bytes))

        self.serial_num.append(str(ens_bytes[packet_pointer + RtbRowe.BYTES_IN_INT32 * 13:packet_pointer + RtbRowe.BYTES_IN_INT32 * 21], "UTF-8"))
        self.firm_rev.append(struct.unpack("B", ens_bytes[packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 0:packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 1])[0])
        self.firm_minor.append(struct.unpack("B", ens_bytes[packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 1:packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 2])[0])
        self.firm_major.append(struct.unpack("B", ens_bytes[packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 2:packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 3])[0])
        self.subsystem_code.append(str(ens_bytes[packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 3:packet_pointer + RtbRowe.BYTES_IN_INT32 * 21 + 4], "UTF-8"))

        self.subsystem_config.append(struct.unpack("B", ens_bytes[packet_pointer + RtbRowe.BYTES_IN_INT32 * 22 + 3:packet_pointer + RtbRowe.BYTES_IN_INT32 * 22 + 4])[0])

        if self.pd0_format:
            year = RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 6, RtbRowe.BYTES_IN_INT32, ens_bytes)
            self.year.append(year - 2000)
        else:
            self.year.append(RtbRowe.get_int32(packet_pointer + RtbRowe.BYTES_IN_INT32 * 6, RtbRowe.BYTES_IN_INT32, ens_bytes))

    def decode_ancillary_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ancillary data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.blank.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bin_size.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.first_ping_time.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.last_ping_time.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        if self.pd0_format:
            salinity = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            sos = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            self.salinity.append(round(salinity))
            self.speed_of_sound.append(round(sos))
        else:
            self.salinity.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            self.speed_of_sound.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def decode_ancillary_adcp3_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ancillary data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.current_system.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.status_2.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.burst_index.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def decode_systemsetup_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the system setup data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.bt_samples_per_second.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_system_freq_hz.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_cpce.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_nce.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_repeat_n.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.wp_samples_per_second.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.wp_system_freq_hz.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.wp_cpce.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.wp_nce.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.wp_repeat_n.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.wp_lag_samples.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_broadband.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_lag_length.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_narrowband.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_beam_mux.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.wp_broadband.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.wp_lag_length.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.wp_transmit_bandwidth.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 19, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.wp_receive_bandwidth.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 20, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.wp_beam_mux.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 22, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def decode_bottom_track_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the system Bottom Track data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.bt_first_ping_time.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_last_ping_time.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_speed_of_sound.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_status.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_num_beams.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_actual_ping_count.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def empty_bt_init(self, num_beams: int):
        """
        Set the list with NAN for all missing Bottom Track data.
        :param num_beams Number of beams.
        """
        self.bt_first_ping_time.append(RtbRowe.nans(num_beams))
        self.bt_last_ping_time.append(RtbRowe.nans(num_beams))
        self.bt_speed_of_sound.append(RtbRowe.nans(num_beams))
        self.bt_status.append(RtbRowe.nans(num_beams))
        self.bt_num_beams.append(RtbRowe.nans(num_beams))
        self.bt_actual_ping_count.append(RtbRowe.nans(num_beams))

    def empty_ancillary_adcp3_init(self):
        """
        If no Ancillary ADCP3 data is given,
        fill in the arrays with NaN values.
        """
        self.current_system.append(np.NaN)
        self.status_2.append(np.NaN)
        self.burst_index.append(np.NaN)


class Sensor:
    """
    System sensor data is all the data from the sensors within the ADCP.  This includes compass and
    temperature sensor.
    """

    def __init__(self, pd0_format: bool = False):
        """
        Initialize all the values

        Set the flag if using PD0 format data.  This will change the scale of the pressure sensor and orientation
        of the roll value.


        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.pd0_format = pd0_format

        self.heading = []                          # Heading in degrees.
        self.pitch = []                            # Pitch in degrees.
        self.roll = []                             # Roll in degrees.
        self.water_temp = []                       # Water Temperature in fahrenheit
        self.system_temp = []                      # System Temperature in fahrenheit

        self.pressure = []                         # Pressure from pressure sensor in Pascals
        self.transducer_depth = []                 # Transducer Depth, used by Pressure sensor in meters

        self.voltage = []                          # Voltage input to ADCP
        self.xmt_voltage = []                      # Transmit Voltage
        self.transmit_boost_neg_volt = []          # Transmitter Boost Negative Voltage

        self.raw_mag_field_strength = []           # Raw magnetic field strength (uT) (micro Tesla)
        self.raw_mag_field_strength2 = []          # Raw magnetic field strength (uT) (micro Tesla)
        self.raw_mag_field_strength3 = []          # Raw magnetic field strength (uT) (micro Tesla)
        self.pitch_gravity_vec = []                # Pitch Gravity Vector
        self.roll_gravity_vec = []                 # Roll Gravity Vector
        self.vertical_gravity_vec = []             # Vertical Gravity Vector

        self.bt_heading = []
        self.bt_pitch = []
        self.bt_roll = []
        self.bt_water_temp = []
        self.bt_system_temp = []
        self.bt_salinity = []
        self.bt_pressure = []
        self.bt_transducer_depth = []

        # ADCP 3 Values
        self.hs1_temp = []
        self.hs2_temp = []
        self.rcv1_temp = []
        self.rcv2_temp = []
        self.vinf = []
        self.vg = []
        self.vt = []
        self.vtl = []
        self.d3v3 = []
        self.bt_hs1_temp = []
        self.bt_hs2_temp = []
        self.bt_rcv1_temp = []
        self.bt_rcv2_temp = []
        self.bt_vinf = []
        self.bt_vg = []
        self.bt_vt = []
        self.bt_vtl = []
        self.bt_d3v3 = []
        self.bt_sounder_range = []
        self.bt_sounder_snr = []
        self.bt_sounder_amp = []

    def decode_systemsetup_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the system setup data for the Sensor data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.voltage.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.xmt_voltage.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.transmit_boost_neg_volt.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 21, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def decode_ancillary_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ancillary data for the Sensor data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.heading.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.pitch.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        self.water_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.system_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        self.raw_mag_field_strength.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.raw_mag_field_strength2.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.raw_mag_field_strength3.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.pitch_gravity_vec.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.roll_gravity_vec.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.vertical_gravity_vec.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        # Convert values to PD0 format if selected
        if self.pd0_format:
            roll = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            if roll > 90.0:
                self.roll.append(-1 * (180.0 - roll))
            elif roll < -90.0:
                self.roll.append(180.0 + roll)

            pressure = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            transducer_depth = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            self.pressure.append(round(pressure * 0.0001))
            self.transducer_depth.append(round(transducer_depth * 10.0))
        else:
            self.roll.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            self.pressure.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            self.transducer_depth.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def decode_ancillary_adcp3_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ancillary ADCP3 data for the Sensor data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.hs1_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.hs2_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.rcv1_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.rcv2_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.vinf.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.vg.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.vt.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.vtl.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.d3v3.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def empty_ancillary_adcp3_init(self):
        """
        Initialize the array with NaN if no value is given.
        """
        self.hs1_temp.append(np.NaN)
        self.hs2_temp.append(np.NaN)
        self.rcv1_temp.append(np.NaN)
        self.rcv2_temp.append(np.NaN)
        self.vinf.append(np.NaN)
        self.vg.append(np.NaN)
        self.vt.append(np.NaN)
        self.vtl.append(np.NaN)
        self.d3v3.append(np.NaN)

    def decode_bottom_track_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the bottom track data for the Sensor data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.bt_heading.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_pitch.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_water_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_system_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_salinity.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        # Convert values to PD0 format if selected
        if self.pd0_format:
            bt_roll = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            if bt_roll > 90.0:
                self.bt_roll.append(-1 * (180.0 - bt_roll))
            elif bt_roll < -90.0:
                self.bt_roll.append(180.0 + bt_roll)

            bt_pressure = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            bt_transducer_depth = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            self.bt_pressure = round(bt_pressure * 0.0001)
            self.bt_transducer_depth = round(bt_transducer_depth * 10.0)
        else:
            self.bt_roll.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            self.bt_pressure.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            self.bt_transducer_depth.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def decode_bottom_track_adcp3_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the bottom track ADCP3 data for the Sensor data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Get the number of beams
        num_beams = int(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        # 14 raw values plus 15 values for each beam
        data_index = 14 + (15 * num_beams)

        self.bt_hs1_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 1), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_hs2_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 2), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_rcv1_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 3), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_rcv2_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 4), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_vinf.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 5), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_vg.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 6), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_vt.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 7), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_vtl.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 8), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_d3v3.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 9), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_sounder_range.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 11), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_sounder_snr.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 12), RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.bt_sounder_amp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * (data_index + 13), RtbRowe.BYTES_IN_FLOAT, ens_bytes))

    def empty_bt_init(self, num_beams: int):
        """
        Set the list with NAN for all missing Bottom Track data.
        :param num_beams Number of ensembles.
        """
        self.bt_heading.append(np.NaN)
        self.bt_pitch.append(np.NaN)
        self.bt_roll.append(np.NaN)
        self.bt_water_temp.append(np.NaN)
        self.bt_system_temp.append(np.NaN)
        self.bt_salinity.append(np.NaN)
        self.bt_pressure.append(np.NaN)
        self.bt_transducer_depth.append(np.NaN)

    def empty_bt_adcp3_init(self, num_beams: int):
        """
        If now Bottom Track ADCP3 data is given,
        fill in the arrays with NaN values.
        :param num_beams Number of beams.
        """
        self.bt_hs1_temp.append(np.NaN)
        self.bt_hs2_temp.append(np.NaN)
        self.bt_rcv1_temp.append(np.NaN)
        self.bt_rcv2_temp.append(np.NaN)
        self.bt_vinf.append(np.NaN)
        self.bt_vg.append(np.NaN)
        self.bt_vt.append(np.NaN)
        self.bt_vtl.append(np.NaN)
        self.bt_d3v3.append(np.NaN)
        self.bt_sounder_range.append(np.NaN)
        self.bt_sounder_snr.append(np.NaN)
        self.bt_sounder_amp.append(np.NaN)


class BT:
    """
    Bottom Tracking used to measure the depth and vessel speed (Speed over Ground).
    """
    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the scale will change from percentage to counts.
        The value has to be converted from
        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.num_beams = 0
        self.depth = []
        self.snr = []
        self.amp = []
        self.corr = []
        self.beam_vel = []
        self.beam_good = []
        self.instr_vel = []
        self.instr_good = []
        self.earth_vel = []
        self.earth_good = []
        self.pulse_coh_snr = []
        self.pulse_coh_amp = []
        self.pulse_coh_vel = []
        self.pulse_coh_noise = []
        self.pulse_coh_corr = []

        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ensemble data for the Bottom Traack data.

        Initialize the list of Bottom Track data.  [beam]

        :param ens_bytes: Byte array containing the Bottom Track data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Get the number of beams
        self.num_beams = int(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        # Get the ping count
        # Value stored in Cfg but needed for conversion to PD0
        bt_actual_ping_count = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

        # Initialize the array
        snr = np.empty(shape=[self.num_beams], dtype=np.float)
        depth = np.empty(shape=[self.num_beams], dtype=np.float)
        amp = np.empty(shape=[self.num_beams], dtype=np.float)
        corr = np.empty(shape=[self.num_beams], dtype=np.float)
        beam_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        beam_good = np.empty(shape=[self.num_beams], dtype=np.int)
        instr_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        instr_good = np.empty(shape=[self.num_beams], dtype=np.int)
        earth_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        earth_good = np.empty(shape=[self.num_beams], dtype=np.int)
        pulse_coh_snr = np.empty(shape=[self.num_beams], dtype=np.float)
        pulse_coh_amp = np.empty(shape=[self.num_beams], dtype=np.float)
        pulse_coh_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        pulse_coh_noise = np.empty(shape=[self.num_beams], dtype=np.float)
        pulse_coh_corr = np.empty(shape=[self.num_beams], dtype=np.float)

        index = 14
        # Range Values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                depth[beam] = value
            else:
                # PD0 data
                # Check for bad velocity and convert
                if RtbRowe.is_bad_velocity(value):
                    value = RtbRowe.PD0_BAD_VEL
                else:
                    # Convert from m to cm
                    value = round(value * 100.0)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:
                    depth[0] = value
                if beam == 0:
                    depth[3] = value
                elif beam == 1:
                    depth[2] = value
                elif beam == 2:
                    depth[0] = value
                elif beam == 3:
                    depth[1] = value

            # Increment for the next beam
            index += 1

        # Add the data to the list
        self.depth.append(depth)

        # SNR values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                snr[beam] = value
            else:
                # PD0 data
                # Convert from db to counts (0.5 counts per dB)
                value = round(value * 2.0)

                # Check for bad value
                if value > RtbRowe.PD0_BAD_AMP:
                    value = RtbRowe.PD0_BAD_AMP

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:
                    snr[0] = value
                elif beam == 0:
                    snr[3] = value
                elif beam == 1:
                    snr[2] = value
                elif beam == 2:
                    snr[0] = value
                elif beam == 3:
                    snr[1] = value

            # Increment for the next beam
            index += 1

        # Add the data to the list
        self.snr.append(snr)

        # Amplitude values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                amp[beam] = value
            else:
                # PD0 data
                # Convert from db to counts (0.5 counts per dB)
                value = round(value * 2.0)

                # Check for bad value
                if value > RtbRowe.PD0_BAD_AMP:
                    value = RtbRowe.PD0_BAD_AMP

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:
                    amp[0] = value
                elif beam == 0:
                    amp[3] = value
                elif beam == 1:
                    amp[2] = value
                elif beam == 2:
                    amp[0] = value
                elif beam == 3:
                    amp[1] = value

            # Increment for the next beam
            index += 1

        # Add the data to the list
        self.amp.append(amp)

        # Correlation values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                corr[beam] = value
            else:
                # PD0 data
                # Convert from percentage to 0-255 counts
                value = round(value * 255.0)

                # Check for bad value
                if value > RtbRowe.PD0_BAD_AMP:
                    value = RtbRowe.PD0_BAD_AMP

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:             # Vertical beam
                    corr[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 3
                    corr[3] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 2
                    corr[2] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 0
                    corr[0] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 1
                    corr[1] = value

            # Increment for the next beam
            index += 1

        # Add the data to the list
        self.corr.append(corr)

        # Beam Velocity values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            # Check for bad velocity and convert
            if RtbRowe.is_bad_velocity(value):
                value = np.nan

            if not self.pd0_format:
                # Store RTB data
                beam_vel[beam] = value
            else:
                # PD0 data
                # Check for bad velocity and convert
                if not np.isnan(value):
                    # Convert from m/s to mm/s
                    # Also invert the direction
                    value = round(value * 1000.0 * -1)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:             # Vertical beam
                    beam_vel[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 3
                    beam_vel[3] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 2
                    beam_vel[2] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 0
                    beam_vel[0] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 1
                    beam_vel[1] = value

            # Increment for the next beam
            index += 1

        # Add the data to the list
        self.beam_vel.append(beam_vel)

        # Beam Good Pings values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                beam_good[beam] = int(value)
            else:
                # PD0 data
                # Check for bad velocity and convert
                if RtbRowe.is_bad_velocity(value):
                    value = RtbRowe.PD0_BAD_VEL
                else:
                    # Convert from number of good pings to a percentage of good pings
                    value = round((value * 100.0) / bt_actual_ping_count)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:             # Vertical beam
                    beam_good[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 3
                    beam_good[3] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 2
                    beam_good[2] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 0
                    beam_good[0] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 1
                    beam_good[1] = value

            # Increment for the next beam
            index += 1

        # Add the data to the list
        self.beam_good.append(beam_good)

        # Instrument Velocity values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            # Check for bad velocity and convert
            if RtbRowe.is_bad_velocity(value):
                value = np.nan

            if not self.pd0_format:
                # Store RTB data
                instr_vel[beam] = value
            else:
                # PD0 data
                # Check for bad velocity and convert
                if not np.isnan(value):
                    # Convert from m/s to mm/s
                    # Also invert the direction
                    value = round(value * 1000.0 * -1)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 XYZ order 1,0,-2,3
                if self.num_beams == 1:             # Vertical beam
                    instr_vel[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 1
                    instr_vel[1] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 0
                    instr_vel[0] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam -2
                    instr_vel[2] = value * -1.0
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 3
                    instr_vel[3] = value

            # Increment for the next beam
            index += 1

        # Add the data to the list
        self.instr_vel.append(instr_vel)

        # Instrument Good Pings values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                instr_good[beam] = int(value)
            else:
                # PD0 data
                # Check for bad velocity and convert
                if RtbRowe.is_bad_velocity(value):
                    value = RtbRowe.PD0_BAD_VEL
                else:
                    # Convert from number of good pings to a percentage of good pings
                    value = round((value * 100.0) / bt_actual_ping_count)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 XYZ order 1,0,-2,3
                if self.num_beams == 1:             # Vertical beam
                    instr_good[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 1
                    instr_good[1] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 0
                    instr_good[0] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam -2
                    instr_good[2] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 3
                    instr_good[3] = value

            # Increment for the next beam
            index += 1

        # Add the data to the list
        self.instr_good.append(instr_good)

        # Earth Velocity values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            # Check for bad velocity and convert
            if RtbRowe.is_bad_velocity(value):
                value = np.nan

            if not self.pd0_format:
                # Store RTB data
                earth_vel[beam] = value
            else:
                # PD0 data
                # Check for bad velocity and convert
                if not np.isnan(value):
                    # Convert from m/s to mm/s
                    # Also invert the direction
                    value = round(value * 1000.0 * -1)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:             # Vertical beam
                    earth_vel[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 0
                    earth_vel[0] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 1
                    earth_vel[1] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 2
                    earth_vel[2] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 3
                    earth_vel[3] = value

            # Increment for the next beam
            index += 1

        # Add the data to the list
        self.earth_vel.append(earth_vel)

        # Earth Good Pings values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                earth_good[beam] = int(value)
            else:
                # PD0 data
                # Check for bad velocity and convert
                if RtbRowe.is_bad_velocity(value):
                    value = RtbRowe.PD0_BAD_VEL
                else:
                    # Convert from number of good pings to a percentage of good pings
                    value = round((value * 100.0) / bt_actual_ping_count)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 XYZ order 0,1,2,3
                if self.num_beams == 1:             # Vertical beam
                    earth_good[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 0
                    earth_good[0] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 1
                    earth_good[1] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 2
                    earth_good[2] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 3
                    earth_good[3] = value

            # Increment for the next beam
            index += 1

        # Add the data to the list
        self.earth_good.append(earth_good)

        # Pulse Coherent SNR values
        for beam in range(self.num_beams):
            pulse_coh_snr[beam] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            index += 1
        self.pulse_coh_snr.append(pulse_coh_snr)

        # Pulse Coherent Amplitude values
        for beam in range(self.num_beams):
            pulse_coh_amp[beam] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            index += 1
        self.pulse_coh_amp.append(pulse_coh_amp)

        # Pulse Coherent Velocity values
        for beam in range(self.num_beams):
            pulse_coh_vel[beam] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            index += 1
        self.pulse_coh_vel.append(pulse_coh_vel)

        # Pulse Coherent Noise values
        for beam in range(self.num_beams):
            pulse_coh_noise[beam] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            index += 1
        self.pulse_coh_noise.append(pulse_coh_noise)

        # Pulse Coherent Correlation values
        for beam in range(self.num_beams):
            pulse_coh_corr[beam] = RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes)
            index += 1
        self.pulse_coh_corr.append(pulse_coh_corr)

    def empty_init(self, num_ens: int, num_beams: int = 4):
        """
        If Bottom Track data is not available.  You can use this method
        to fill all the list with NAN.
        :param num_beams Number of beams.
        :param num_ens Number of ensembles.
        """
        self.num_beams = num_beams

        depth_empty = np.empty(num_ens, dtype=float)
        depth_empty.fill(np.nan)
        self.depth.append(depth_empty)

        snr_empty = np.empty(num_ens, dtype=float)
        snr_empty.fill(np.nan)
        self.snr.append(snr_empty)

        amp_empty = np.empty(num_ens, dtype=float)
        amp_empty.fill(np.nan)
        self.amp.append(amp_empty)

        corr_empty = np.empty(num_ens, dtype=float)
        corr_empty.fill(np.nan)
        self.corr.append(corr_empty)

        bv_empty = np.empty(num_ens, dtype=float)
        bv_empty.fill(np.nan)
        self.beam_vel.append(bv_empty)

        bg_empty = np.empty(num_ens, dtype=float)
        bg_empty.fill(np.nan)
        self.beam_good.append(bg_empty)

        iv_empty = np.empty(num_ens, dtype=float)
        iv_empty.fill(np.nan)
        self.instr_vel.append(iv_empty)

        ig_empty = np.empty(num_ens, dtype=float)
        ig_empty.fill(np.nan)
        self.instr_good.append(ig_empty)

        ev_empty = np.empty(num_ens, dtype=float)
        ev_empty.fill(np.nan)
        self.earth_vel.append(ev_empty)

        eg_empty = np.empty(num_ens, dtype=float)
        eg_empty.fill(np.nan)
        self.earth_good.append(eg_empty)

        pcs_empty = np.empty(num_ens, dtype=float)
        pcs_empty.fill(np.nan)
        self.pulse_coh_snr.append(pcs_empty)

        pca_empty = np.empty(num_ens, dtype=float)
        pca_empty.fill(np.nan)
        self.pulse_coh_amp.append(pca_empty)

        pcv_empty = np.empty(num_ens, dtype=float)
        pcv_empty.fill(np.nan)
        self.pulse_coh_vel.append(pcv_empty)

        pcn_empty = np.empty(num_ens, dtype=float)
        pcn_empty.fill(np.nan)
        self.pulse_coh_noise.append(pcn_empty)

        pcc_empty = np.empty(num_ens, dtype=float)
        pcc_empty.fill(np.nan)
        self.pulse_coh_corr.append(pcc_empty)


class RT:
    """
    Range Tracking values to measure the surface when upward looking.
    When downward looking, values are used as an echo sounder using
    the profile ping.
    """
    def __init__(self, pd0_format: bool = False):
        """
        Set the flag if using PD0 format data.
        If using PD0 format, then the beams will be rearranged to match PD0 beam order
        and the scale will change from percentage to counts.
        The value has to be converted from
        :param pd0_format: Set flag if the data should be decoded in PD0 format.
        """
        self.num_beams = 0
        self.snr = []
        self.depth = []
        self.pings = []
        self.amp = []
        self.corr = []
        self.beam_vel = []
        self.instr_vel = []
        self.earth_vel = []

        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ensemble data for the Range Tracking data.

        Initialize the list of Range Tracking data.  [beam]

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Get the number of beams
        self.num_beams = int(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        # Initialize the array
        snr = np.empty(shape=[self.num_beams], dtype=np.float)
        depth = np.empty(shape=[self.num_beams], dtype=np.float)
        pings = np.empty(shape=[self.num_beams], dtype=np.float)
        amp = np.empty(shape=[self.num_beams], dtype=np.float)
        corr = np.empty(shape=[self.num_beams], dtype=np.float)
        beam_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        instr_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        earth_vel = np.empty(shape=[self.num_beams], dtype=np.float)

        if self.num_beams == 4:
            snr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            snr[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            snr[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            snr[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            depth[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            pings[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            amp[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            corr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 19, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 20, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            beam_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 21, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 22, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 23, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 24, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            instr_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 25, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 26, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 27, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 28, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            earth_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 29, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 30, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 31, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[3] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 32, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        elif self.num_beams == 3:
            snr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            snr[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            snr[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            depth[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            pings[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            amp[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            corr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            beam_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            instr_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 19, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 20, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 21, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            earth_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 22, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 23, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[2] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 24, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        elif self.num_beams == 2:
            snr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            snr[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            depth[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            pings[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            amp[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            corr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            beam_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            instr_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

            earth_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[1] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        elif self.num_beams == 1:
            snr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            depth[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            pings[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            amp[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            corr[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            beam_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            instr_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            earth_vel[0] = (RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))

        # Add the data to the lis
        self.snr.append(snr)
        self.depth.append(depth)
        self.pings.append(pings)
        self.amp.append(amp)
        self.corr.append(corr)
        self.beam_vel.append(beam_vel)
        self.instr_vel.append(instr_vel)
        self.earth_vel.append(earth_vel)


class Nmea:
    """
    NMEA data from the ensemble dataset.
    """
    def __init__(self, pd0_format: bool = False):
        """
        Initialize all the values.

        Initializing the lists as list and converting
        to numpy array after data is decoded.
        """
        self.pd0_format = pd0_format

        self.gga = []
        self.gsa = []
        self.vtg = []
        self.dbt = []
        self.hdt = []

        # GGA
        self.gga_delta_time = []            # float
        self.gga_header = []                # str
        self.utc = []                       # float
        self.lat_deg = []                   # float
        self.lat_ref = []                   # str
        self.lon_deg = []                   # float
        self.lon_ref = []                   # str
        self.corr_qual = []                 # float
        self.num_sats = []                  # int
        self.hdop = []                      # float
        self.alt = []                       # float
        self.alt_unit = []                  # str
        self.geoid = []                     # str
        self.geoid_unit = []                # str
        self.d_gps_age = []                 # float
        self.ref_stat_id = []               # float

        # VTG
        self.vtg_delta_time = []            # float
        self.vtg_header = []                # str
        self.course_true = []               # float
        self.true_indicator = []            # str
        self.course_mag = []                # float
        self.mag_indicator = []             # str
        self.speed_knots = []               # float
        self.knots_indicator = []           # str
        self.speed_kph = []                 # float
        self.kph_indicator = []             # str
        self.mode_indicator = []            # str

        # HDT
        self.hdt_header = []
        self.heading = []
        self.rel_true_north = []

        # Temp variables to accumulate with each new ensemble
        self.temp_gga = []
        self.temp_gsa = []
        self.temp_vtg = []
        self.temp_dbt = []
        self.temp_hdt = []

    def decode(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the NMEA dataset.  This will be the raw NMEA messages
        from the ADCP containing GPS data.
        :param ens_bytes Bytes for dataset.
        :param name_len: Name length to get the start location.
        """
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        # Convert all the messages to a string
        nmea_str = str(ens_bytes[packet_pointer:], "UTF-8")

        # Clear the lists
        self.temp_gga.clear()
        self.temp_gsa.clear()
        self.temp_vtg.clear()
        self.temp_dbt.clear()
        self.temp_hdt.clear()

        # Decode each NMEA message
        for msg in nmea_str.split():
            self.decode_nmea(msg)

        # Convert all the list to numpy array for better storage
        # Add the data to the list
        self.gga.append(np.array(self.temp_gga))
        self.gsa.append(np.array(self.temp_gsa))
        self.vtg.append(np.array(self.temp_vtg))
        self.dbt.append(np.array(self.temp_dbt))
        self.hdt.append(np.array(self.temp_hdt))

        # Decode the last messages
        if len(self.temp_gga) > 0:
            self.decode_gga(self.temp_gga[-1])
        else:
            self.decode_gga(None)

        if len(self.temp_vtg) > 0:
            self.decode_vtg(self.temp_vtg[-1])
        else:
            self.decode_vtg(None)

        if len(self.temp_hdt) > 0:
            self.decode_hdt(self.temp_hdt[-1])
        else:
            self.decode_hdt(None)

    def decode_nmea(self, nmea_str: str):
        """
        Verify the NMEA message is by checking the checksum.
        Then add the message to the list and decode each message.
        :param nmea_str NMEA string to decode.
        """

        # Verify the NMEA string is good
        if Nmea.check_nmea_checksum(nmea_str):
            # Add each message to the list
            # Decode the data
            if 'gga' in  nmea_str or 'GGA' in nmea_str:
                self.temp_gga.append(nmea_str)
            if 'gsa' in nmea_str or 'GSA' in nmea_str:
                self.temp_gsa.append(nmea_str)
            if 'vtg' in nmea_str or 'VTG' in nmea_str:
                self.temp_vtg.append(nmea_str)
            if 'dbt' in nmea_str or 'DBT' in nmea_str:
                self.temp_dbt.append(nmea_str)
            if 'hdt' in nmea_str or 'HDT' in nmea_str:
                self.temp_hdt.append(nmea_str)

    def decode_gga(self, nmea_str: str):
        """
        Decode GGA message.  Update the variables.

        :param nmea_str NMEA string.
        """
        try:
            if nmea_str:
                temp_array = np.array(nmea_str.split(','))
                temp_array[temp_array == '999.9'] = ''

                #self.gga_delta_time = delta_time
                self.gga_header.append(temp_array[0])
                self.utc.append(float(temp_array[1]))
                lat_str = temp_array[2]
                lat_deg = float(lat_str[0:2])
                lat_deg = lat_deg + float(lat_str[2:]) / 60
                self.lat_deg.append(lat_deg)
                self.lat_ref.append(temp_array[3])
                lon_str = temp_array[4]
                lon_num = float(lon_str)
                lon_deg = np.floor(lon_num / 100)
                lon_deg = lon_deg + (((lon_num / 100.) - lon_deg) * 100.) / 60.
                self.lon_deg.append(lon_deg)
                self.lon_ref.append(temp_array[5])
                self.corr_qual.append(float(temp_array[6]))
                self.num_sats.append(float(temp_array[7]))
                self.hdop.append(float(temp_array[8]))
                self.alt.append(float(temp_array[9]))
                self.alt_unit.append(temp_array[10])
                self.geoid.append(temp_array[11])
                self.geoid_unit.append(temp_array[12])
                self.d_gps_age.append(float(temp_array[13]))
                idx_star = temp_array[14].find('*')
                self.ref_stat_id.append(float(temp_array[15][:idx_star]))
            else:
                self.gga_header.append(np.NaN)
                self.utc.append(np.NaN)
                self.lat_deg.append(np.NaN)
                self.lat_ref.append(np.NaN)
                self.lon_deg.append(np.NaN)
                self.lon_ref.append(np.NaN)
                self.corr_qual.append(np.NaN)
                self.num_sats.append(np.NaN)
                self.hdop.append(np.NaN)
                self.alt.append(np.NaN)
                self.alt_unit.append(np.NaN)
                self.geoid.append(np.NaN)
                self.geoid_unit.append(np.NaN)
                self.d_gps_age.append(np.NaN)
                self.ref_stat_id.append(np.NaN)

        except (ValueError, EOFError, IndexError):
            pass

    def decode_vtg(self, nmea_str: str):
        """
        Decode the VTG message and set all the variables.

        :param nmea_str: NMEA string.
        """
        try:
            if nmea_str:
                temp_array = np.array(nmea_str.split(','))
                temp_array[temp_array == '999.9'] = ''

                #self.vtg_delta_time = delta_time
                self.vtg_header.append(temp_array[0])
                self.course_true.append(Nmea.valid_number(temp_array[1]))
                self.true_indicator.append(temp_array[2])
                self.course_mag.append(Nmea.valid_number(temp_array[3]))
                self.mag_indicator.append(temp_array[4])
                self.speed_knots.append(Nmea.valid_number(temp_array[5]))
                self.knots_indicator.append(temp_array[6])
                self.speed_kph.append(Nmea.valid_number(temp_array[7]))
                self.kph_indicator.append(temp_array[8])
                idx_star = temp_array[9].find('*')
                self.mode_indicator.append(temp_array[9][:idx_star])
            else:
                self.vtg_header.append(np.NaN)
                self.course_true.append(np.NaN)
                self.true_indicator.append(np.NaN)
                self.course_mag.append(np.NaN)
                self.mag_indicator.append(np.NaN)
                self.speed_knots.append(np.NaN)
                self.knots_indicator.append(np.NaN)
                self.speed_kph.append(np.NaN)
                self.kph_indicator.append(np.NaN)
                self.mode_indicator.append(np.NaN)

        except (ValueError, EOFError, IndexError):
            pass

    def decode_hdt(self, nmea_str: str):
        """
        Decode the HDT message and set all the variables.

        :param nmea_str: NMEA string.
        """
        try:
            if nmea_str:
                temp_array = np.array(nmea_str.split(','))
                temp_array[temp_array == '999.9'] = ''

                # self.vtg_delta_time = delta_time
                self.hdt_header.append(temp_array[0])
                self.heading.append(Nmea.valid_number(temp_array[1]))
                idx_star = temp_array[2].find('*')
                self.rel_true_north.append(temp_array[2][:idx_star])
            else:
                self.hdt_header.append(np.NaN)
                self.heading.append(np.NaN)
                self.rel_true_north.append(np.NaN)

        except (ValueError, EOFError, IndexError):
            pass

    @staticmethod
    def valid_number(data_in):
        """
        Check to see if data_in can be converted to float.

        :param data_in: str String to be converted to float
        :return Returns a float of data_in or nan if conversion is not possible
        """

        try:
            data_out = float(data_in)
        except ValueError:
            data_out = np.nan
        return data_out

    @staticmethod
    def check_nmea_checksum(nmea_str: str):
        """
        Calculate the NMEA checksum.  Verify the
        checksum value matches the given value.
        :param nmea_str NMEA string.
        :return TRUE = Good checksum
        """
        try:
            # Remove newline and spaces at the end
            nmea_str = nmea_str.rstrip('\n')
            # Get the checksum value
            checksum = nmea_str[len(nmea_str) - 2:]
            checksum = int(checksum, 16)

            # Get the data from the string
            nmea_data = re.sub("(\n|\r\n)", "", nmea_str[nmea_str.find("$") + 1:nmea_str.find("*")])

            # Calculate the checksum
            calc_checksum = 0
            for c in nmea_data:
                calc_checksum ^= ord(c)
            calc_checksum = calc_checksum & 0xFF

            # Verify the checksum matches
            if calc_checksum == checksum:
                return True

            return False
        except Exception as ex:
            logging.error(ex)
            return False


class Gage:
    """
    Gage Height data from the ensemble dataset.
    """
    def __init__(self, pd0_format: bool = False):
        """
        Initialize all the values.

        Initializing the lists as list and converting
        to numpy array after data is decoded.
        """
        self.pd0_format = pd0_format

        self.status = []
        self.avg_range = []
        self.sd = []
        self.avg_sn = []
        self.n = []
        self.salinity = []
        self.pressure = []
        self.depth = []
        self.water_temp = []
        self.backplane_temp = []
        self.speed_of_sound = []
        self.heading = []
        self.pitch = []
        self.roll = []
        self.avg_s = []
        self.avg_n1 = []
        self.avg_n2 = []
        self.gain_frac = []

        self.pings = []
        self.snr_thresh = []
        self.gain_thresh = []
        self.stat_thresh = []
        self.xmt_cycles = []
        self.depth_offset = []

    def decode_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ancillary data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        self.status.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.avg_range.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 1, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.sd.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 2, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.avg_sn.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 3, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.n.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 4, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.salinity.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 5, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.pressure.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 6, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.depth.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 7, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.water_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 8, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.backplane_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 9, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.speed_of_sound.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 10, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.heading.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 11, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.pitch.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 12, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.roll.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 13, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.avg_s.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 14, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.avg_n1.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 15, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.avg_n2.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 16, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.gain_frac.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 17, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.pings.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 18, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.snr_thresh.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 19, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.gain_thresh.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 20, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.stat_thresh.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 21, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.xmt_cycles.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 22, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.depth_offset.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 23, RtbRowe.BYTES_IN_FLOAT, ens_bytes))


class RiverBT:
    """
    River Bottom Track data from the ensemble dataset.
    """
    def __init__(self, pd0_format: bool = False):
        """
        Initialize all the values.

        Initializing the lists as list and converting
        to numpy array after data is decoded.
        """
        self.pd0_format = pd0_format

        self.num_subsystems = []                # Number of subsystems to decode
        self.ping_count = []                    # Pings averaged
        self.status = []                        # Data status
        self.beams = []                         # Number of beams
        self.nce = []                           # Number of code elements
        self.repeats_n = []                     # Number of code repeats
        self.cpce = []                          # Codes per code elements
        self.bb = []                            # Broadband
        self.ll = []
        self.beam_mux = []                      # Beam Mux setup
        self.nb = []                            # Narrowband
        self.ping_sec = []                      # Ping time in seconds
        self.heading = []                       # Heading 0 to 360
        self.pitch = []                         # Pitch -90 to 90
        self.roll = []                          # Roll -180 to 180
        self.water_temp = []                    # Water Temperature in C
        self.backplane_temp = []                # Internal System temperature in C
        self.salinity = []                      # Salinity in PPT
        self.pressure = []                      # Pressure in Pascal
        self.depth = []                         # Pressure converted to m
        self.speed_of_sound = []                # Speed of Sound in m/s
        self.mx = []
        self.my = []
        self.mz = []
        self.gp = []
        self.gr = []
        self.gz = []
        self.samples_per_sec = []               # Samples per second
        self.system_freq_hz = []                # System frequency in Hz
        self.bt_range = []                      # Bottom Track Range in m
        self.bt_snr = []                        # Bottom Track SNR in dB
        self.bt_amp = []                        # Bottom Track Amplitude in dB
        self.bt_noise_amp_bp = []               # Noise in Amplitude Back Porch
        self.bt_noise_amp_fp = []               # Noise in Amplitude Front Porch
        self.bt_corr = []                       # Bottom Track Correlation in percent
        self.vel = []                           # Bottom Track Beam Velocity in m/s
        self.beam_n = []

    def decode_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the River Bottom data data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """

        # Determine where to start in the ensemble data
        packet_pointer = RtbRowe.get_base_data_size(name_len)

        num_subsystems = int(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * 0, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
        self.num_subsystems.append(num_subsystems)

        # Start of the data
        index = 1

        # Create a temp list to hold all the values for each subsystem
        # Accumulate the list then add it to the data type
        # Index will keep track of where we are located in the data
        pint_count = []
        for sb in range(num_subsystems):
            pint_count.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.ping_count.append(pint_count)

        status = []
        for sb in range(num_subsystems):
            status.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.status.append(status)

        beams = []
        for sb in range(num_subsystems):
            beams.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.beams.append(beams)

        nce = []
        for sb in range(num_subsystems):
            nce.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.nce.append(nce)

        repeats_n = []
        for sb in range(num_subsystems):
            repeats_n.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.repeats_n.append(repeats_n)

        cpce = []
        for sb in range(num_subsystems):
            cpce.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.cpce.append(cpce)

        bb = []
        for sb in range(num_subsystems):
            bb.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bb.append(bb)

        ll = []
        for sb in range(num_subsystems):
            ll.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.ll.append(ll)

        beam_mux = []
        for sb in range(num_subsystems):
            beam_mux.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.beam_mux.append(beam_mux)

        nb = []
        for sb in range(num_subsystems):
            nb.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.nb.append(nb)

        ps = []
        for sb in range(num_subsystems):
            ps.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.ping_sec.append(ps)

        hdg = []
        for sb in range(num_subsystems):
            hdg.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.heading.append(hdg)

        ptch = []
        for sb in range(num_subsystems):
            ptch.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.pitch.append(ptch)

        roll = []
        for sb in range(num_subsystems):
            roll.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.roll.append(roll)

        wt = []
        for sb in range(num_subsystems):
            wt.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.water_temp.append(wt)

        sys_temp = []
        for sb in range(num_subsystems):
            sys_temp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.backplane_temp.append(sys_temp)

        sal = []
        for sb in range(num_subsystems):
            sal.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.salinity.append(sal)

        pres = []
        for sb in range(num_subsystems):
            pres.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.pressure.append(pres)

        depth = []
        for sb in range(num_subsystems):
            depth.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.depth.append(depth)

        sos = []
        for sb in range(num_subsystems):
            sos.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.speed_of_sound.append(sos)

        mx = []
        for sb in range(num_subsystems):
            mx.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.mx.append(mx)

        my = []
        for sb in range(num_subsystems):
            my.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.my.append(my)

        mz = []
        for sb in range(num_subsystems):
            mz.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.mz.append(mz)

        gp = []
        for sb in range(num_subsystems):
            gp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.gp.append(gp)

        gr = []
        for sb in range(num_subsystems):
            gr.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.gr.append(gr)

        gz = []
        for sb in range(num_subsystems):
            gz.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.gz.append(gz)

        sps = []
        for sb in range(num_subsystems):
            sps.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.samples_per_sec.append(sps)

        freq = []
        for sb in range(num_subsystems):
            freq.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.system_freq_hz.append(freq)

        bt_range = []
        for sb in range(num_subsystems):
            bt_range.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bt_range.append(bt_range)

        snr = []
        for sb in range(num_subsystems):
            snr.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bt_snr.append(snr)

        amp = []
        for sb in range(num_subsystems):
            amp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bt_amp.append(amp)

        noise_bp = []
        for sb in range(num_subsystems):
            noise_bp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bt_noise_amp_bp.append(noise_bp)

        noise_fp = []
        for sb in range(num_subsystems):
            noise_fp.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bt_noise_amp_fp.append(noise_fp)

        corr = []
        for sb in range(num_subsystems):
            corr.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.bt_corr.append(corr)

        vel = []
        for sb in range(num_subsystems):
            vel.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.vel.append(vel)

        beam_n = []
        for sb in range(num_subsystems):
            beam_n.append(RtbRowe.get_float(packet_pointer + RtbRowe.BYTES_IN_FLOAT * index, RtbRowe.BYTES_IN_FLOAT, ens_bytes))
            index += 1
        self.beam_n.append(beam_n)





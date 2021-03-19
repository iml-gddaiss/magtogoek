import os
import re
import logging
import numpy as np
import struct
import binascii


class RtbRoweEns(object):
    """
    Class to read data from RTB files

    Single file to read in RTB data, then create an ensemble object list.  The list will contain all the
    data from the file.

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

        # List of all the ensembles decoded
        self.ens = []

        # Read in the given file path
        self.rtb_read(file_path=file_path, use_pd0_format=self.use_pd0_format)

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
            ens = self.decode_data_sets(ens_bytes, use_pd0_format=use_pd0_format)

            # Add the ensemble to the list
            self.ens.append(ens)

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
        #type = 0
        #numElements = 0
        #elementMultiplier = 0
        #imag = 0
        #nameLen = 0
        #name = ""
        #dataSetSize = 0
        ens_len = len(ens_bytes)

        # Create Ensemble
        ensemble = Ensemble()

        # Decode the ensemble datasets
        # Limit the number of attempts to look for new datasets
        for x in range(self.MAX_DATASETS):
            # Check if we are at the end of the payload
            if packetPointer >= ens_len - RtbRoweEns.CHECKSUM_SIZE - RtbRoweEns.HEADER_SIZE:
                break

            # Get the dataset info
            ds_type = RtbRoweEns.get_int32(packetPointer + (RtbRoweEns.BYTES_IN_INT32 * 0), RtbRoweEns.BYTES_IN_INT32, ens_bytes)
            num_elements = RtbRoweEns.get_int32(packetPointer + (RtbRoweEns.BYTES_IN_INT32 * 1), RtbRoweEns.BYTES_IN_INT32, ens_bytes)
            element_multiplier = RtbRoweEns.get_int32(packetPointer + (RtbRoweEns.BYTES_IN_INT32 * 2), RtbRoweEns.BYTES_IN_INT32, ens_bytes)
            image = RtbRoweEns.get_int32(packetPointer + (RtbRoweEns.BYTES_IN_INT32 * 3), RtbRoweEns.BYTES_IN_INT32, ens_bytes)
            name_len = RtbRoweEns.get_int32(packetPointer + (RtbRoweEns.BYTES_IN_INT32 * 4), RtbRoweEns.BYTES_IN_INT32, ens_bytes)
            name = str(ens_bytes[packetPointer + (RtbRoweEns.BYTES_IN_INT32 * 5):packetPointer + (RtbRoweEns.BYTES_IN_INT32 * 5) + 8], 'UTF-8')

            # Calculate the dataset size
            data_set_size = RtbRoweEns.get_data_set_size(ds_type, name_len, num_elements, element_multiplier)

            # Beam Velocity
            if "E000001" in name:
                logging.debug(name)
                ensemble.BeamVel = BeamVelocity(pd0_format=use_pd0_format)
                ensemble.BeamVel.decode(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                        num_elements=num_elements,
                                        element_multiplier=element_multiplier,
                                        name_len=name_len)

            # Instrument Velocity
            if "E000002" in name:
                logging.debug(name)
                ensemble.InstrVel = InstrVelocity(pd0_format=use_pd0_format)
                ensemble.InstrVel.decode(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                         num_elements=num_elements,
                                         element_multiplier=element_multiplier,
                                         name_len=name_len)

            # Earth Velocity
            if "E000003" in name:
                logging.debug(name)
                ensemble.EarthVel = EarthVelocity(pd0_format=use_pd0_format)
                ensemble.EarthVel.decode(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                         num_elements=num_elements,
                                         element_multiplier=element_multiplier,
                                         name_len=name_len)

            # Amplitude
            if "E000004" in name:
                logging.debug(name)
                ensemble.Amp = Amplitude(pd0_format=use_pd0_format)
                ensemble.Amp.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                    num_elements=num_elements,
                                    element_multiplier=element_multiplier,
                                    name_len=name_len)

            # Correlation
            if "E000005" in name:
                logging.debug(name)

                # Get code repeats for accurate conversion for PD0
                num_repeats = None
                if ensemble.Cfg:
                    num_repeats = ensemble.Cfg.wp_repeat_n

                ensemble.Corr = Correlation(pd0_format=True)
                ensemble.Corr.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                     num_elements=num_elements,
                                     element_multiplier=element_multiplier,
                                     num_repeats=num_repeats,
                                     name_len=name_len)

            # Good Beam
            if "E000006" in name:
                logging.debug(name)

                # Get the number of pings used in the ensemble
                pings_per_ens = 1
                if ensemble.Cfg:
                    pings_per_ens = ensemble.Cfg.actual_ping_count

                ensemble.GdB = GoodBeam(pd0_format=use_pd0_format)
                ensemble.GdB.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                    num_elements=num_elements,
                                    element_multiplier=element_multiplier,
                                    pings_per_ens=pings_per_ens,
                                    name_len=name_len)

            # Good Earth
            if "E000007" in name:
                logging.debug(name)
                ensemble.GdE = GoodEarth(pd0_format=use_pd0_format)
                ensemble.GdE.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                    num_elements=num_elements,
                                    element_multiplier=element_multiplier,
                                    pings_per_ens=pings_per_ens,
                                    name_len=name_len)

            # Ensemble Data
            if "E000008" in name:
                logging.debug(name)
                # Check if the Cfg is already created from other dataset
                if not ensemble.Cfg:
                    ensemble.Cfg = Cfg(pd0_format=use_pd0_format)
                ensemble.Cfg.decode_ensemble_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                  name_len=name_len)

            # Ancillary Data
            if "E000009" in name:
                logging.debug(name)

                # Configuration data
                # Check if the Cfg is already created from other dataset
                if not ensemble.Cfg:
                    ensemble.Cfg = Cfg(pd0_format=use_pd0_format)
                ensemble.Cfg.decode_ancillary_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                   name_len=name_len)

                # Sensor data
                # Check if the Sensor is already created from other dataset
                if not ensemble.Sensor:
                    ensemble.Sensor = Sensor(pd0_format=use_pd0_format)
                ensemble.Sensor.decode_ancillary_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                      name_len=name_len)

            # Bottom Track
            if "E000010" in name:
                logging.debug(name)
                # Populate Bottom Track data
                if not ensemble.Bt:
                    ensemble.Bt = BT(pd0_format=use_pd0_format)
                ensemble.Bt.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                   name_len=name_len)

                # Populate Config data
                if not ensemble.Cfg:
                    ensemble.Cfg = Cfg(pd0_format=use_pd0_format)
                ensemble.Cfg.decode_bottom_track_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                      name_len=name_len)

                # Populate Sensor data
                if not ensemble.Sensor:
                    ensemble.Sensor = Cfg(pd0_format=use_pd0_format)
                ensemble.Sensor.decode_bottom_track_data(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                                         name_len=name_len)

            # NMEA data
            if "E000011" in name:
                logging.debug(name)
                if not ensemble.Nmea:
                    ensemble.Nmea = Nmea(pd0_format=use_pd0_format)
                ensemble.Nmea.decode(ens_bytes=ens_bytes[packetPointer:packetPointer+data_set_size],
                                     name_len=name_len)

            # System Setup
            if "E000014" in name:
                logging.debug(name)
                # Configuration data
                # Check if the Cfg is already created from other dataset
                if not ensemble.Cfg:
                    ensemble.Cfg = Cfg(pd0_format=use_pd0_format)
                ensemble.Cfg.decode_systemsetup_data(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                                     name_len=name_len)

                if not ensemble.Sensor:
                    ensemble.Sensor = Sensor(pd0_format=use_pd0_format)
                ensemble.Sensor.decode_systemsetup_data(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                                        name_len=name_len)

            # Range Tracking
            if "E000015" in name:
                logging.debug(name)
                ensemble.Rt = RT(pd0_format=use_pd0_format)
                ensemble.Rt.decode(ens_bytes=ens_bytes[packetPointer:packetPointer + data_set_size],
                                   name_len=name_len)

            # Move to the next dataset
            packetPointer += data_set_size

        return ensemble

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

        return ((num_elements * element_multiplier) * datatype_size) + RtbRoweEns.get_base_data_size(name_len)

    @staticmethod
    def get_base_data_size(name_len: int):
        """
        Get the size of the header for a dataset.
        :param name_len: Length of the name.
        :return: Dataset header size in bytes.
        """
        return name_len + (RtbRoweEns.BYTES_IN_INT32 * (RtbRoweEns.NUM_DATASET_HEADER_ELEMENTS - 1))

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
        if vel >= RtbRoweEns.BAD_VEL:
            return True
        if RtbRoweEns.is_float_close(vel, RtbRoweEns.BAD_VEL):
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


class Ensemble:
    """
    Object to hold all the ensemble data.
    Eliminate the need to create array for every element.
    Also you do not need to know how many ensembles are in a file.
    Because an RTB can have up to 12 different configurations per deployment,
    the ensemble sizes will vary widely.
    """
    def __init__(self):
        self.Cfg = None
        self.Sensor = None
        self.Amp = None
        self.Corr = None
        self.BeamVel = None
        self.InstrVel = None
        self.EarthVel = None
        self.GdB = None
        self.GdE = None
        self.Rt = None
        self.Wt = None
        self.Bt = None
        self.Gps = None
        self.Gps2 = None
        self.Surface = None
        self.AutoMode = None
        self.Nmea = None


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
        self.vel = None
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
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        # Initialize the array
        #for beam in range(element_multiplier):
        #    self.vel[beam].append([None] * num_elements)
        if not self.pd0_format:
            self.vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            self.vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    # Use the original value
                    self.vel[beam][bin_num] = RtbRoweEns.get_float(packet_pointer, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Get the velocity data
                    pd0_vel = RtbRoweEns.get_float(packet_pointer, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

                    # Check for bad velocity and convert
                    if RtbRoweEns.is_bad_velocity(pd0_vel):
                        pd0_vel = RtbRoweEns.PD0_BAD_VEL
                    else:
                        # Convert from m/s to mm/s
                        pd0_vel = round(pd0_vel * 1000.0)

                    # Set the velocity based on the beam reassignment
                    if element_multiplier == 1:             # Vertical Beam
                        self.vel[0][bin_num] = pd0_vel
                    elif beam == 0:                         # RTB 0 - PD0 3
                        self.vel[3][bin_num] = pd0_vel
                    elif beam == 1:                         # RTB 1 - PD0 2
                        self.vel[2][bin_num] = pd0_vel
                    elif beam == 2:                         # RTB 2 - PD0 0
                        self.vel[0][bin_num] = pd0_vel
                    elif beam == 3:                         # RTB 3 - PD0 1
                        self.vel[1][bin_num] = pd0_vel

                # Move the pointer
                packet_pointer += RtbRoweEns.BYTES_IN_FLOAT


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
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            self.vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            self.vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    self.vel[beam][bin_num] = RtbRoweEns.get_float(packet_pointer, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Get the velocity data
                    pd0_vel = RtbRoweEns.get_float(packet_pointer, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

                    # Check for bad velocity and convert
                    if RtbRoweEns.is_bad_velocity(pd0_vel):
                        pd0_vel = RtbRoweEns.PD0_BAD_VEL
                    else:
                        # Convert from m/s to mm/s
                        pd0_vel = round(pd0_vel * 1000.0)

                    # Set the velocity based on the beam reassignment
                    if element_multiplier == 1:                     # Vertical Beam
                        self.vel[0][bin_num] = pd0_vel
                    elif beam == 0:                                 # RTB 0 - PD0 1
                        self.vel[1][bin_num] = pd0_vel
                    elif beam == 1:                                 # RTB 1 - PD0 0
                        self.vel[0][bin_num] = pd0_vel
                    elif beam == 2:                                 # RTB 2 - PD0 -2
                        if pd0_vel != RtbRoweEns.PD0_BAD_VEL:
                            self.vel[2][bin_num] = pd0_vel * -1.0
                        else:
                            self.vel[2][bin_num] = pd0_vel
                    elif beam == 3:                                 # RTB 3 - PD0 3
                        self.vel[3][bin_num] = pd0_vel

                # Move the pointer
                packet_pointer += RtbRoweEns.BYTES_IN_FLOAT


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
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            self.vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            self.vel = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    self.vel[beam][bin_num] = RtbRoweEns.get_float(packet_pointer, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Get the velocity data
                    pd0_vel = RtbRoweEns.get_float(packet_pointer, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

                    # Check for bad velocity and convert
                    if RtbRoweEns.is_bad_velocity(pd0_vel):
                        pd0_vel = RtbRoweEns.PD0_BAD_VEL
                    else:
                        # Convert from m/s to mm/s
                        pd0_vel = round(pd0_vel * 1000.0)

                    # Set the values
                    # No reassignment needed
                    self.vel[beam][bin_num] = pd0_vel

                # Move the pointer
                packet_pointer += RtbRoweEns.BYTES_IN_FLOAT


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
        self.amp = None
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
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            self.amp = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            self.amp = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    self.amp[beam][bin_num] = RtbRoweEns.get_float(packet_pointer, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
                else:
                    # Get the dB and convert to counts
                    pd0_amp = round(RtbRoweEns.get_float(packet_pointer, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes) * 2.0)

                    # Beam Reassignment
                    if element_multiplier == 1:                 # Vertical Beam
                        self.amp[beam][bin_num] = pd0_amp
                    elif beam == 0:                               # RTB 0 - PD0 3
                        self.amp[3][bin_num] = pd0_amp
                    elif beam == 1:                             # RTB 1 - PD0 2
                        self.amp[2][bin_num] = pd0_amp
                    elif beam == 2:                             # RTB 2 - PD0 0
                        self.amp[0][bin_num] = pd0_amp
                    elif beam == 3:                             # RTB 3 - PD0 1
                        self.amp[1][bin_num] = pd0_amp

                # Move the pointer
                packet_pointer += RtbRoweEns.BYTES_IN_FLOAT


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
        self.corr = None
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
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            self.corr = np.empty(shape=[element_multiplier, num_elements], dtype=np.float)
        else:
            self.corr = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list of velocities
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    self.corr[beam][bin_num] = RtbRoweEns.get_float(packet_pointer, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
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
                        pd0_corr = RtbRoweEns.get_float(packet_pointer, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes) * 128.0
                        pd0_corr = round(pd0_corr / repeats)
                    else:
                        # If no repeats given, use this calculation
                        pd0_corr = RtbRoweEns.get_float(packet_pointer, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes) * 255.0

                    # Beam Reassignment
                    if element_multiplier == 1:                 # Vertical Beam
                        self.corr[beam][bin_num] = RtbRoweEns.get_float(packet_pointer, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes) * 255.0
                    elif beam == 0:                               # RTB 0 - PD0 3
                        self.corr[3][bin_num] = pd0_corr
                    elif beam == 1:                             # RTB 1 - PD0 2
                        self.corr[2][bin_num] = pd0_corr
                    elif beam == 2:                             # RTB 2 - PD0 0
                        self.corr[0][bin_num] = pd0_corr
                    elif beam == 3:                             # RTB 3 - PD0 1
                        self.corr[1][bin_num] = pd0_corr

                # Move the pointer
                packet_pointer += RtbRoweEns.BYTES_IN_FLOAT


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
        self.pings = None
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
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            self.pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)
        else:
            self.pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    self.pings[beam][bin_num] = RtbRoweEns.get_int32(packet_pointer, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
                else:
                    # Verify a good value for pings_per_ens
                    if pings_per_ens == 0:
                        pings_per_ens = 1

                    # Get the Good Beam number of good pings and convert to percentage
                    pd0_gb = round((RtbRoweEns.get_int32(packet_pointer, RtbRoweEns.BYTES_IN_INT32, ens_bytes) * 100) / pings_per_ens)

                    # Beam Reassignment
                    if element_multiplier == 1:                 # Vertical Beam
                        self.pings[beam][bin_num] = pd0_gb
                    elif beam == 0:                               # RTB 0 - PD0 3
                        self.pings[3][bin_num] = pd0_gb
                    elif beam == 1:                             # RTB 1 - PD0 2
                        self.pings[2][bin_num] = pd0_gb
                    elif beam == 2:                             # RTB 2 - PD0 0
                        self.pings[0][bin_num] = pd0_gb
                    elif beam == 3:                             # RTB 3 - PD0 1
                        self.pings[1][bin_num] = pd0_gb

                # Move the pointer
                packet_pointer += RtbRoweEns.BYTES_IN_INT32


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
        self.pings = None
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
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        # Initialize the array
        if not self.pd0_format:
            self.pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)
        else:
            self.pings = np.empty(shape=[element_multiplier, num_elements], dtype=np.int)

        # Create a 2D list
        # [beam][bin]
        for beam in range(element_multiplier):
            for bin_num in range(num_elements):
                # Determine if RTB or PD0 data format
                if not self.pd0_format:
                    self.pings[beam][bin_num] = RtbRoweEns.get_int32(packet_pointer, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
                else:
                    # Verify a good value for pings_per_ens
                    if pings_per_ens == 0:
                        pings_per_ens = 1

                    # Get the Good Earth number of good pings and convert to percentage
                    # No reassignment needed
                    self.pings[beam][bin_num] = round((RtbRoweEns.get_int32(packet_pointer, RtbRoweEns.BYTES_IN_INT32, ens_bytes) * 100) / pings_per_ens)

                # Move the pointer
                packet_pointer += RtbRoweEns.BYTES_IN_INT32


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

        self.ens_num = 0                    # Ensemble number
        self.num_bins = 0                   # Number of bins
        self.num_beams = 0                  # Number of beams
        self.desired_ping_count = 0         # Avg Ping Count configured in seconds
        self.actual_ping_count = 0          # Avg Ping Count actually output in seconds
        self.serial_num = ""                # Serial Number
        self.firm_major = 0                 # Firmware Major Number
        self.firm_minor = 0                 # Firmware Minor Number
        self.firm_rev = 0                   # Firmware Revision
        self.subsystem_code = ""            # Subsystem Code (Indentifier of frequency and orientation)
        self.subsystem_config = 0           # Subsystem Config.  System allows multiple configures of the same frequency.  This identifies each configuration
        self.status = 0                     # Status code
        self.year = 0                       # Year
        self.month = 0                      # Month
        self.day = 0                        # Day
        self.hour = 0                       # Hour
        self.minute = 0                     # Minute
        self.second = 0                     # Second
        self.hsec = 0                       # Hundredth Second

        self.blank = 0.0                    # Blank.  Depth to the first bin in meters.
        self.bin_size = 0.0                 # Size of a bin in meters.
        self.first_ping_time = 0.0          # First Ping Time in seconds.
        self.last_ping_time = 0.0           # Last Ping Time in seconds. (If averaging pings, this will be the last ping)
        self.salinity = 0.0                 # Water Salinity set by the user in PPT
        self.speed_of_sound = 0.0           # Speed of Sound in m/s.

        self.bt_first_ping_time = 0.0
        self.bt_last_ping_time = 0.0
        self.bt_speed_of_sound = 0.0
        self.bt_status = 0.0
        self.bt_num_beams = 0.0
        self.bt_actual_ping_count = 0.0

        self.bt_samples_per_second = 0.0    # Bottom Track Samples Per Second
        self.bt_system_freq_hz = 0.0        # Bottom Track System Frequency (Hz)
        self.bt_cpce = 0.0                  # Bottom Track Cycles per Code Elements
        self.bt_nce = 0.0                   # Bottom Track Number of Code Elements
        self.bt_repeat_n = 0.0              # Bottom Track Number of Code Repeats
        self.wp_samples_per_second = 0.0    # Water Profile Samples per Second
        self.wp_system_freq_hz = 0.0        # Water Profile System Frequency (Hz)
        self.wp_cpce = 0.0                  # Water Profile Cycles per Code Element
        self.wp_nce = 0.0                   # Water Profile Number of Code Element
        self.wp_repeat_n = 0.0              # Water Profile Number of Code Repeats
        self.wp_lag_samples = 0.0           # Water Profile Lag Samples
        self.bt_broadband = 0.0             # Bottom Track Broadband
        self.bt_lag_length = 0.0            # Bottom Track Pulse to Pulse Lag (m)
        self.bt_narrowband = 0.0            # Bottom Track Long Range Switch Depth (m)
        self.bt_beam_mux = 0.0              # Bottom Track Beam Multiplex
        self.wp_broadband = 0.0             # Water Profile Mode
        self.wp_lag_length = 0.0            # Water Profile Lag Length
        self.wp_transmit_bandwidth = 0.0    # Water Profile Transmit Bandwidth
        self.wp_receive_bandwidth = 0.0     # Water Profile Receive Bandwidth
        self.wp_beam_mux = 0.0              # WP Beam Mux

    def decode_ensemble_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ensemble data for the configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        self.ens_num = RtbRoweEns.get_int32(packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 0, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
        self.num_bins = RtbRoweEns.get_int32(packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 1, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
        self.num_beams = RtbRoweEns.get_int32(packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 2, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
        self.desired_ping_count = RtbRoweEns.get_int32(packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 3, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
        self.actual_ping_count = RtbRoweEns.get_int32(packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 4, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
        self.status = RtbRoweEns.get_int32(packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 5, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
        self.year = RtbRoweEns.get_int32(packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 6, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
        self.month = RtbRoweEns.get_int32(packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 7, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
        self.day = RtbRoweEns.get_int32(packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 8, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
        self.hour = RtbRoweEns.get_int32(packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 9, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
        self.minute = RtbRoweEns.get_int32(packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 10, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
        self.second = RtbRoweEns.get_int32(packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 11, RtbRoweEns.BYTES_IN_INT32, ens_bytes)
        self.hsec = RtbRoweEns.get_int32(packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 12, RtbRoweEns.BYTES_IN_INT32, ens_bytes)

        self.serial_num = str(ens_bytes[packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 13:packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 21], "UTF-8")
        self.firm_rev = struct.unpack("B", ens_bytes[packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 21 + 0:packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 21 + 1])[0]
        self.firm_minor = struct.unpack("B", ens_bytes[packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 21 + 1:packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 21 + 2])[0]
        self.firm_major = struct.unpack("B", ens_bytes[packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 21 + 2:packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 21 + 3])[0]
        self.subsystem_code = str(ens_bytes[packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 21 + 3:packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 21 + 4], "UTF-8")

        self.subsystem_config = struct.unpack("B", ens_bytes[packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 22 + 3:packet_pointer + RtbRoweEns.BYTES_IN_INT32 * 22 + 4])[0]

        if self.pd0_format:
            self.year = self.year - 2000
            self.salinity = round(self.salinity)
            self.speed_of_sound = round(self.speed_of_sound)

    def decode_ancillary_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ancillary data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        self.blank = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 0, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bin_size = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 1, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.first_ping_time = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 2, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.last_ping_time = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 3, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

        self.salinity = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 9, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.speed_of_sound = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 12, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

    def decode_systemsetup_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the system setup data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        self.bt_samples_per_second = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 0, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_system_freq_hz = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 1, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_cpce = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 2, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_nce = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 3, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_repeat_n = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 4, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.wp_samples_per_second = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 5, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.wp_system_freq_hz = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 6, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.wp_cpce = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 7, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.wp_nce = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 8, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.wp_repeat_n = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 9, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.wp_lag_samples = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 10, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_broadband = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 13, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_lag_length = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 14, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_narrowband = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 15, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_beam_mux = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 16, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.wp_broadband = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 17, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.wp_lag_length = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 18, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.wp_transmit_bandwidth = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 19, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.wp_receive_bandwidth = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 20, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.wp_beam_mux = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 22, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

    def decode_bottom_track_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the system Bottom Track data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        self.bt_first_ping_time = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 0, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_last_ping_time = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 1, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_speed_of_sound = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 10, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_status = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 11, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_num_beams = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 12, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_actual_ping_count = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 13, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)


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

        self.heading = 0.0                          # Heading in degrees.
        self.pitch = 0.0                            # Pitch in degrees.
        self.roll = 0.0                             # Roll in degrees.
        self.water_temp = 0.0                       # Water Temperature in fahrenheit
        self.system_temp = 0.0                      # System Temperature in fahrenheit

        self.pressure = 0.0                         # Pressure from pressure sensor in Pascals
        self.transducer_depth = 0.0                 # Transducer Depth, used by Pressure sensor in meters

        self.voltage = 0.0                          # Voltage input to ADCP
        self.xmt_voltage = 0.0                      # Transmit Voltage
        self.transmit_boost_neg_volt = 0.0          # Transmitter Boost Negative Voltage

        self.raw_mag_field_strength = 0.0           # Raw magnetic field strength (uT) (micro Tesla)
        self.raw_mag_field_strength2 = 0.0          # Raw magnetic field strength (uT) (micro Tesla)
        self.raw_mag_field_strength3 = 0.0          # Raw magnetic field strength (uT) (micro Tesla)
        self.pitch_gravity_vec = 0.0                # Pitch Gravity Vector
        self.roll_gravity_vec = 0.0                 # Roll Gravity Vector
        self.vertical_gravity_vec = 0.0             # Vertical Gravity Vector

        self.bt_heading = 0.0
        self.bt_pitch = 0.0
        self.bt_roll = 0.0
        self.bt_water_temp = 0.0
        self.bt_system_temp = 0.0
        self.bt_salinity = 0.0
        self.bt_pressure = 0.0
        self.bt_transducer_depth = 0.0

    def decode_systemsetup_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the system setup data for the Sensor data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        self.voltage = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 11, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.xmt_voltage = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 12, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.transmit_boost_neg_volt = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 21, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

    def decode_ancillary_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ancillary data for the Sensor data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        self.heading = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 4, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.pitch = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 5, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.roll = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 6, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.water_temp = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 7, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.system_temp = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 8, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

        self.pressure = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 10, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.transducer_depth = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 11, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

        self.raw_mag_field_strength = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 13, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.raw_mag_field_strength2 = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 14, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.raw_mag_field_strength3 = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 15, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.pitch_gravity_vec = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 16, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.roll_gravity_vec = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 17, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.vertical_gravity_vec = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 18, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

        # Convert values to PD0 format if selected
        if self.pd0_format:
            if self.roll > 90.0:
                self.roll = -1 * (180.0 - self.roll)
            elif self.roll < -90.0:
                self.roll = 180.0 + self.roll

            self.pressure = round(self.pressure * 0.0001)
            self.transducer_depth = round(self.transducer_depth * 10.0)

    def decode_bottom_track_data(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ancillary data for the Configuration data.

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        self.bt_heading = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 2, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_pitch = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 3, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_roll = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 4, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_water_temp = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 5, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_system_temp = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 6, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_salinity = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 7, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_pressure = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 8, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
        self.bt_transducer_depth = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 9, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

        # Convert values to PD0 format if selected
        if self.pd0_format:
            if self.bt_roll > 90.0:
                self.bt_roll = -1 * (180.0 - self.bt_roll)
            elif self.bt_roll < -90.0:
                self.bt_roll = 180.0 + self.bt_roll

            self.bt_pressure = round(self.pressure * 0.0001)
            self.bt_transducer_depth = round(self.transducer_depth * 10.0)


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
        self.range = []
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
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        # Get the number of beams
        self.num_beams = int(RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 12, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

        # Get the ping count
        # Value stored in Cfg but needed for conversion to PD0
        bt_actual_ping_count = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 13, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)


        # Initialize the array
        self.snr = np.empty(shape=[self.num_beams], dtype=np.float)
        self.range = np.empty(shape=[self.num_beams], dtype=np.float)
        self.amp = np.empty(shape=[self.num_beams], dtype=np.float)
        self.corr = np.empty(shape=[self.num_beams], dtype=np.float)
        self.beam_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        self.beam_good = np.empty(shape=[self.num_beams], dtype=np.int)
        self.instr_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        self.instr_good = np.empty(shape=[self.num_beams], dtype=np.int)
        self.earth_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        self.earth_good = np.empty(shape=[self.num_beams], dtype=np.int)
        self.pulse_coh_snr = np.empty(shape=[self.num_beams], dtype=np.float)
        self.pulse_coh_amp = np.empty(shape=[self.num_beams], dtype=np.float)
        self.pulse_coh_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        self.pulse_coh_noise = np.empty(shape=[self.num_beams], dtype=np.float)
        self.pulse_coh_corr = np.empty(shape=[self.num_beams], dtype=np.float)

        index = 14
        # Range Values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                self.range[beam] = value
            else:
                # PD0 data
                # Check for bad velocity and convert
                if RtbRoweEns.is_bad_velocity(value):
                    value = RtbRoweEns.PD0_BAD_VEL
                else:
                    # Convert from m to cm
                    value = round(value * 100.0)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:
                    self.range[0] = value
                if beam == 0:
                    self.range[3] = value
                elif beam == 1:
                    self.range[2] = value
                elif beam == 2:
                    self.range[0] = value
                elif beam == 3:
                    self.range[1] = value

            # Increment for the next beam
            index += 1

        # SNR values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                self.snr[beam] = value
            else:
                # PD0 data
                # Convert from db to counts (0.5 counts per dB)
                value = round(value * 2.0)

                # Check for bad value
                if value > RtbRoweEns.PD0_BAD_AMP:
                    value = RtbRoweEns.PD0_BAD_AMP

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:
                    self.snr[0] = value
                elif beam == 0:
                    self.snr[3] = value
                elif beam == 1:
                    self.snr[2] = value
                elif beam == 2:
                    self.snr[0] = value
                elif beam == 3:
                    self.snr[1] = value

            # Increment for the next beam
            index += 1

        # Amplitude values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                self.amp[beam] = value
            else:
                # PD0 data
                # Convert from db to counts (0.5 counts per dB)
                value = round(value * 2.0)

                # Check for bad value
                if value > RtbRoweEns.PD0_BAD_AMP:
                    value = RtbRoweEns.PD0_BAD_AMP

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:
                    self.amp[0] = value
                elif beam == 0:
                    self.amp[3] = value
                elif beam == 1:
                    self.amp[2] = value
                elif beam == 2:
                    self.amp[0] = value
                elif beam == 3:
                    self.amp[1] = value

            # Increment for the next beam
            index += 1

        # Correlation values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                self.corr[beam] = value
            else:
                # PD0 data
                # Convert from percentage to 0-255 counts
                value = round(value * 255.0)

                # Check for bad value
                if value > RtbRoweEns.PD0_BAD_AMP:
                    value = RtbRoweEns.PD0_BAD_AMP

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:             # Vertical beam
                    self.corr[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 3
                    self.corr[3] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 2
                    self.corr[2] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 0
                    self.corr[0] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 1
                    self.corr[1] = value

            # Increment for the next beam
            index += 1

        # Beam Velocity values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

            # Check for bad velocity and convert
            if RtbRoweEns.is_bad_velocity(value):
                value = np.nan

            if not self.pd0_format:
                # Store RTB data
                self.beam_vel[beam] = value
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
                    self.beam_vel[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 3
                    self.beam_vel[3] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 2
                    self.beam_vel[2] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 0
                    self.beam_vel[0] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 1
                    self.beam_vel[1] = value

            # Increment for the next beam
            index += 1

        # Beam Good Pings values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                self.beam_good[beam] = int(value)
            else:
                # PD0 data
                # Check for bad velocity and convert
                if RtbRoweEns.is_bad_velocity(value):
                    value = RtbRoweEns.PD0_BAD_VEL
                else:
                    # Convert from number of good pings to a percentage of good pings
                    value = round((value * 100.0) / bt_actual_ping_count)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
                if self.num_beams == 1:             # Vertical beam
                    self.beam_good[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 3
                    self.beam_good[3] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 2
                    self.beam_good[2] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 0
                    self.beam_good[0] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 1
                    self.beam_good[1] = value

            # Increment for the next beam
            index += 1

        # Instrument Velocity values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

            # Check for bad velocity and convert
            if RtbRoweEns.is_bad_velocity(value):
                value = np.nan

            if not self.pd0_format:
                # Store RTB data
                self.instr_vel[beam] = value
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
                    self.instr_vel[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 1
                    self.instr_vel[1] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 0
                    self.instr_vel[0] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam -2
                    self.instr_vel[2] = value * -1.0
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 3
                    self.instr_vel[3] = value

            # Increment for the next beam
            index += 1

        # Instrument Good Pings values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                self.instr_good[beam] = int(value)
            else:
                # PD0 data
                # Check for bad velocity and convert
                if RtbRoweEns.is_bad_velocity(value):
                    value = RtbRoweEns.PD0_BAD_VEL
                else:
                    # Convert from number of good pings to a percentage of good pings
                    value = round((value * 100.0) / bt_actual_ping_count)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 XYZ order 1,0,-2,3
                if self.num_beams == 1:             # Vertical beam
                    self.instr_good[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 1
                    self.instr_good[1] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 0
                    self.instr_good[0] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam -2
                    self.instr_good[2] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 3
                    self.instr_good[3] = value

            # Increment for the next beam
            index += 1

        # Earth Velocity values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

            # Check for bad velocity and convert
            if RtbRoweEns.is_bad_velocity(value):
                value = np.nan

            if not self.pd0_format:
                # Store RTB data
                self.earth_vel[beam] = value
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
                    self.earth_vel[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 0
                    self.earth_vel[0] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 1
                    self.earth_vel[1] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 2
                    self.earth_vel[2] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 3
                    self.earth_vel[3] = value

            # Increment for the next beam
            index += 1

        # Earth Good Pings values
        for beam in range(self.num_beams):
            # Get the value
            value = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)

            if not self.pd0_format:
                # Store RTB data
                self.earth_good[beam] = int(value)
            else:
                # PD0 data
                # Check for bad velocity and convert
                if RtbRoweEns.is_bad_velocity(value):
                    value = RtbRoweEns.PD0_BAD_VEL
                else:
                    # Convert from number of good pings to a percentage of good pings
                    value = round((value * 100.0) / bt_actual_ping_count)

                # Reorganize beams
                # RTB BEAM 0,1,2,3 = PD0 XYZ order 0,1,2,3
                if self.num_beams == 1:             # Vertical beam
                    self.earth_good[0] = value
                elif beam == 0:                     # RTB Beam 0 - PD0 Beam 0
                    self.earth_good[0] = value
                elif beam == 1:                     # RTB Beam 1 - PD0 Beam 1
                    self.earth_good[1] = value
                elif beam == 2:                     # RTB Beam 2 - PD0 Beam 2
                    self.earth_good[2] = value
                elif beam == 3:                     # RTB Beam 3 - PD0 Beam 3
                    self.earth_good[3] = value

            # Increment for the next beam
            index += 1

        # Pulse Coherent SNR values
        for beam in range(self.num_beams):
            self.pulse_coh_snr[beam] = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
            index += 1

        # Pulse Coherent Amplitude values
        for beam in range(self.num_beams):
            self.pulse_coh_amp[beam] = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
            index += 1

        # Pulse Coherent Velocity values
        for beam in range(self.num_beams):
            self.pulse_coh_vel[beam] = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
            index += 1

        # Pulse Coherent Noise values
        for beam in range(self.num_beams):
            self.pulse_coh_noise[beam] = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
            index += 1

        # Pulse Coherent Correlation values
        for beam in range(self.num_beams):
            self.pulse_coh_corr[beam] = RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * index, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes)
            index += 1


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
        self.snr = None
        self.range = None
        self.pings = None
        self.amp = None
        self.corr = None
        self.beam_vel = None
        self.instr_vel = None
        self.earth_vel = None

        self.pd0_format = pd0_format

    def decode(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the ensemble data for the Range Tracking data.

        Initialize the list of Range Tracking data.  [beam]

        :param ens_bytes: Byte array containing the ensemble data.
        :param name_len: Length of the name of the dataset.
        """
        # Determine where to start in the ensemble data
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        # Get the number of beams
        self.num_beams = int(RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 0, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

        # Initialize the array
        self.snr = np.empty(shape=[self.num_beams], dtype=np.float)
        self.range = np.empty(shape=[self.num_beams], dtype=np.float)
        self.pings = np.empty(shape=[self.num_beams], dtype=np.float)
        self.amp = np.empty(shape=[self.num_beams], dtype=np.float)
        self.corr = np.empty(shape=[self.num_beams], dtype=np.float)
        self.beam_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        self.instr_vel = np.empty(shape=[self.num_beams], dtype=np.float)
        self.earth_vel = np.empty(shape=[self.num_beams], dtype=np.float)

        if self.num_beams == 4:
            self.snr[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 1, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.snr[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 2, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.snr[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 3, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.snr[3] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 4, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.range[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 5, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.range[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 6, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.range[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 7, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.range[3] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 8, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.pings[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 9, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.pings[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 10, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.pings[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 11, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.pings[3] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 12, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.amp[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 13, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.amp[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 14, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.amp[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 15, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.amp[3] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 16, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.corr[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 17, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.corr[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 18, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.corr[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 19, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.corr[3] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 20, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.beam_vel[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 21, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.beam_vel[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 22, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.beam_vel[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 23, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.beam_vel[3] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 24, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.instr_vel[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 25, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.instr_vel[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 26, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.instr_vel[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 27, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.instr_vel[3] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 28, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.earth_vel[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 29, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.earth_vel[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 30, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.earth_vel[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 31, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.earth_vel[3] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 32, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
        elif self.num_beams == 3:
            self.snr[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 1, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.snr[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 2, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.snr[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 3, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.range[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 4, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.range[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 5, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.range[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 6, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.pings[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 7, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.pings[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 8, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.pings[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 9, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.amp[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 10, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.amp[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 11, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.amp[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 12, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.corr[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 13, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.corr[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 14, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.corr[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 15, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.beam_vel[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 16, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.beam_vel[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 17, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.beam_vel[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 18, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.instr_vel[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 19, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.instr_vel[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 20, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.instr_vel[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 21, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.earth_vel[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 22, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.earth_vel[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 23, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.earth_vel[2] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 24, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
        elif self.num_beams == 2:
            self.snr[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 1, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.snr[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 2, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.range[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 3, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.range[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 4, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.pings[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 5, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.pings[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 6, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.amp[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 7, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.amp[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 8, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.corr[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 9, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.corr[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 10, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.beam_vel[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 11, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.beam_vel[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 12, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.instr_vel[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 13, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.instr_vel[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 14, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))

            self.earth_vel[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 15, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.earth_vel[1] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 16, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
        elif self.num_beams == 1:
            self.snr[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 1, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.range[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 2, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.pings[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 3, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.amp[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 4, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.corr[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 5, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.beam_vel[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 6, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.instr_vel[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 7, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))
            self.earth_vel[0] = (RtbRoweEns.get_float(packet_pointer + RtbRoweEns.BYTES_IN_FLOAT * 8, RtbRoweEns.BYTES_IN_FLOAT, ens_bytes))


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
        self.gga_delta_time = 0.0
        self.gga_header = ""
        self.utc = 0.0
        self.lat_deg = 0.0
        self.lat_ref = ""
        self.lon_deg = 0.0
        self.lon_ref = ""
        self.corr_qual = 0.0
        self.num_sats = 0.0
        self.hdop = 0.0
        self.alt = 0.0
        self.alt_unit = ""
        self.geoid = ""
        self.geoid_unit = ""
        self.d_gps_age = 0.0
        self.ref_stat_id = 0.0

        # VTG
        self.vtg_delta_time = 0
        self.vtg_header = ""
        self.course_true = 0.0
        self.true_indicator = ""
        self.course_mag = 0.0
        self.mag_indicator = ""
        self.speed_knots = 0.0
        self.knots_indicator = ""
        self.speed_kph = 0.0
        self.kph_indicator = ""
        self.mode_indicator = ""

        # HDT
        self.hdt_header = ""
        self.heading = 0.0
        self.rel_true_north = ""

    def decode(self, ens_bytes: list, name_len: int = 8):
        """
        Decode the NMEA dataset.  This will be the raw NMEA messages
        from the ADCP containing GPS data.
        :param ens_bytes Bytes for dataset.
        :param name_len: Name length to get the start location.
        """
        packet_pointer = RtbRoweEns.get_base_data_size(name_len)

        # Convert all the messages to a string
        nmea_str = str(ens_bytes[packet_pointer:], "UTF-8")

        # Decode each NMEA message
        for msg in nmea_str.split():
            self.decode_nmea(msg)

        # Convert all the list to numpy array for better storage
        self.gga = np.array(self.gga)
        self.gsa = np.array(self.gsa)
        self.vtg = np.array(self.vtg)
        self.dbt = np.array(self.dbt)
        self.hdt = np.array(self.hdt)

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
                self.gga.append(nmea_str)
                self.decode_gga(nmea_str)
            if 'gsa' in nmea_str or 'GSA' in nmea_str:
                self.gsa.append(nmea_str)
            if 'vtg' in nmea_str or 'VTG' in nmea_str:
                self.vtg.append(nmea_str)
                self.decode_vtg(nmea_str)
            if 'dbt' in nmea_str or 'DBT' in nmea_str:
                self.dbt.append(nmea_str)
            if 'hdt' in nmea_str or 'HDT' in nmea_str:
                self.hdt.append(nmea_str)
                self.decode_hdt(nmea_str)

    def decode_gga(self, nmea_str: str):
        """
        Decode GGA message.  Update the variables.

        :param nmea_str NMEA string.
        """
        temp_array = np.array(nmea_str.split(','))
        temp_array[temp_array == '999.9'] = ''

        try:
            #self.gga_delta_time = delta_time
            self.gga_header = temp_array[0]
            self.utc = float(temp_array[1])
            lat_str = temp_array[2]
            lat_deg = float(lat_str[0:2])
            lat_deg = lat_deg + float(lat_str[2:]) / 60
            self.lat_deg = lat_deg
            self.lat_ref = temp_array[3]
            lon_str = temp_array[4]
            lon_num = float(lon_str)
            lon_deg = np.floor(lon_num / 100)
            lon_deg = lon_deg + (((lon_num / 100.) - lon_deg) * 100.) / 60.
            self.lon_deg = lon_deg
            self.lon_ref = temp_array[5]
            self.corr_qual = float(temp_array[6])
            self.num_sats = float(temp_array[7])
            self.hdop = float(temp_array[8])
            self.alt = float(temp_array[9])
            self.alt_unit = temp_array[10]
            self.geoid = temp_array[11]
            self.geoid_unit = temp_array[12]
            self.d_gps_age = float(temp_array[13])
            idx_star = temp_array[14].find('*')
            self.ref_stat_id= float(temp_array[15][:idx_star])

        except (ValueError, EOFError, IndexError):
            pass

    def decode_gga(self, nmea_str: str):
        """
        Decode GGA message.  Update the variables.

        :param nmea_str NMEA string.
        """
        temp_array = np.array(nmea_str.split(','))
        temp_array[temp_array == '999.9'] = ''

        try:
            # self.gga_delta_time = delta_time
            self.gga_header = temp_array[0]
            self.utc = float(temp_array[1])
            lat_str = temp_array[2]
            lat_deg = float(lat_str[0:2])
            lat_deg = lat_deg + float(lat_str[2:]) / 60
            self.lat_deg = lat_deg
            self.lat_ref = temp_array[3]
            lon_str = temp_array[4]
            lon_num = float(lon_str)
            lon_deg = np.floor(lon_num / 100)
            lon_deg = lon_deg + (((lon_num / 100.) - lon_deg) * 100.) / 60.
            self.lon_deg = lon_deg
            self.lon_ref = temp_array[5]
            self.corr_qual = float(temp_array[6])
            self.num_sats = float(temp_array[7])
            self.hdop = float(temp_array[8])
            self.alt = float(temp_array[9])
            self.alt_unit = temp_array[10]
            self.geoid = temp_array[11]
            self.geoid_unit = temp_array[12]
            self.d_gps_age = float(temp_array[13])
            idx_star = temp_array[14].find('*')
            self.ref_stat_id = float(temp_array[15][:idx_star])

        except (ValueError, EOFError, IndexError):
            pass

    def decode_vtg(self, nmea_str: str):
        """
        Decode the VTG message and set all the variables.

        :param nmea_str: NMEA string.
        """

        temp_array = np.array(nmea_str.split(','))
        temp_array[temp_array == '999.9'] = ''

        try:
            #self.vtg_delta_time = delta_time
            self.vtg_header = temp_array[0]
            self.course_true = Nmea.valid_number(temp_array[1])
            self.true_indicator = temp_array[2]
            self.course_mag = Nmea.valid_number(temp_array[3])
            self.mag_indicator = temp_array[4]
            self.speed_knots = Nmea.valid_number(temp_array[5])
            self.knots_indicator = temp_array[6]
            self.speed_kph = Nmea.valid_number(temp_array[7])
            self.kph_indicator = temp_array[8]
            idx_star = temp_array[9].find('*')
            self.mode_indicator = temp_array[9][:idx_star]

        except (ValueError, EOFError, IndexError):
            pass

    def decode_hdt(self, nmea_str: str):
        """
        Decode the HDT message and set all the variables.

        :param nmea_str: NMEA string.
        """

        temp_array = np.array(nmea_str.split(','))
        temp_array[temp_array == '999.9'] = ''

        try:
            # self.vtg_delta_time = delta_time
            self.hdt_header = temp_array[0]
            self.heading = Nmea.valid_number(temp_array[1])
            idx_star = temp_array[2].find('*')
            self.rel_true_north = temp_array[2][:idx_star]

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


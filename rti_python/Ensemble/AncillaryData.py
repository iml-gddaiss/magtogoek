from rti_python.Ensemble.Ensemble import Ensemble
import logging
from pandas import DataFrame


class AncillaryData:
    """
    Ancillary Data DataSet.
    Float values that give details about the ensemble.
    """

    def __init__(self, num_elements=19, element_multiplier=1):
        self.ds_type = 10                   # Float
        self.num_elements = num_elements
        self.element_multiplier = element_multiplier
        self.image = 0
        self.name_len = 8
        self.Name = "E000009\0"

        self.FirstBinRange = 0.0        # Blank.  Depth to the first bin in meters.
        self.BinSize = 0.0              # Size of a bin in meters.
        self.FirstPingTime = 0.0        # First Ping Time in seconds.
        self.LastPingTime = 0.0         # Last Ping Time in seconds.  (If averaging pings, this will be the last ping)
        self.Heading = 0.0              # Heading in degrees.
        self.Pitch = 0.0                # Pitch in degrees.
        self.Roll = 0.0                 # Roll in degrees.
        self.WaterTemp = 0.0            # Water Temperature in fahrenheit
        self.SystemTemp = 0.0           # System Temperature in fahrenheit
        self.Salinity = 0.0             # Water Salinity set by the user in PPT
        self.Pressure = 0.0             # Pressure from pressure sensor in Pascals
        self.TransducerDepth = 0.0      # Transducer Depth, used by Pressure sensor in meters
        self.SpeedOfSound = 0.0         # Speed of Sound in m/s.
        self.RawMagFieldStrength = 0.0  # Raw magnetic field strength (uT) (micro Tesla)
        self.RawMagFieldStrength2 = 0.0 # Raw magnetic field strength (uT) (micro Tesla)
        self.RawMagFieldStrength3 = 0.0 # Raw magnetic field strength (uT) (micro Tesla)
        self.PitchGravityVector = 0.0   # Pitch Gravity Vector
        self.RollGravityVector = 0.0    # Roll Gravity Vector
        self.VerticalGravityVector = 0.0 # Vertical Gravity Vector

    def decode(self, data):
        """
        Take the data bytearray.  Decode the data to populate
        the values.
        :param data: Bytearray for the dataset.
        """
        packet_pointer = Ensemble.GetBaseDataSize(self.name_len)

        self.FirstBinRange = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 0, Ensemble().BytesInFloat, data)
        self.BinSize = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 1, Ensemble().BytesInFloat, data)
        self.FirstPingTime = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 2, Ensemble().BytesInFloat, data)
        self.LastPingTime = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 3, Ensemble().BytesInFloat, data)
        self.Heading = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 4, Ensemble().BytesInFloat, data)
        self.Pitch = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 5, Ensemble().BytesInFloat, data)
        self.Roll = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 6, Ensemble().BytesInFloat, data)
        self.WaterTemp = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 7, Ensemble().BytesInFloat, data)
        self.SystemTemp = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 8, Ensemble().BytesInFloat, data)
        self.Salinity = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 9, Ensemble().BytesInFloat, data)
        self.Pressure = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 10, Ensemble().BytesInFloat, data)
        self.TransducerDepth = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 11, Ensemble().BytesInFloat, data)
        self.SpeedOfSound = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 12, Ensemble().BytesInFloat, data)

        if self.num_elements > 13:
            self.RawMagFieldStrength = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 13, Ensemble().BytesInFloat, data)
            self.RawMagFieldStrength2 = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 14, Ensemble().BytesInFloat, data)
            self.RawMagFieldStrength3 = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 15, Ensemble().BytesInFloat, data)
            self.PitchGravityVector = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 16, Ensemble().BytesInFloat, data)
            self.RollGravityVector = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 17, Ensemble().BytesInFloat, data)
            self.VerticalGravityVector = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 18, Ensemble().BytesInFloat, data)

        logging.debug(self.FirstBinRange)
        logging.debug(self.BinSize)
        logging.debug(self.Heading)
        logging.debug(self.Pitch)
        logging.debug(self.Roll)
        logging.debug(self.Salinity)
        logging.debug(self.SpeedOfSound)

    def encode(self):
        """
        Encode the data into RTB format.
        :return:
        """
        result = []

        # Generate header
        result += Ensemble.generate_header(self.ds_type,
                                           self.num_elements,
                                           self.element_multiplier,
                                           self.image,
                                           self.name_len,
                                           self.Name)

        # Add the data
        result += Ensemble.float_to_bytes(self.FirstBinRange)
        result += Ensemble.float_to_bytes(self.BinSize)
        result += Ensemble.float_to_bytes(self.FirstPingTime)
        result += Ensemble.float_to_bytes(self.LastPingTime)
        result += Ensemble.float_to_bytes(self.Heading)
        result += Ensemble.float_to_bytes(self.Pitch)
        result += Ensemble.float_to_bytes(self.Roll)
        result += Ensemble.float_to_bytes(self.WaterTemp)
        result += Ensemble.float_to_bytes(self.SystemTemp)
        result += Ensemble.float_to_bytes(self.Salinity)
        result += Ensemble.float_to_bytes(self.Pressure)
        result += Ensemble.float_to_bytes(self.TransducerDepth)
        result += Ensemble.float_to_bytes(self.SpeedOfSound)
        result += Ensemble.float_to_bytes(self.RawMagFieldStrength)
        result += Ensemble.float_to_bytes(self.RawMagFieldStrength2)
        result += Ensemble.float_to_bytes(self.RawMagFieldStrength3)
        result += Ensemble.float_to_bytes(self.PitchGravityVector)
        result += Ensemble.float_to_bytes(self.RollGravityVector)
        result += Ensemble.float_to_bytes(self.VerticalGravityVector)

        return result

    def encode_csv(self, dt, ss_code, ss_config, blank=0, bin_size=0):
        """
        Encode into CSV format.
        :param dt: Datetime object.
        :param ss_code: Subsystem code.
        :param ss_config: Subsystem Configuration
        :param blank: Blank or first bin position in meters.
        :param bin_size: Bin size in meters.
        :return: List of CSV lines.
        """
        str_result = []

        # Create the CSV strings
        str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_FIRST_PING_TIME, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.FirstPingTime))
        str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_LAST_PING_TIME, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.LastPingTime))
        str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_HEADING, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.Heading))
        str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_PITCH, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.Pitch))
        str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_ROLL, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.Roll))
        str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_WATER_TEMP, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.WaterTemp))
        str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_SYS_TEMP, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.SystemTemp))
        str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_PRESSURE, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.Pressure))
        str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_XDCR_DEPTH, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.TransducerDepth))
        str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_SOS, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.SpeedOfSound))

        return str_result

    def encode_df(self, dt, ss_code, ss_config):
        """
        Encode into Dataframe format.
        :param dt: Datetime object.
        :param ss_code: Subsystem code.
        :param ss_config: Subsystem Configuration
        :return: Dataframe of the data.
        """
        df_result = []

        # Create the Dataframe strings
        df_result.append([dt, Ensemble.CSV_FIRST_PING_TIME, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.FirstPingTime])
        df_result.append([dt, Ensemble.CSV_LAST_PING_TIME, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.LastPingTime])
        df_result.append([dt, Ensemble.CSV_HEADING, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.Heading])
        df_result.append([dt, Ensemble.CSV_PITCH, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.Pitch])
        df_result.append([dt, Ensemble.CSV_ROLL, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.Roll])
        df_result.append([dt, Ensemble.CSV_WATER_TEMP, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.WaterTemp])
        df_result.append([dt, Ensemble.CSV_SYS_TEMP, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.SystemTemp])
        df_result.append([dt, Ensemble.CSV_PRESSURE, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.Pressure])
        df_result.append([dt, Ensemble.CSV_XDCR_DEPTH, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.TransducerDepth])
        df_result.append([dt, Ensemble.CSV_SOS, ss_code, ss_config, 0, 0, self.FirstBinRange, self.BinSize, self.SpeedOfSound])

        # Create the column names
        df_earth_columns = ["dt", "type", "ss_code", "ss_config", "bin_num", "beam", "blank", "bin_size", "val"]

        return DataFrame(df_result, columns=df_earth_columns)

    def is_upward_facing(self, min_roll: float = 0.0, max_roll: float = 20.0):
        """
        Check the roll value if it is near 0 degrees.  A value near
        zero means the ADCP is upward facing.
        Upward looking is around 0 degrees for roll.
        Downward looking is around 180 degrees for roll.

        :param min_roll: Minimum roll for upward looking taking absolute value.
        :param max_roll: Maximum roll for the upward looking taking absolute value.
        :return: TRUE if Upward facing.
        """

        # Check if the roll value is near 0
        if min_roll <= abs(self.Roll) <= max_roll:
            return True

        return False


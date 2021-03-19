from rti_python.Ensemble.Ensemble import Ensemble
import logging
from pandas import DataFrame


class SystemSetup:
    """
    System Setup DataSet.
    Float values that give details about the system setup.
    """

    def __init__(self, num_elements=25, element_multiplier=1):
        self.ds_type = 10                       # Float
        self.num_elements = num_elements
        self.element_multiplier = element_multiplier
        self.image = 0
        self.name_len = 8
        self.Name = "E000014\0"

        self.BtSamplesPerSecond = 0.0           # Bottom Track Samples Per Second
        self.BtSystemFreqHz = 0.0               # Bottom Track System Frequency (Hz)
        self.BtCPCE = 0.0                       # Bottom Track Cycles per Code Elements
        self.BtNCE = 0.0                        # Bottom Track Number of Code Elements
        self.BtRepeatN = 0.0                    # Bottom Track Number of Code Repeats
        self.WpSamplesPerSecond = 0.0           # Water Profile Samples per Second
        self.WpSystemFreqHz = 0.0               # Water Profile System Frequency (Hz)
        self.WpCPCE = 0.0                       # Water Profile Cycles per Code Element
        self.WpNCE = 0.0                        # Water Profile Number of Code Element
        self.WpRepeatN = 0.0                    # Water Profile Number of Code Repeats
        self.WpLagSamples = 0.0                 # Water Profile Lag Samples
        self.Voltage = 0.0                      # Voltage input to ADCP
        self.XmtVoltage = 0.0                   # Transmit Voltage
        self.BtBroadband = 0.0                  # Bottom Track Broadband
        self.BtLagLength = 0.0                  # Bottom Track Pulse to Pulse Lag (m)
        self.BtNarrowband = 0.0                 # Bottom Track Long Range Switch Depth (m)
        self.BtBeamMux = 0.0                    # Bottom Track Beam Multiplex
        self.WpBroadband = 0.0                  # Water Profile Mode
        self.WpLagLength = 0.0                  # Water Profile Lag Length
        self.WpTransmitBandwidth = 0.0          # Water Profile Transmit Bandwidth
        self.WpReceiveBandwidth = 0.0           # Water Profile Receive Bandwidth
        self.TransmitBoostNegVolt = 0.0         # Transmitter Boost Negative Voltage
        self.WpBeamMux = 0.0                    # WP Beam Mux
        self.Reserved = 0.0                     # Reserved
        self.Reserved1 = 0.0                    # Reserved

    def decode(self, data):
        """
        Take the data bytearray.  Decode the data to populate
        the values.
        :param data: Bytearray for the dataset.
        """
        packet_pointer = Ensemble.GetBaseDataSize(self.name_len)

        self.BtSamplesPerSecond = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 0, Ensemble().BytesInFloat, data)
        self.BtSystemFreqHz = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 1, Ensemble().BytesInFloat, data)
        self.BtCPCE = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 2, Ensemble().BytesInFloat, data)
        self.BtNCE = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 3, Ensemble().BytesInFloat, data)
        self.BtRepeatN = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 4, Ensemble().BytesInFloat, data)
        self.WpSamplesPerSecond = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 5, Ensemble().BytesInFloat, data)
        self.WpSystemFreqHz = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 6, Ensemble().BytesInFloat, data)
        self.WpCPCE = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 7, Ensemble().BytesInFloat, data)
        self.WpNCE = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 8, Ensemble().BytesInFloat, data)
        self.WpRepeatN = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 9, Ensemble().BytesInFloat, data)
        self.WpLagSamples = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 10, Ensemble().BytesInFloat, data)
        self.Voltage = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 11, Ensemble().BytesInFloat, data)

        if self.num_elements > 12:
            self.XmtVoltage = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 12, Ensemble().BytesInFloat, data)
            self.BtBroadband = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 13, Ensemble().BytesInFloat, data)
            self.BtLagLength = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 14, Ensemble().BytesInFloat, data)
            self.BtNarrowband = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 15, Ensemble().BytesInFloat, data)
            self.BtBeamMux = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 16, Ensemble().BytesInFloat, data)
            self.WpBroadband = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 17, Ensemble().BytesInFloat, data)
            self.WpLagLength = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 18, Ensemble().BytesInFloat, data)
            self.WpTransmitBandwidth = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 19, Ensemble().BytesInFloat, data)
            self.WpReceiveBandwidth = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 20, Ensemble().BytesInFloat, data)
            self.TransmitBoostNegVolt = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 21, Ensemble().BytesInFloat, data)
            self.WpBeamMux = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 22, Ensemble().BytesInFloat, data)
        if self.num_elements > 23:
            self.Reserved = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 23, Ensemble().BytesInFloat, data)
            self.Reserved1 = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 24, Ensemble().BytesInFloat, data)

        logging.debug(self.BtSamplesPerSecond)
        logging.debug(self.BtSystemFreqHz)
        logging.debug(self.BtCPCE)
        logging.debug(self.BtNCE)
        logging.debug(self.BtRepeatN)
        logging.debug(self.WpSamplesPerSecond)
        logging.debug(self.WpSystemFreqHz)
        logging.debug(self.WpCPCE)
        logging.debug(self.WpNCE)
        logging.debug(self.WpRepeatN)
        logging.debug(self.WpLagSamples)
        logging.debug(self.Voltage)
        logging.debug(self.XmtVoltage)
        logging.debug(self.BtBroadband)
        logging.debug(self.BtLagLength)
        logging.debug(self.BtNarrowband)
        logging.debug(self.BtBeamMux)
        logging.debug(self.WpBroadband)
        logging.debug(self.WpLagLength)
        logging.debug(self.WpTransmitBandwidth)
        logging.debug(self.WpReceiveBandwidth)

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
        result += Ensemble.float_to_bytes(self.BtSamplesPerSecond)
        result += Ensemble.float_to_bytes(self.BtSystemFreqHz)
        result += Ensemble.float_to_bytes(self.BtCPCE)
        result += Ensemble.float_to_bytes(self.BtNCE)
        result += Ensemble.float_to_bytes(self.BtRepeatN)
        result += Ensemble.float_to_bytes(self.WpSamplesPerSecond)
        result += Ensemble.float_to_bytes(self.WpSystemFreqHz)
        result += Ensemble.float_to_bytes(self.WpCPCE)
        result += Ensemble.float_to_bytes(self.WpNCE)
        result += Ensemble.float_to_bytes(self.WpRepeatN)
        result += Ensemble.float_to_bytes(self.WpLagSamples)
        result += Ensemble.float_to_bytes(self.Voltage)
        result += Ensemble.float_to_bytes(self.XmtVoltage)
        result += Ensemble.float_to_bytes(self.BtBroadband)
        result += Ensemble.float_to_bytes(self.BtLagLength)
        result += Ensemble.float_to_bytes(self.BtNarrowband)
        result += Ensemble.float_to_bytes(self.BtBeamMux)
        result += Ensemble.float_to_bytes(self.WpBroadband)
        result += Ensemble.float_to_bytes(self.WpLagLength)
        result += Ensemble.float_to_bytes(self.WpTransmitBandwidth)
        result += Ensemble.float_to_bytes(self.WpReceiveBandwidth)
        result += Ensemble.float_to_bytes(self.TransmitBoostNegVolt)
        result += Ensemble.float_to_bytes(self.WpBeamMux)
        result += Ensemble.float_to_bytes(self.Reserved)
        result += Ensemble.float_to_bytes(self.Reserved1)

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
        str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_VOLTAGE, ss_code, ss_config, 0, 0, blank, bin_size, self.Voltage))

        return str_result

    def encode_df(self, dt, ss_code, ss_config):
        """
        Encode into Dataframe format.
        :param dt: Datetime object.
        :param ss_code: Subsystem code.
        :param ss_config: Subsystem Configuration
        :return: List of CSV lines.
        """
        df_result = []

        # Create the CSV strings
        df_result.append([dt, Ensemble.CSV_VOLTAGE, ss_code, ss_config, 0, 0, self.Voltage])

        # Create the column names
        df_earth_columns = ["dt", "type", "ss_code", "ss_config", "bin_num", "beam", "val"]

        return DataFrame(df_result, columns=df_earth_columns)

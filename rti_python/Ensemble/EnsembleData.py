import struct
from rti_python.Ensemble.Ensemble import Ensemble
import logging
from datetime import datetime


class EnsembleData:
    """
    Ensemble Data DataSet.
    Integer values that give details about the ensemble.
    """

    def __init__(self, num_elements=23, element_multiplier=1):
        self.ds_type = 20
        self.num_elements = num_elements
        self.element_multiplier = element_multiplier
        self.image = 0
        self.name_len = 8
        self.Name = "E000008\0"

        self.EnsembleNumber = 0
        self.NumBins = 0
        self.NumBeams = 0
        self.DesiredPingCount = 0
        self.ActualPingCount = 0
        self.SerialNumber = ""
        self.SysFirmwareMajor = 0
        self.SysFirmwareMinor = 0
        self.SysFirmwareRevision = 0
        self.SysFirmwareSubsystemCode = ""
        self.SubsystemConfig = 0
        self.Status = 0
        self.Year = 0
        self.Month = 0
        self.Day = 0
        self.Hour = 0
        self.Minute = 0
        self.Second = 0
        self.HSec = 0

    def decode(self, data):
        """
        Take the data bytearray.  Decode the data to populate
        the values.
        :param data: Bytearray for the dataset.
        """
        packet_pointer = Ensemble.GetBaseDataSize(self.name_len)

        self.EnsembleNumber = Ensemble.GetInt32(packet_pointer + Ensemble().BytesInInt32 * 0, Ensemble().BytesInInt32, data)
        self.NumBins = Ensemble.GetInt32(packet_pointer + Ensemble().BytesInInt32 * 1, Ensemble().BytesInInt32, data)
        self.NumBeams = Ensemble.GetInt32(packet_pointer + Ensemble().BytesInInt32 * 2, Ensemble().BytesInInt32, data)
        self.DesiredPingCount = Ensemble.GetInt32(packet_pointer + Ensemble().BytesInInt32 * 3, Ensemble().BytesInInt32, data)
        self.ActualPingCount = Ensemble.GetInt32(packet_pointer + Ensemble().BytesInInt32 * 4, Ensemble().BytesInInt32, data)
        self.Status = Ensemble.GetInt32(packet_pointer + Ensemble().BytesInInt32 * 5, Ensemble().BytesInInt32, data)
        self.Year = Ensemble.GetInt32(packet_pointer + Ensemble().BytesInInt32 * 6, Ensemble().BytesInInt32, data)
        self.Month = Ensemble.GetInt32(packet_pointer + Ensemble().BytesInInt32 * 7, Ensemble().BytesInInt32, data)
        self.Day = Ensemble.GetInt32(packet_pointer + Ensemble().BytesInInt32 * 8, Ensemble().BytesInInt32, data)
        self.Hour = Ensemble.GetInt32(packet_pointer + Ensemble().BytesInInt32 * 9, Ensemble().BytesInInt32, data)
        self.Minute = Ensemble.GetInt32(packet_pointer + Ensemble().BytesInInt32 * 10, Ensemble().BytesInInt32, data)
        self.Second = Ensemble.GetInt32(packet_pointer + Ensemble().BytesInInt32 * 11, Ensemble().BytesInInt32, data)
        self.HSec = Ensemble.GetInt32(packet_pointer + Ensemble().BytesInInt32 * 12, Ensemble().BytesInInt32, data)

        self.SerialNumber = str(data[packet_pointer+Ensemble().BytesInInt32*13:packet_pointer+Ensemble().BytesInInt32*21], "UTF-8")
        self.SysFirmwareRevision = struct.unpack("B", data[packet_pointer+Ensemble().BytesInInt32*21 + 0:packet_pointer+Ensemble().BytesInInt32*21 + 1])[0]
        self.SysFirmwareMinor = struct.unpack("B", data[packet_pointer+Ensemble().BytesInInt32*21 + 1:packet_pointer+Ensemble().BytesInInt32*21 + 2])[0]
        self.SysFirmwareMajor = struct.unpack("B", data[packet_pointer + Ensemble().BytesInInt32 * 21 + 2:packet_pointer + Ensemble().BytesInInt32 * 21 + 3])[0]
        self.SysFirmwareSubsystemCode = str(data[packet_pointer + Ensemble().BytesInInt32 * 21 + 3:packet_pointer + Ensemble().BytesInInt32 * 21 + 4], "UTF-8")

        self.SubsystemConfig = struct.unpack("B", data[packet_pointer + Ensemble().BytesInInt32 * 22 + 3:packet_pointer + Ensemble().BytesInInt32 * 22 + 4])[0]

        logging.debug(self.EnsembleNumber)
        logging.debug(str(self.Month) + "/" + str(self.Day) + "/" + str(self.Year) + "  " + str(self.Hour) + ":" + str(self.Minute) + ":" + str(self.Second) + "." + str(self.HSec))
        logging.debug(self.SerialNumber)
        logging.debug(str(self.SysFirmwareMajor) + "." + str(self.SysFirmwareMinor) + "." + str(self.SysFirmwareRevision) + "-" + str(self.SysFirmwareSubsystemCode))
        logging.debug(self.SubsystemConfig)

    def datetime_str(self):
        """
        Return the date and time as a string.
        :return: Date time string.  2013/07/30 21:00:00.00
        """
        return str(self.Year).zfill(4) + "/" + str(self.Month).zfill(2) + "/" + str(self.Day).zfill(2) + " " + str(self.Hour).zfill(2) + ":" + str(self.Minute).zfill(2) + ":" + str(self.Second).zfill(2) + "." + str(self.HSec).zfill(2)

    def datetime(self):
        """
        Create a datetime object from the date and time of the ensemble.
        If an error occurs, use the current date and time.
        :return: datetime of the ensemble.
        """
        try:
            dt = datetime(self.Year, self.Month, self.Day, self.Hour, self.Minute, self.Second, self.HSec * 10000)
            return dt
        except Exception:
            return datetime.now()

    def firmware_str(self):
        """
        Create a string of the firmware version and subsystem code.
        :return:
        """
        return "{0}.{1}.{2} - {3}".format(self.SysFirmwareMajor, self.SysFirmwareMinor, self.SysFirmwareRevision, self.SysFirmwareSubsystemCode)

    def status_str(self):
        """
        Convert the status value to a string.
        :return: Status value as a string.
        """
        BT_LONG_LAG = 0x0001;
        BT_BT_3BEAM_SOLUTION = 0x0002;
        BT_HOLD = 0x0004;
        BT_SEARCHING = 0x0008;
        BT_LR = 0x0010;
        BT_COAST = 0x0020;
        BT_PROOF = 0x0040;
        OVERTEMP = 0x0020;
        BT_LOWGAIN = 0x0080;
        ERR_HEADING_SENSOR = 0x0100;
        ERR_PRESSURE_SENSOR = 0x0200;
        ERR_POWER_DOWN_FAILURE = 0x0400;
        ERR_NONVOLATILE_DATA = 0x0800;
        ERR_RTC = 0x1000;
        ERR_TEMPERATURE = 0x2000;
        ERR_RCVR_DATA = 0x4000;
        ERR_RCVR_TIMEOUT = 0x8000;
        ERR_LOW_VOLTAGE = 0xFFFF;

        result_str = ""
        if self.Status & BT_LONG_LAG:
            result_str += "Bottom Track Long Lag, "
        if self.Status & BT_BT_3BEAM_SOLUTION:
            result_str += "Bottom Track 3 Beam Solution"
        if self.Status & BT_HOLD:
            result_str += "Bottom Track Search: HOLD, "
        if self.Status & BT_SEARCHING:
            result_str += "Bottom Track Search: SEARCHING, "
        if self.Status & BT_LR:
            result_str += "Bottom Track Long Range [Narrowband Mode], "
        if self.Status & BT_COAST:
            result_str += "Bottom Track Coast, "
        if self.Status & BT_PROOF:
            result_str += "Bottom Track Search: PROOF, "
        if self.Status & OVERTEMP:
            result_str += "Over Temperature, "
        if self.Status & BT_LOWGAIN:
            result_str += "Bottom Track Low Gain (Shallow Water Mode), "
        if self.Status & ERR_HEADING_SENSOR:
            result_str += "Heading Sensor Error, "
        if self.Status & ERR_PRESSURE_SENSOR:
            result_str += "Pressure Sensor Error, "
        if self.Status & ERR_POWER_DOWN_FAILURE:
            result_str += "Error Powering Down, "
        if self.Status & ERR_NONVOLATILE_DATA:
            result_str += "Error in NonVolatile Data: "
        if self.Status & ERR_RTC:
            result_str += "RTC Error, "
        if self.Status & ERR_TEMPERATURE:
            result_str += "Temperature Error, "
        if self.Status & ERR_RCVR_DATA:
            result_str += "Receiver Data Error, "
        if self.Status & ERR_RCVR_TIMEOUT:
            result_str += "Receiver Timeout, "
        if self.Status == ERR_LOW_VOLTAGE:
            result_str += "Low Voltage, "

        return result_str

    def is_vertical_beam(self):
        """
        Determine if the current ensemble is a vertical beam ensemble or other type.
        :return: TRUE = Vertical Beam Ensemble
        :rtype: bool
        """
        if self.SysFirmwareSubsystemCode == "9" or \
                self.SysFirmwareSubsystemCode == "A" or \
                self.SysFirmwareSubsystemCode == "B" or \
                self.SysFirmwareSubsystemCode == "C" or \
                self.SysFirmwareSubsystemCode == "D" or \
                self.SysFirmwareSubsystemCode == "E" or \
                self.SysFirmwareSubsystemCode == "F" or \
                self.SysFirmwareSubsystemCode == "G":
            return True

        return False

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
        result += Ensemble.int32_to_bytes(self.EnsembleNumber)
        result += Ensemble.int32_to_bytes(self.NumBins)
        result += Ensemble.int32_to_bytes(self.NumBeams)
        result += Ensemble.int32_to_bytes(self.DesiredPingCount)
        result += Ensemble.int32_to_bytes(self.ActualPingCount)
        result += Ensemble.int32_to_bytes(self.Status)
        result += Ensemble.int32_to_bytes(self.Year)
        result += Ensemble.int32_to_bytes(self.Month)
        result += Ensemble.int32_to_bytes(self.Day)
        result += Ensemble.int32_to_bytes(self.Hour)
        result += Ensemble.int32_to_bytes(self.Minute)
        result += Ensemble.int32_to_bytes(self.Second)
        result += Ensemble.int32_to_bytes(self.HSec)
        result += self.SerialNumber.encode("UTF-8")
        result += bytes([self.SysFirmwareRevision])
        result += bytes([self.SysFirmwareMinor])
        result += bytes([self.SysFirmwareMajor])
        result += self.SysFirmwareSubsystemCode.encode("UTF-8")
        result += bytes([0])
        result += bytes([0])
        result += bytes([0])
        result += bytes([self.SubsystemConfig])

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
        str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_STATUS, ss_code, ss_config, 0, 0, blank, bin_size, self.Status))

        return str_result

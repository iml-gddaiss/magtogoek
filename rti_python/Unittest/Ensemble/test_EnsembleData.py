import pytest
import datetime
import re
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Ensemble.EnsembleData import EnsembleData


def test_generate_header():

    value_type = 20             # Int
    num_elements = 19           # 19 elements
    element_multiplier = 1      # no multiplier
    imag = 0                    # NOT USED
    name_length = 8             # Length of name
    name = "E000008\0"          # Ensemble Dataset name

    header = Ensemble.generate_header(value_type,
                                      num_elements,
                                      element_multiplier,
                                      imag,
                                      name_length,
                                      name)

    # Value type
    assert 0x14 == header[0]
    assert 0x0 == header[1]
    assert 0x0 == header[2]
    assert 0x0 == header[3]

    # Num Elements
    assert 0x13 == header[4]
    assert 0x0 == header[5]
    assert 0x0 == header[6]
    assert 0x0 == header[7]

    # Element Multiplier
    assert 0x1 == header[8]
    assert 0x0 == header[9]
    assert 0x0 == header[10]
    assert 0x0 == header[11]

    # Imag
    assert 0x0 == header[12]
    assert 0x0 == header[13]
    assert 0x0 == header[14]
    assert 0x0 == header[15]

    # Name Length
    assert 0x8 == header[16]
    assert 0x0 == header[17]
    assert 0x0 == header[18]
    assert 0x0 == header[19]

    # Name
    assert ord('E') == header[20]
    assert ord('0') == header[21]
    assert ord('0') == header[22]
    assert ord('0') == header[23]
    assert ord('0') == header[24]
    assert ord('0') == header[25]
    assert ord('8') == header[26]
    assert ord('\0') == header[27]


def test_ensembledata():
    ens = EnsembleData()
    ens.EnsembleNumber = 2668
    ens.NumBins = 37
    ens.NumBeams = 4
    ens.DesiredPingCount = 45
    ens.ActualPingCount = 46
    ens.SerialNumber = "01H00000000000000000000000999999"
    ens.SysFirmwareMajor = 2
    ens.SysFirmwareMinor = 11
    ens.SysFirmwareRevision = 5
    ens.SysFirmwareSubsystemCode = "A"
    ens.SubsystemConfig = 3
    ens.Status = 0x0120
    ens.Year = 2019
    ens.Month = 3
    ens.Day = 9
    ens.Hour = 12
    ens.Minute = 23
    ens.Second = 24
    ens.HSec = 33

    # Populate data

    result = ens.encode()

    # Value type
    assert 0x14 == result[0]
    assert 0x0 == result[1]
    assert 0x0 == result[2]
    assert 0x0 == result[3]

    # Num Elements
    assert 0x17 == result[4]
    assert 0x0 == result[5]
    assert 0x0 == result[6]
    assert 0x0 == result[7]

    # Element Multiplier
    assert 0x1 == result[8]
    assert 0x0 == result[9]
    assert 0x0 == result[10]
    assert 0x0 == result[11]

    # Imag
    assert 0x0 == result[12]
    assert 0x0 == result[13]
    assert 0x0 == result[14]
    assert 0x0 == result[15]

    # Name Length
    assert 0x8 == result[16]
    assert 0x0 == result[17]
    assert 0x0 == result[18]
    assert 0x0 == result[19]

    # Name
    assert ord('E') == result[20]
    assert ord('0') == result[21]
    assert ord('0') == result[22]
    assert ord('0') == result[23]
    assert ord('0') == result[24]
    assert ord('0') == result[25]
    assert ord('8') == result[26]
    assert ord('\0') == result[27]

    # Length
    assert len(result) == (23 * Ensemble.BytesInInt32) + 28

    # Data
    # Ensemble Number
    assert Ensemble.int32_to_bytes(2668)[0] == result[28]
    assert Ensemble.int32_to_bytes(2668)[1] == result[29]
    assert Ensemble.int32_to_bytes(2668)[2] == result[30]
    assert Ensemble.int32_to_bytes(2668)[3] == result[31]

    # Num Bins
    assert Ensemble.int32_to_bytes(37)[0] == result[32]
    assert Ensemble.int32_to_bytes(37)[1] == result[33]
    assert Ensemble.int32_to_bytes(37)[2] == result[34]
    assert Ensemble.int32_to_bytes(37)[3] == result[35]

    # Num Beams
    assert Ensemble.int32_to_bytes(4)[0] == result[36]
    assert Ensemble.int32_to_bytes(4)[1] == result[37]
    assert Ensemble.int32_to_bytes(4)[2] == result[38]
    assert Ensemble.int32_to_bytes(4)[3] == result[39]

    # Desired Ping Count
    assert Ensemble.int32_to_bytes(45)[0] == result[40]
    assert Ensemble.int32_to_bytes(45)[1] == result[41]
    assert Ensemble.int32_to_bytes(45)[2] == result[42]
    assert Ensemble.int32_to_bytes(45)[3] == result[43]

    # Actual Ping Count
    assert Ensemble.int32_to_bytes(46)[0] == result[44]
    assert Ensemble.int32_to_bytes(46)[1] == result[45]
    assert Ensemble.int32_to_bytes(46)[2] == result[46]
    assert Ensemble.int32_to_bytes(46)[3] == result[47]

    # Status
    assert Ensemble.int32_to_bytes(288)[0] == result[48]
    assert Ensemble.int32_to_bytes(288)[1] == result[49]
    assert Ensemble.int32_to_bytes(288)[2] == result[50]
    assert Ensemble.int32_to_bytes(288)[3] == result[51]

    # Year
    assert Ensemble.int32_to_bytes(2019)[0] == result[52]
    assert Ensemble.int32_to_bytes(2019)[1] == result[53]
    assert Ensemble.int32_to_bytes(2019)[2] == result[54]
    assert Ensemble.int32_to_bytes(2019)[3] == result[55]

    # Month
    assert Ensemble.int32_to_bytes(3)[0] == result[56]
    assert Ensemble.int32_to_bytes(3)[1] == result[57]
    assert Ensemble.int32_to_bytes(3)[2] == result[58]
    assert Ensemble.int32_to_bytes(3)[3] == result[59]

    # Day
    assert Ensemble.int32_to_bytes(9)[0] == result[60]
    assert Ensemble.int32_to_bytes(9)[1] == result[61]
    assert Ensemble.int32_to_bytes(9)[2] == result[62]
    assert Ensemble.int32_to_bytes(9)[3] == result[63]

    # Hour
    assert Ensemble.int32_to_bytes(12)[0] == result[64]
    assert Ensemble.int32_to_bytes(12)[1] == result[65]
    assert Ensemble.int32_to_bytes(12)[2] == result[66]
    assert Ensemble.int32_to_bytes(12)[3] == result[67]

    # Minute
    assert Ensemble.int32_to_bytes(23)[0] == result[68]
    assert Ensemble.int32_to_bytes(23)[1] == result[69]
    assert Ensemble.int32_to_bytes(23)[2] == result[70]
    assert Ensemble.int32_to_bytes(23)[3] == result[71]

    # Second
    assert Ensemble.int32_to_bytes(24)[0] == result[72]
    assert Ensemble.int32_to_bytes(24)[1] == result[73]
    assert Ensemble.int32_to_bytes(24)[2] == result[74]
    assert Ensemble.int32_to_bytes(24)[3] == result[75]

    # HSecond
    assert Ensemble.int32_to_bytes(33)[0] == result[76]
    assert Ensemble.int32_to_bytes(33)[1] == result[77]
    assert Ensemble.int32_to_bytes(33)[2] == result[78]
    assert Ensemble.int32_to_bytes(33)[3] == result[79]

    # Serial Number
    serial = ens.SerialNumber.encode()
    assert serial[0] == result[80]
    assert serial[1] == result[81]
    assert serial[2] == result[82]
    assert serial[3] == result[83]
    assert serial[4] == result[84]
    assert serial[5] == result[85]
    assert serial[6] == result[86]
    assert serial[7] == result[87]
    assert serial[8] == result[88]
    assert serial[9] == result[89]
    assert serial[10] == result[90]
    assert serial[11] == result[91]
    assert serial[12] == result[92]
    assert serial[13] == result[93]
    assert serial[14] == result[94]
    assert serial[15] == result[95]
    assert serial[16] == result[96]
    assert serial[17] == result[97]
    assert serial[18] == result[98]
    assert serial[19] == result[99]
    assert serial[20] == result[100]
    assert serial[21] == result[101]
    assert serial[22] == result[102]
    assert serial[23] == result[103]
    assert serial[24] == result[104]
    assert serial[25] == result[105]
    assert serial[26] == result[106]
    assert serial[27] == result[107]
    assert serial[28] == result[108]
    assert serial[29] == result[109]
    assert serial[30] == result[110]
    assert serial[31] == result[111]

    str_serial = bytes(result[80:112]).decode("UTF-8")
    assert "01H00000000000000000000000999999" == str_serial

    # Firmware
    assert 5 == result[112]         # Revision
    assert 11 == result[113]        # Minor
    assert 2 == result[114]         # Major
    assert 65 == result[115]        # System Code

    char_ss_code = chr(result[115])
    assert 'A' == char_ss_code
    str_ss_code = bytes(result[115:116]).decode("UTF-8")
    assert 'A' == str_ss_code

    # Subsystem Config
    assert 0 == result[116]
    assert 0 == result[117]
    assert 0 == result[118]
    assert 3 == result[119]


def test_encode_csv():

    ens = EnsembleData()
    ens.EnsembleNumber = 2668
    ens.NumBins = 37
    ens.NumBeams = 4
    ens.DesiredPingCount = 45
    ens.ActualPingCount = 46
    ens.SerialNumber = 386
    ens.SysFirmwareMajor = 2
    ens.SysFirmwareMinor = 11
    ens.SysFirmwareRevision = 5
    ens.SysFirmwareSubsystemCode = 'A'
    ens.SubsystemConfig = 1
    ens.Status = 0x0120
    ens.Year = 2019
    ens.Month = 3
    ens.Day = 9
    ens.Hour = 12
    ens.Minute = 23
    ens.Second = 24
    ens.HSec = 33

    # Populate data

    dt = datetime.datetime.now()

    # Create CSV lines
    result = ens.encode_csv(dt, 'A', 1)

    # Check the csv data
    for line in result:
        if Ensemble.CSV_STATUS in line:
            assert bool(re.search(str(288), line))
            assert bool(re.search(str(0), line))


def test_encode_decode():
    ens = EnsembleData()
    ens.EnsembleNumber = 2668
    ens.NumBins = 37
    ens.NumBeams = 4
    ens.DesiredPingCount = 45
    ens.ActualPingCount = 46
    ens.SerialNumber = "01H00000000000000000000000999999"
    ens.SysFirmwareMajor = 2
    ens.SysFirmwareMinor = 11
    ens.SysFirmwareRevision = 5
    ens.SysFirmwareSubsystemCode = "A"
    ens.SubsystemConfig = 3
    ens.Status = 9
    ens.Year = 2019
    ens.Month = 3
    ens.Day = 9
    ens.Hour = 12
    ens.Minute = 23
    ens.Second = 24
    ens.HSec = 33

    bin_Data = ens.encode()                 # Encode

    ens1 = EnsembleData()
    ens1.decode(bytearray(bin_Data))        # Decode

    assert ens.EnsembleNumber == ens1.EnsembleNumber
    assert ens.NumBins == ens1.NumBins
    assert ens.NumBeams == ens1.NumBeams
    assert ens.DesiredPingCount == ens1.DesiredPingCount
    assert ens.ActualPingCount == ens1.ActualPingCount
    assert ens.SerialNumber == ens1.SerialNumber
    assert ens.SysFirmwareMajor == ens1.SysFirmwareMajor
    assert ens.SysFirmwareMinor == ens1.SysFirmwareMinor
    assert ens.SysFirmwareRevision == ens1.SysFirmwareRevision
    assert ens.SysFirmwareSubsystemCode == ens1.SysFirmwareSubsystemCode
    assert ens.SubsystemConfig == ens1.SubsystemConfig
    assert ens.Status == ens1.Status
    assert ens.Year == ens1.Year
    assert ens.Month == ens1.Month
    assert ens.Day == ens1.Day
    assert ens.Hour == ens1.Hour
    assert ens.Minute == ens1.Minute
    assert ens.Second == ens1.Second
    assert ens.HSec == ens1.HSec

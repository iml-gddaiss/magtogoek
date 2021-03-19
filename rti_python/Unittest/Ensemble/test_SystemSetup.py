import pytest
import datetime
import re
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Ensemble.SystemSetup import SystemSetup


def test_generate_header():

    value_type = 10             # Float
    num_elements = 25           # 25 elements
    element_multiplier = 1      # no multiplier
    imag = 0                    # NOT USED
    name_length = 8             # Length of name
    name = "E000014\0"          # System Setup name

    header = Ensemble.generate_header(value_type,
                                      num_elements,
                                      element_multiplier,
                                      imag,
                                      name_length,
                                      name)

    # Value type
    assert 0xA == header[0]
    assert 0x0 == header[1]
    assert 0x0 == header[2]
    assert 0x0 == header[3]

    # Num Elements
    assert 0x19 == header[4]
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
    assert ord('1') == header[25]
    assert ord('4') == header[26]
    assert ord('\0') == header[27]


def test_ancillary():
    ss = SystemSetup()

    ss.BtSamplesPerSecond = 1.0
    ss.BtSystemFreqHz = 3.0
    ss.BtCPCE = 1.2
    ss.BtNCE = 2.3
    ss.BtRepeatN = 23.5
    ss.WpSamplesPerSecond = 13.6
    ss.WpSystemFreqHz = 11.25
    ss.WpCPCE = 25.3
    ss.WpNCE = 54.6
    ss.WpRepeatN = 35.0
    ss.WpLagSamples = 23.78
    ss.Voltage = 45.69
    ss.XmtVoltage = 1400.23
    ss.BtBroadband = 3.0
    ss.BtLagLength = 4.0
    ss.BtNarrowband = 5.0
    ss.BtBeamMux = 6.0
    ss.WpBroadband = 6.0
    ss.WpLagLength = 6.0
    ss.WpTransmitBandwidth = 6.0
    ss.WpReceiveBandwidth = 6.0
    ss.TransmitBoostNegVolt = 6.0
    ss.WpBeamMux = 6.0
    ss.Reserved = 6.0
    ss.Reserved1 = 6.0

    # Populate data

    result = ss.encode()

    # Value type
    assert 0xA == result[0]
    assert 0x0 == result[1]
    assert 0x0 == result[2]
    assert 0x0 == result[3]

    # Num Elements
    assert 0x19 == result[4]
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
    assert ord('1') == result[25]
    assert ord('4') == result[26]
    assert ord('\0') == result[27]

    # Length
    assert len(result) == 28 + (25 * Ensemble.BytesInFloat)

    # Data
    # Bottom Track Samples Per Second
    assert Ensemble.float_to_bytes(1.0)[0] == result[28]
    assert Ensemble.float_to_bytes(1.0)[1] == result[29]
    assert Ensemble.float_to_bytes(1.0)[2] == result[30]
    assert Ensemble.float_to_bytes(1.0)[3] == result[31]

    # Bottom Track System Frequency (Hz)
    assert Ensemble.float_to_bytes(3.0)[0] == result[32]
    assert Ensemble.float_to_bytes(3.0)[1] == result[33]
    assert Ensemble.float_to_bytes(3.0)[2] == result[34]
    assert Ensemble.float_to_bytes(3.0)[3] == result[35]

    # Bottom Track Cycles per Code Elements
    assert Ensemble.float_to_bytes(1.2)[0] == result[36]
    assert Ensemble.float_to_bytes(1.2)[1] == result[37]
    assert Ensemble.float_to_bytes(1.2)[2] == result[38]
    assert Ensemble.float_to_bytes(1.2)[3] == result[39]

    # Bottom Track Number of Code Elements
    assert Ensemble.float_to_bytes(2.3)[0] == result[40]
    assert Ensemble.float_to_bytes(2.3)[1] == result[41]
    assert Ensemble.float_to_bytes(2.3)[2] == result[42]
    assert Ensemble.float_to_bytes(2.3)[3] == result[43]

    # Bottom Track Number of Code Repeats
    assert Ensemble.float_to_bytes(23.5)[0] == result[44]
    assert Ensemble.float_to_bytes(23.5)[1] == result[45]
    assert Ensemble.float_to_bytes(23.5)[2] == result[46]
    assert Ensemble.float_to_bytes(23.5)[3] == result[47]

    # Water Profile Samples per Second
    assert Ensemble.float_to_bytes(13.6)[0] == result[48]
    assert Ensemble.float_to_bytes(13.6)[1] == result[49]
    assert Ensemble.float_to_bytes(13.6)[2] == result[50]
    assert Ensemble.float_to_bytes(13.6)[3] == result[51]

    # Water Profile System Frequency (Hz)
    assert Ensemble.float_to_bytes(11.25)[0] == result[52]
    assert Ensemble.float_to_bytes(11.25)[1] == result[53]
    assert Ensemble.float_to_bytes(11.25)[2] == result[54]
    assert Ensemble.float_to_bytes(11.25)[3] == result[55]

    # Water Profile Cycles per Code Element
    assert Ensemble.float_to_bytes(25.3)[0] == result[56]
    assert Ensemble.float_to_bytes(25.3)[1] == result[57]
    assert Ensemble.float_to_bytes(25.3)[2] == result[58]
    assert Ensemble.float_to_bytes(25.3)[3] == result[59]

    # Water Profile Number of Code Element
    assert Ensemble.float_to_bytes(54.6)[0] == result[60]
    assert Ensemble.float_to_bytes(54.6)[1] == result[61]
    assert Ensemble.float_to_bytes(54.6)[2] == result[62]
    assert Ensemble.float_to_bytes(54.6)[3] == result[63]

    # Water Profile Number of Code Repeats
    assert Ensemble.float_to_bytes(35.0)[0] == result[64]
    assert Ensemble.float_to_bytes(35.0)[1] == result[65]
    assert Ensemble.float_to_bytes(35.0)[2] == result[66]
    assert Ensemble.float_to_bytes(35.0)[3] == result[67]

    # Water Profile Lag Samples
    assert Ensemble.float_to_bytes(23.78)[0] == result[68]
    assert Ensemble.float_to_bytes(23.78)[1] == result[69]
    assert Ensemble.float_to_bytes(23.78)[2] == result[70]
    assert Ensemble.float_to_bytes(23.78)[3] == result[71]

    # Voltage input to ADCP
    assert Ensemble.float_to_bytes(45.69)[0] == result[72]
    assert Ensemble.float_to_bytes(45.69)[1] == result[73]
    assert Ensemble.float_to_bytes(45.69)[2] == result[74]
    assert Ensemble.float_to_bytes(45.69)[3] == result[75]

    # Transmit Voltage
    assert Ensemble.float_to_bytes(1400.23)[0] == result[76]
    assert Ensemble.float_to_bytes(1400.23)[1] == result[77]
    assert Ensemble.float_to_bytes(1400.23)[2] == result[78]
    assert Ensemble.float_to_bytes(1400.23)[3] == result[79]

    # Bottom Track Broadband
    assert Ensemble.float_to_bytes(3.0)[0] == result[80]
    assert Ensemble.float_to_bytes(3.0)[1] == result[81]
    assert Ensemble.float_to_bytes(3.0)[2] == result[82]
    assert Ensemble.float_to_bytes(3.0)[3] == result[83]

    # Bottom Track Lag Length
    assert Ensemble.float_to_bytes(4.0)[0] == result[84]
    assert Ensemble.float_to_bytes(4.0)[1] == result[85]
    assert Ensemble.float_to_bytes(4.0)[2] == result[86]
    assert Ensemble.float_to_bytes(4.0)[3] == result[87]

    # Bottom Track Narrowband
    assert Ensemble.float_to_bytes(5.0)[0] == result[88]
    assert Ensemble.float_to_bytes(5.0)[1] == result[89]
    assert Ensemble.float_to_bytes(5.0)[2] == result[90]
    assert Ensemble.float_to_bytes(5.0)[3] == result[91]

    # Bottom Track Beam MUX
    assert Ensemble.float_to_bytes(6.0)[0] == result[92]
    assert Ensemble.float_to_bytes(6.0)[1] == result[93]
    assert Ensemble.float_to_bytes(6.0)[2] == result[94]
    assert Ensemble.float_to_bytes(6.0)[3] == result[95]

    # Water Profile Broadband
    assert Ensemble.float_to_bytes(6.0)[0] == result[96]
    assert Ensemble.float_to_bytes(6.0)[1] == result[97]
    assert Ensemble.float_to_bytes(6.0)[2] == result[98]
    assert Ensemble.float_to_bytes(6.0)[3] == result[99]

    # Water Profile Lag Length
    assert Ensemble.float_to_bytes(6.0)[0] == result[100]
    assert Ensemble.float_to_bytes(6.0)[1] == result[101]
    assert Ensemble.float_to_bytes(6.0)[2] == result[102]
    assert Ensemble.float_to_bytes(6.0)[3] == result[103]

    # Water Profile Transmit Bandwidth
    assert Ensemble.float_to_bytes(6.0)[0] == result[104]
    assert Ensemble.float_to_bytes(6.0)[1] == result[105]
    assert Ensemble.float_to_bytes(6.0)[2] == result[106]
    assert Ensemble.float_to_bytes(6.0)[3] == result[107]

    # Water Profile Receive Bandwidth
    assert Ensemble.float_to_bytes(6.0)[0] == result[108]
    assert Ensemble.float_to_bytes(6.0)[1] == result[109]
    assert Ensemble.float_to_bytes(6.0)[2] == result[110]
    assert Ensemble.float_to_bytes(6.0)[3] == result[111]

    # Transmit Boost Negative Voltage
    assert Ensemble.float_to_bytes(6.0)[0] == result[112]
    assert Ensemble.float_to_bytes(6.0)[1] == result[113]
    assert Ensemble.float_to_bytes(6.0)[2] == result[114]
    assert Ensemble.float_to_bytes(6.0)[3] == result[115]

    # WP Beam Mux
    assert Ensemble.float_to_bytes(6.0)[0] == result[116]
    assert Ensemble.float_to_bytes(6.0)[1] == result[117]
    assert Ensemble.float_to_bytes(6.0)[2] == result[118]
    assert Ensemble.float_to_bytes(6.0)[3] == result[119]

    # Reserved
    assert Ensemble.float_to_bytes(6.0)[0] == result[120]
    assert Ensemble.float_to_bytes(6.0)[1] == result[121]
    assert Ensemble.float_to_bytes(6.0)[2] == result[122]
    assert Ensemble.float_to_bytes(6.0)[3] == result[123]

    # Reserved 1
    assert Ensemble.float_to_bytes(6.0)[0] == result[124]
    assert Ensemble.float_to_bytes(6.0)[1] == result[125]
    assert Ensemble.float_to_bytes(6.0)[2] == result[126]
    assert Ensemble.float_to_bytes(6.0)[3] == result[127]


def test_encode_csv():
    ss = SystemSetup()

    ss.BtSamplesPerSecond = 1.0
    ss.BtSystemFreqHz = 3.0
    ss.BtCPCE = 1.2
    ss.BtNCE = 2.3
    ss.BtRepeatN = 23.5
    ss.WpSamplesPerSecond = 13.6
    ss.WpSystemFreqHz = 11.25
    ss.WpCPCE = 25.3
    ss.WpNCE = 54.6
    ss.WpRepeatN = 35.0
    ss.WpLagSamples = 23.78
    ss.Voltage = 45.69
    ss.XmtVoltage = 1400.23
    ss.BtBroadband = 3.0
    ss.BtLagLength = 4.0
    ss.BtNarrowband = 5.0
    ss.BtBeamMux = 6.0
    ss.WpBroadband = 6.0
    ss.WpLagLength = 6.0
    ss.WpTransmitBandwidth = 6.0
    ss.WpReceiveBandwidth = 6.0
    ss.TransmitBoostNegVolt = 6.0
    ss.WpBeamMux = 6.0
    ss.Reserved = 6.0
    ss.Reserved1 = 6.0

    # Populate data

    dt = datetime.datetime.now()

    # Create CSV lines
    result = ss.encode_csv(dt, 'A', 1)

    for line in result:
        if Ensemble.CSV_VOLTAGE in line:
            assert bool(re.search(str(45.69), line))
            assert bool(re.search(str(0), line))


def test_encode_decode():
    ss = SystemSetup()

    ss.BtSamplesPerSecond = 1.0
    ss.BtSystemFreqHz = 3.0
    ss.BtCPCE = 1.2
    ss.BtNCE = 2.3
    ss.BtRepeatN = 23.5
    ss.WpSamplesPerSecond = 13.6
    ss.WpSystemFreqHz = 11.25
    ss.WpCPCE = 25.3
    ss.WpNCE = 54.6
    ss.WpRepeatN = 35.0
    ss.WpLagSamples = 23.78
    ss.Voltage = 45.69
    ss.XmtVoltage = 1400.23
    ss.BtBroadband = 3.0
    ss.BtLagLength = 4.0
    ss.BtNarrowband = 5.0
    ss.BtBeamMux = 6.0
    ss.WpBroadband = 6.0
    ss.WpLagLength = 6.0
    ss.WpTransmitBandwidth = 6.0
    ss.WpReceiveBandwidth = 6.0
    ss.TransmitBoostNegVolt = 6.0
    ss.WpBeamMux = 6.0
    ss.Reserved = 6.0
    ss.Reserved1 = 6.0

    # Populate data

    result = ss.encode()                   # Encode

    ss1 = SystemSetup()
    ss1.decode(bytearray(result))                     # Decode

    assert ss.BtSamplesPerSecond == pytest.approx(ss1.BtSamplesPerSecond, 0.1)
    assert ss.BtSystemFreqHz == pytest.approx(ss1.BtSystemFreqHz, 0.1)
    assert ss.BtCPCE == pytest.approx(ss1.BtCPCE, 0.1)
    assert ss.BtNCE == pytest.approx(ss1.BtNCE, 0.1)
    assert ss.BtRepeatN == pytest.approx(ss1.BtRepeatN, 0.1)
    assert ss.WpSamplesPerSecond == pytest.approx(ss1.WpSamplesPerSecond, 0.1)
    assert ss.WpSystemFreqHz == pytest.approx(ss1.WpSystemFreqHz, 0.1)
    assert ss.WpCPCE == pytest.approx(ss1.WpCPCE, 0.1)
    assert ss.WpNCE == pytest.approx(ss1.WpNCE, 0.1)
    assert ss.WpRepeatN == pytest.approx(ss1.WpRepeatN, 0.1)
    assert ss.WpLagSamples == pytest.approx(ss1.WpLagSamples, 0.1)
    assert ss.Voltage == pytest.approx(ss1.Voltage, 0.1)
    assert ss.XmtVoltage == pytest.approx(ss1.XmtVoltage, 0.1)
    assert ss.BtBroadband == pytest.approx(ss1.BtBroadband, 0.1)
    assert ss.BtLagLength == pytest.approx(ss1.BtLagLength, 0.1)
    assert ss.BtNarrowband == pytest.approx(ss1.BtNarrowband, 0.1)
    assert ss.BtBeamMux == pytest.approx(ss1.BtBeamMux, 0.1)
    assert ss.WpBroadband == pytest.approx(ss1.WpBroadband, 0.1)
    assert ss.WpLagLength == pytest.approx(ss1.WpLagLength, 0.1)
    assert ss.WpTransmitBandwidth == pytest.approx(ss1.WpTransmitBandwidth, 0.1)
    assert ss.WpReceiveBandwidth == pytest.approx(ss1.WpReceiveBandwidth, 0.1)
    assert ss.TransmitBoostNegVolt == pytest.approx(ss1.TransmitBoostNegVolt, 0.1)
    assert ss.WpBeamMux == pytest.approx(ss1.WpBeamMux, 0.1)
    assert ss.Reserved == pytest.approx(ss1.Reserved, 0.1)
    assert ss.Reserved1 == pytest.approx(ss1.Reserved1, 0.1)

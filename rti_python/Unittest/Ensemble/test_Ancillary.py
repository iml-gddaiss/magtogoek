import pytest
import datetime
import re
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Ensemble.AncillaryData import AncillaryData


def test_generate_header():

    value_type = 10             # Float
    num_elements = 19           # 19 elements
    element_multiplier = 1      # no multiplier
    imag = 0                    # NOT USED
    name_length = 8             # Length of name
    name = "E000009\0"          # Ancillary name

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
    assert ord('9') == header[26]
    assert ord('\0') == header[27]


def test_ancillary():
    anc = AncillaryData()
    anc.FirstBinRange = 1.0  # Blank.  Depth to the first bin in meters.
    anc.BinSize = 3.0  # Size of a bin in meters.
    anc.FirstPingTime = 1.2  # First Ping Time in seconds.
    anc.LastPingTime = 2.3  # Last Ping Time in seconds.  (If averaging pings, this will be the last ping)
    anc.Heading = 23.5  # Heading in degrees.
    anc.Pitch = 13.6  # Pitch in degrees.
    anc.Roll = 11.25  # Roll in degrees.
    anc.WaterTemp = 25.3  # Water Temperature in fahrenheit
    anc.SystemTemp = 54.6  # System Temperature in fahrenheit
    anc.Salinity = 35.0  # Water Salinity set by the user in PPT
    anc.Pressure = 23.78  # Pressure from pressure sensor in Pascals
    anc.TransducerDepth = 45.69  # Transducer Depth, used by Pressure sensor in meters
    anc.SpeedOfSound = 1400.23  # Speed of Sound in m/s.
    anc.RawMagFieldStrength = 3.0  # Raw magnetic field strength
    anc.RawMagFieldStrength2 = 4.0  # Raw magnetic field strength
    anc.RawMagFieldStrength3 = 5.0  # Raw magnetic field strength
    anc.PitchGravityVector = 4.0  # Pitch Gravity Vector
    anc.RollGravityVector = 5.0  # Roll Gravity Vector
    anc.VerticalGravityVector = 6.0  # Vertical Gravity Vector

    # Populate data

    result = anc.encode()

    # Value type
    assert 0xA == result[0]
    assert 0x0 == result[1]
    assert 0x0 == result[2]
    assert 0x0 == result[3]

    # Num Elements
    assert 0x13 == result[4]
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
    assert ord('9') == result[26]
    assert ord('\0') == result[27]

    # Length
    assert len(result) == 28 + ((anc.element_multiplier * anc.num_elements) * Ensemble.BytesInFloat)

    # Data
    # First Bin Range
    assert Ensemble.float_to_bytes(1.0)[0] == result[28]
    assert Ensemble.float_to_bytes(1.0)[1] == result[29]
    assert Ensemble.float_to_bytes(1.0)[2] == result[30]
    assert Ensemble.float_to_bytes(1.0)[3] == result[31]

    # Bin SIze
    assert Ensemble.float_to_bytes(3.0)[0] == result[32]
    assert Ensemble.float_to_bytes(3.0)[1] == result[33]
    assert Ensemble.float_to_bytes(3.0)[2] == result[34]
    assert Ensemble.float_to_bytes(3.0)[3] == result[35]

    # First Ping TIme
    assert Ensemble.float_to_bytes(1.2)[0] == result[36]
    assert Ensemble.float_to_bytes(1.2)[1] == result[37]
    assert Ensemble.float_to_bytes(1.2)[2] == result[38]
    assert Ensemble.float_to_bytes(1.2)[3] == result[39]

    # Last Ping TIme
    assert Ensemble.float_to_bytes(2.3)[0] == result[40]
    assert Ensemble.float_to_bytes(2.3)[1] == result[41]
    assert Ensemble.float_to_bytes(2.3)[2] == result[42]
    assert Ensemble.float_to_bytes(2.3)[3] == result[43]

    # Heading
    assert Ensemble.float_to_bytes(23.5)[0] == result[44]
    assert Ensemble.float_to_bytes(23.5)[1] == result[45]
    assert Ensemble.float_to_bytes(23.5)[2] == result[46]
    assert Ensemble.float_to_bytes(23.5)[3] == result[47]

    # Pitch
    assert Ensemble.float_to_bytes(13.6)[0] == result[48]
    assert Ensemble.float_to_bytes(13.6)[1] == result[49]
    assert Ensemble.float_to_bytes(13.6)[2] == result[50]
    assert Ensemble.float_to_bytes(13.6)[3] == result[51]

    # Roll
    assert Ensemble.float_to_bytes(11.25)[0] == result[52]
    assert Ensemble.float_to_bytes(11.25)[1] == result[53]
    assert Ensemble.float_to_bytes(11.25)[2] == result[54]
    assert Ensemble.float_to_bytes(11.25)[3] == result[55]

    # Water Temp
    assert Ensemble.float_to_bytes(25.3)[0] == result[56]
    assert Ensemble.float_to_bytes(25.3)[1] == result[57]
    assert Ensemble.float_to_bytes(25.3)[2] == result[58]
    assert Ensemble.float_to_bytes(25.3)[3] == result[59]

    # System Temp
    assert Ensemble.float_to_bytes(54.6)[0] == result[60]
    assert Ensemble.float_to_bytes(54.6)[1] == result[61]
    assert Ensemble.float_to_bytes(54.6)[2] == result[62]
    assert Ensemble.float_to_bytes(54.6)[3] == result[63]

    # Salinity
    assert Ensemble.float_to_bytes(35.0)[0] == result[64]
    assert Ensemble.float_to_bytes(35.0)[1] == result[65]
    assert Ensemble.float_to_bytes(35.0)[2] == result[66]
    assert Ensemble.float_to_bytes(35.0)[3] == result[67]

    # Pressure
    assert Ensemble.float_to_bytes(23.78)[0] == result[68]
    assert Ensemble.float_to_bytes(23.78)[1] == result[69]
    assert Ensemble.float_to_bytes(23.78)[2] == result[70]
    assert Ensemble.float_to_bytes(23.78)[3] == result[71]

    # Transducer Depth
    assert Ensemble.float_to_bytes(45.69)[0] == result[72]
    assert Ensemble.float_to_bytes(45.69)[1] == result[73]
    assert Ensemble.float_to_bytes(45.69)[2] == result[74]
    assert Ensemble.float_to_bytes(45.69)[3] == result[75]

    # Speed of Sound
    assert Ensemble.float_to_bytes(1400.23)[0] == result[76]
    assert Ensemble.float_to_bytes(1400.23)[1] == result[77]
    assert Ensemble.float_to_bytes(1400.23)[2] == result[78]
    assert Ensemble.float_to_bytes(1400.23)[3] == result[79]

    # Raw Mag
    assert Ensemble.float_to_bytes(3.0)[0] == result[80]
    assert Ensemble.float_to_bytes(3.0)[1] == result[81]
    assert Ensemble.float_to_bytes(3.0)[2] == result[82]
    assert Ensemble.float_to_bytes(3.0)[3] == result[83]

    # Raw Mag 2
    assert Ensemble.float_to_bytes(4.0)[0] == result[84]
    assert Ensemble.float_to_bytes(4.0)[1] == result[85]
    assert Ensemble.float_to_bytes(4.0)[2] == result[86]
    assert Ensemble.float_to_bytes(4.0)[3] == result[87]

    # Raw Mag 3
    assert Ensemble.float_to_bytes(5.0)[0] == result[88]
    assert Ensemble.float_to_bytes(5.0)[1] == result[89]
    assert Ensemble.float_to_bytes(5.0)[2] == result[90]
    assert Ensemble.float_to_bytes(5.0)[3] == result[91]

    # Raw Pitch
    assert Ensemble.float_to_bytes(4.0)[0] == result[92]
    assert Ensemble.float_to_bytes(4.0)[1] == result[93]
    assert Ensemble.float_to_bytes(4.0)[2] == result[94]
    assert Ensemble.float_to_bytes(4.0)[3] == result[95]

    # Raw Roll
    assert Ensemble.float_to_bytes(5.0)[0] == result[96]
    assert Ensemble.float_to_bytes(5.0)[1] == result[97]
    assert Ensemble.float_to_bytes(5.0)[2] == result[98]
    assert Ensemble.float_to_bytes(5.0)[3] == result[99]

    # Raw Vert
    assert Ensemble.float_to_bytes(6.0)[0] == result[100]
    assert Ensemble.float_to_bytes(6.0)[1] == result[101]
    assert Ensemble.float_to_bytes(6.0)[2] == result[102]
    assert Ensemble.float_to_bytes(6.0)[3] == result[103]


def test_encode_csv():

    anc = AncillaryData()
    anc.FirstBinRange = 1.0  # Blank.  Depth to the first bin in meters.
    anc.BinSize = 3.0  # Size of a bin in meters.
    anc.FirstPingTime = 1.2  # First Ping Time in seconds.
    anc.LastPingTime = 2.3  # Last Ping Time in seconds.  (If averaging pings, this will be the last ping)
    anc.Heading = 23.5  # Heading in degrees.
    anc.Pitch = 13.6  # Pitch in degrees.
    anc.Roll = 11.25  # Roll in degrees.
    anc.WaterTemp = 25.3  # Water Temperature in fahrenheit
    anc.SystemTemp = 54.6  # System Temperature in fahrenheit
    anc.Salinity = 35.0  # Water Salinity set by the user in PPT
    anc.Pressure = 23.78  # Pressure from pressure sensor in Pascals
    anc.TransducerDepth = 45.69  # Transducer Depth, used by Pressure sensor in meters
    anc.SpeedOfSound = 1400.23  # Speed of Sound in m/s.
    anc.RawMagFieldStrength = 3.0  # Raw magnetic field strength
    anc.RawMagFieldStrength2 = 4.0  # Raw magnetic field strength
    anc.RawMagFieldStrength3 = 5.0  # Raw magnetic field strength
    anc.PitchGravityVector = 4.0  # Pitch Gravity Vector
    anc.RollGravityVector = 5.0  # Roll Gravity Vector
    anc.VerticalGravityVector = 6.0  # Vertical Gravity Vector

    # Populate data

    dt = datetime.datetime.now()

    # Create CSV lines
    result = anc.encode_csv(dt, 'A', 1)

    # Check the csv data
    for line in result:
        if Ensemble.CSV_FIRST_PING_TIME in line:
            assert bool(re.search(str(1.2), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_LAST_PING_TIME in line:
            assert bool(re.search(str(2.3), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_HEADING in line:
            assert bool(re.search(str(23.5), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_PITCH in line:
            assert bool(re.search(str(13.6), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_ROLL in line:
            assert bool(re.search(str(11.25), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_WATER_TEMP in line:
            assert bool(re.search(str(25.3), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_SYS_TEMP in line:
            assert bool(re.search(str(54.6), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_PRESSURE in line:
            assert bool(re.search(str(23.78), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_XDCR_DEPTH in line:
            assert bool(re.search(str(45.69), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_SOS in line:
            assert bool(re.search(str(1400.23), line))
            assert bool(re.search(str(0), line))


def test_encode_decode():
    anc = AncillaryData()
    anc.FirstBinRange = 1.0  # Blank.  Depth to the first bin in meters.
    anc.BinSize = 3.0  # Size of a bin in meters.
    anc.FirstPingTime = 1.2  # First Ping Time in seconds.
    anc.LastPingTime = 2.3  # Last Ping Time in seconds.  (If averaging pings, this will be the last ping)
    anc.Heading = 23.5  # Heading in degrees.
    anc.Pitch = 13.6  # Pitch in degrees.
    anc.Roll = 11.25  # Roll in degrees.
    anc.WaterTemp = 25.3  # Water Temperature in fahrenheit
    anc.SystemTemp = 54.6  # System Temperature in fahrenheit
    anc.Salinity = 35.0  # Water Salinity set by the user in PPT
    anc.Pressure = 23.78  # Pressure from pressure sensor in Pascals
    anc.TransducerDepth = 45.69  # Transducer Depth, used by Pressure sensor in meters
    anc.SpeedOfSound = 1400.23  # Speed of Sound in m/s.
    anc.RawMagFieldStrength = 3.0  # Raw magnetic field strength
    anc.RawMagFieldStrength2 = 4.0  # Raw magnetic field strength
    anc.RawMagFieldStrength3 = 5.0  # Raw magnetic field strength
    anc.PitchGravityVector = 4.0  # Pitch Gravity Vector
    anc.RollGravityVector = 5.0  # Roll Gravity Vector
    anc.VerticalGravityVector = 6.0  # Vertical Gravity Vector

    # Populate data

    result = anc.encode()                   # Encode

    anc1 = AncillaryData()
    anc1.decode(bytearray(result))                     # Decode

    assert anc.FirstBinRange == pytest.approx(anc1.FirstBinRange, 0.1)
    assert anc.BinSize == pytest.approx(anc1.BinSize, 0.1)
    assert anc.FirstPingTime == pytest.approx(anc1.FirstPingTime, 0.1)
    assert anc.LastPingTime == pytest.approx(anc1.LastPingTime, 0.1)
    assert anc.Heading == pytest.approx(anc1.Heading, 0.1)
    assert anc.Pitch == pytest.approx(anc1.Pitch, 0.1)
    assert anc.Roll == pytest.approx(anc1.Roll, 0.1)
    assert anc.WaterTemp == pytest.approx(anc1.WaterTemp, 0.1)
    assert anc.SystemTemp == pytest.approx(anc1.SystemTemp, 0.1)
    assert anc.Salinity == pytest.approx(anc1.Salinity, 0.1)
    assert anc.Pressure == pytest.approx(anc1.Pressure, 0.1)
    assert anc.TransducerDepth == pytest.approx(anc1.TransducerDepth, 0.1)
    assert anc.SpeedOfSound == pytest.approx(anc1.SpeedOfSound, 0.1)
    assert anc.RawMagFieldStrength == pytest.approx(anc1.RawMagFieldStrength, 0.1)
    assert anc.RawMagFieldStrength2 == pytest.approx(anc1.RawMagFieldStrength2, 0.1)
    assert anc.RawMagFieldStrength3 == pytest.approx(anc1.RawMagFieldStrength3, 0.1)
    assert anc.PitchGravityVector == pytest.approx(anc1.PitchGravityVector, 0.1)
    assert anc.RollGravityVector == pytest.approx(anc1.RollGravityVector, 0.1)
    assert anc.VerticalGravityVector == pytest.approx(anc1.VerticalGravityVector, 0.1)

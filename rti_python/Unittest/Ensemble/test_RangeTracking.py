import pytest
import datetime
import re
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Ensemble.RangeTracking import RangeTracking


def test_generate_header():

    value_type = 10             # Float
    num_elements = 33           # 54 elements
    element_multiplier = 1      # no multiplier
    imag = 0                    # NOT USED
    name_length = 8             # Length of name
    name = "E000015\0"          # Ensemble Dataset name

    header = Ensemble.generate_header(value_type,
                                      num_elements,
                                      element_multiplier,
                                      imag,
                                      name_length,
                                      name)

    # Value type
    assert 0x0A == header[0]
    assert 0x0 == header[1]
    assert 0x0 == header[2]
    assert 0x0 == header[3]

    # Num Elements
    assert 0x21 == header[4]
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
    assert ord('5') == header[26]
    assert ord('\0') == header[27]


def test_range_tracking_data():
    rt = RangeTracking()
    rt.NumBeams = 4.0
    rt.Range = [1.1, 2.2, 3.3, 4.4]
    rt.Pings = [1, 2, 3, 4]
    rt.SNR = [1.1, 2.2, 3.3, 4.4]
    rt.Amplitude = [1.1, 2.2, 3.3, 4.4]
    rt.Correlation = [1.1, 2.2, 3.3, 4.4]
    rt.BeamVelocity = [1.1, 2.2, 3.3, 4.4]
    rt.InstrumentVelocity = [1.1, 2.2, 3.3, 4.4]
    rt.EarthVelocity = [1.1, 2.2, 3.3, 4.4]

    # Populate data

    result = rt.encode()

    # Value type
    assert 0x0A == result[0]
    assert 0x0 == result[1]
    assert 0x0 == result[2]
    assert 0x0 == result[3]

    # Num Elements
    assert 0x21 == result[4]
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
    assert ord('5') == result[26]
    assert ord('\0') == result[27]

    # Length
    assert len(result) == (33 * Ensemble.BytesInFloat) + 28

    # Data

    # Number of Beams
    assert Ensemble.float_to_bytes(4)[0] == result[28]
    assert Ensemble.float_to_bytes(4)[1] == result[29]
    assert Ensemble.float_to_bytes(4)[2] == result[30]
    assert Ensemble.float_to_bytes(4)[3] == result[31]

    index = 32

    # SNR Beam 0
    assert Ensemble.float_to_bytes(1.1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[3] == result[index]
    index += 1
    # SNR Beam 1
    assert Ensemble.float_to_bytes(2.2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[3] == result[index]
    index += 1
    # SNR Beam 2
    assert Ensemble.float_to_bytes(3.3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[3] == result[index]
    index += 1
    # SNR Beam 3
    assert Ensemble.float_to_bytes(4.4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[3] == result[index]
    index += 1

    # Range Beam 0
    assert Ensemble.float_to_bytes(1.1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[3] == result[index]
    index += 1
    # Range Beam 1
    assert Ensemble.float_to_bytes(2.2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[3] == result[index]
    index += 1
    # Range Beam 2
    assert Ensemble.float_to_bytes(3.3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[3] == result[index]
    index += 1
    # Range Beam 3
    assert Ensemble.float_to_bytes(4.4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[3] == result[index]
    index += 1

    # Pings Beam 0
    assert Ensemble.float_to_bytes(1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[3] == result[index]
    index += 1
    # Pings Beam 1
    assert Ensemble.float_to_bytes(2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[3] == result[index]
    index += 1
    # Pings Beam 2
    assert Ensemble.float_to_bytes(3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[3] == result[index]
    index += 1
    # Pings Beam 3
    assert Ensemble.float_to_bytes(4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[3] == result[index]
    index += 1

    # Amplitude Beam 0
    assert Ensemble.float_to_bytes(1.1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[3] == result[index]
    index += 1
    # Amplitude Beam 1
    assert Ensemble.float_to_bytes(2.2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[3] == result[index]
    index += 1
    # Amplitude Beam 2
    assert Ensemble.float_to_bytes(3.3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[3] == result[index]
    index += 1
    # Amplitude Beam 3
    assert Ensemble.float_to_bytes(4.4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[3] == result[index]
    index += 1

    # Correlation Beam 0
    assert Ensemble.float_to_bytes(1.1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[3] == result[index]
    index += 1
    # Correlation Beam 1
    assert Ensemble.float_to_bytes(2.2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[3] == result[index]
    index += 1
    # Correlation Beam 2
    assert Ensemble.float_to_bytes(3.3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[3] == result[index]
    index += 1
    # Correlation Beam 3
    assert Ensemble.float_to_bytes(4.4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[3] == result[index]
    index += 1

    # Beam Velocity Beam 0
    assert Ensemble.float_to_bytes(1.1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[3] == result[index]
    index += 1
    # Beam Velocity Beam 1
    assert Ensemble.float_to_bytes(2.2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[3] == result[index]
    index += 1
    # Beam Velocity Beam 2
    assert Ensemble.float_to_bytes(3.3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[3] == result[index]
    index += 1
    # Beam Velocity Beam 3
    assert Ensemble.float_to_bytes(4.4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[3] == result[index]
    index += 1

    # Instrument Velocity Beam 0
    assert Ensemble.float_to_bytes(1.1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[3] == result[index]
    index += 1
    # Instrument Velocity Beam 1
    assert Ensemble.float_to_bytes(2.2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[3] == result[index]
    index += 1
    # Instrument Velocity Beam 2
    assert Ensemble.float_to_bytes(3.3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[3] == result[index]
    index += 1
    # Instrument Velocity Beam 3
    assert Ensemble.float_to_bytes(4.4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[3] == result[index]
    index += 1

    # Earth Velocity Beam 0
    assert Ensemble.float_to_bytes(1.1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1.1)[3] == result[index]
    index += 1
    # Earth Velocity Beam 1
    assert Ensemble.float_to_bytes(2.2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2.2)[3] == result[index]
    index += 1
    # Earth Velocity Beam 2
    assert Ensemble.float_to_bytes(3.3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3.3)[3] == result[index]
    index += 1
    # Earth Velocity Beam 3
    assert Ensemble.float_to_bytes(4.4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4.4)[3] == result[index]
    index += 1


def test_encode_csv():

    rt = RangeTracking()
    rt.NumBeams = 4.0
    rt.Range = [1.1, 2.2, 3.3, 4.4]
    rt.Pings = [1, 2, 3, 4]
    rt.SNR = [1.1, 2.2, 3.3, 4.4]
    rt.Amplitude = [1.1, 2.2, 3.3, 4.4]
    rt.Correlation = [1.1, 2.2, 3.3, 4.4]
    rt.BeamVelocity = [1.1, 2.2, 3.3, 4.4]
    rt.BeamGood = [1, 2, 3, 4]
    rt.InstrumentVelocity = [1.1, 2.2, 3.3, 4.4]
    rt.InstrumentGood = [1, 2, 3, 4]
    rt.EarthVelocity = [1.1, 2.2, 3.3, 4.4]
    rt.EarthGood = [1, 2, 3, 4]
    rt.SNR_PulseCoherent = [1, 2, 3, 4]
    rt.Amp_PulseCoherent = [1, 2, 3, 4]
    rt.Vel_PulseCoherent = [1, 2, 3, 4]
    rt.Noise_PulseCoherent = [1, 2, 3, 4]


    # Populate data

    dt = datetime.datetime.now()

    # Create CSV lines
    result = rt.encode_csv(dt, 'A', 1, 1.3, 1.0)

    # Check the csv data
    for line in result:
        if Ensemble.CSV_RT_RANGE in line:
            if "0,0" in line:
                assert bool(re.search(str(1.1), line))
            #if "0,1" in line:
            #    assert bool(re.search(str(2.2), line))
            if "0,2" in line:
                assert bool(re.search(str(3.3), line))
            if "0,3" in line:
                assert bool(re.search(str(4.4), line))

        if Ensemble.CSV_RT_PINGS in line:
            if "0,0" in line:
                assert bool(re.search(str(1), line))
            #if "0,1" in line:
            #    assert bool(re.search(str(2.2), line))
            if "0,2" in line:
                assert bool(re.search(str(3), line))
            if "0,3" in line:
                assert bool(re.search(str(4), line))

        if Ensemble.CSV_BT_BEAM_VEL in line:
            if "0,0" in line:
                assert bool(re.search(str(1.1), line))
            #if "0,1" in line:
            #    assert bool(re.search(str(2.2), line))
            if "0,2" in line:
                assert bool(re.search(str(3.3), line))
            if "0,3" in line:
                assert bool(re.search(str(4.4), line))

        if Ensemble.CSV_BT_INSTR_VEL in line:
            if "0,0" in line:
                assert bool(re.search(str(1.1), line))
            #if "0,1" in line:
            #    assert bool(re.search(str(2.2), line))
            if "0,2" in line:
                assert bool(re.search(str(3.3), line))
            if "0,3" in line:
                assert bool(re.search(str(4.4), line))

        if Ensemble.CSV_BT_EARTH_VEL in line:
            if "0,0" in line:
                assert bool(re.search(str(1.1), line))
            #if "0,1" in line:
            #    assert bool(re.search(str(2.2), line))
            if "0,2" in line:
                assert bool(re.search(str(3.3), line))
            if "0,3" in line:
                assert bool(re.search(str(4.4), line))


def test_encode_decode():
    rt = RangeTracking()
    rt.NumBeams = 4.0
    rt.Range = [1.1, 2.2, 3.3, 4.4]
    rt.Pings = [1, 2, 3, 4]
    rt.SNR = [1.1, 2.2, 3.3, 4.4]
    rt.Amplitude = [1.1, 2.2, 3.3, 4.4]
    rt.Correlation = [1.1, 2.2, 3.3, 4.4]
    rt.BeamVelocity = [1.1, 2.2, 3.3, 4.4]
    rt.InstrumentVelocity = [1.1, 2.2, 3.3, 4.4]
    rt.EarthVelocity = [1.1, 2.2, 3.3, 4.4]

    # Populate data

    result = rt.encode()

    rt1 = RangeTracking()
    rt1.decode(bytearray(result))

    assert rt.NumBeams == rt1.NumBeams
    assert rt.Range == pytest.approx(rt1.Range)
    assert rt.SNR == pytest.approx(rt1.SNR)
    assert rt.Amplitude == pytest.approx(rt1.Amplitude)
    assert rt.Correlation == pytest.approx(rt1.Correlation)
    assert rt.BeamVelocity == pytest.approx(rt1.BeamVelocity)
    assert rt.InstrumentVelocity == pytest.approx(rt1.InstrumentVelocity)
    assert rt.EarthVelocity == pytest.approx(rt1.EarthVelocity)

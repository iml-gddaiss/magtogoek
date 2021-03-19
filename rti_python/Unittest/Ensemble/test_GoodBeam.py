import pytest
import datetime
import re
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Ensemble.GoodBeam import GoodBeam


def test_generate_header():

    value_type = 20             # Int
    num_elements = 30           # 30 bins
    element_multiplier = 4      # 4 Beams
    imag = 0                    # NOT USED
    name_length = 8             # Length of name
    name = "E000006\0"          # Good Beam name

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
    assert 0x1E == header[4]
    assert 0x0 == header[5]
    assert 0x0 == header[6]
    assert 0x0 == header[7]

    # Element Multiplier
    assert 0x4 == header[8]
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
    assert ord('6') == header[26]
    assert ord('\0') == header[27]


def test_velocities():
    gb = GoodBeam(30, 4)

    # Populate data
    val = 1
    for beam in range(gb.element_multiplier):
        for bin_num in range(gb.num_elements):
            gb.GoodBeam[bin_num][beam] = val
            val += 1

    result = gb.encode()

    # Value type
    assert 0x14 == result[0]
    assert 0x0 == result[1]
    assert 0x0 == result[2]
    assert 0x0 == result[3]

    # Num Elements
    assert 0x1E == result[4]
    assert 0x0 == result[5]
    assert 0x0 == result[6]
    assert 0x0 == result[7]

    # Element Multiplier
    assert 0x4 == result[8]
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
    assert ord('6') == result[26]
    assert ord('\0') == result[27]

    # Length
    assert len(result) == 28 + ((gb.element_multiplier * gb.num_elements) * Ensemble.BytesInInt32)

    # Data
    result_val = 1
    index = 28                  # 28 = Header size
    for beam in range(gb.element_multiplier):
        for bin_num in range(gb.num_elements):
            test_val = Ensemble.GetInt32(index, Ensemble().BytesInFloat, bytearray(result))
            assert result_val == pytest.approx(test_val, 0.1)
            result_val += 1
            index += Ensemble().BytesInFloat


def test_encode_csv():
    num_bins = 30
    num_beams = 4

    gb = GoodBeam(num_bins, num_beams)

    # Populate data
    val = 1
    for beam in range(gb.element_multiplier):
        for bin_num in range(gb.num_elements):
            gb.GoodBeam[bin_num][beam] = val
            val += 1

    dt = datetime.datetime.now()

    # Create CSV lines
    result = gb.encode_csv(dt, 'A', 1, 1.3, 1.0)

    # Check the csv data
    test_value = 1
    for line in result:
        assert bool(re.search(str(test_value), line))
        assert bool(re.search(Ensemble.CSV_GOOD_BEAM, line))
        test_value += 1


def test_encode_decode():

    num_bins = 30
    num_beams = 4

    gb = GoodBeam(num_bins, num_beams)

    # Populate data
    val = 1
    for beam in range(gb.element_multiplier):
        for bin_num in range(gb.num_elements):
            gb.GoodBeam[bin_num][beam] = val
            val += 1

    result = gb.encode()

    gb1 = GoodBeam(num_bins, num_beams)
    gb1.decode(bytearray(result))

    for beam in range(gb1.element_multiplier):
        for bin_num in range(gb1.num_elements):
            assert gb1.GoodBeam[bin_num][beam] == pytest.approx(gb1.GoodBeam[bin_num][beam], 0.1)


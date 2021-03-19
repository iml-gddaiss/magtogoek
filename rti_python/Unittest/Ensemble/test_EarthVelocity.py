import pytest
import datetime
import re
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Ensemble.EarthVelocity import EarthVelocity
import numpy as np


def test_generate_header():

    value_type = 10             # Float
    num_elements = 30           # 30 bins
    element_multiplier = 4      # 4 Beams
    imag = 0                    # NOT USED
    name_length = 8             # Length of name
    name = "E000003\0"          # Earth Vel name

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
    assert ord('3') == header[26]
    assert ord('\0') == header[27]


def test_velocities():
    vels = EarthVelocity(30, 4)

    # Populate data
    val = 1.0
    for beam in range(vels.element_multiplier):
        for bin_num in range(vels.num_elements):
            vels.Velocities[bin_num][beam] = val
            val += 1.1

    result = vels.encode()

    # Value type
    assert 0xA == result[0]
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
    assert ord('3') == result[26]
    assert ord('\0') == result[27]

    # Length
    assert len(result) == 28 + ((vels.element_multiplier * vels.num_elements) * Ensemble.BytesInFloat)

    # Beam Velocities data
    result_val = 1.0
    index = 28                  # 28 = Header size
    for beam in range(vels.element_multiplier):
        for bin_num in range(vels.num_elements):
            test_val = Ensemble.GetFloat(index, Ensemble().BytesInFloat, bytearray(result))
            assert result_val == pytest.approx(test_val, 0.1)
            result_val += 1.1
            index += Ensemble().BytesInFloat


def test_encode_csv():
    num_bins = 30
    num_beams = 4

    vel = EarthVelocity(num_bins, num_beams)

    # Populate data
    val = 1.0
    for beam in range(vel.element_multiplier):
        for bin_num in range(vel.num_elements):
            vel.Velocities[bin_num][beam] = val
            val += 1.1
    vel.Magnitude, vel.Direction = EarthVelocity.generate_vectors(vel.Velocities)

    dt = datetime.datetime.now()

    # Create CSV lines
    result = vel.encode_csv(dt, 'A', 1, 1.3, 1.0)

    # Check the csv data
    test_value = 1.0
    for line in result:
        if bool(re.search(Ensemble.CSV_EARTH_VEL, line[0])):
            assert bool(re.search(str(test_value), line[0]))
            assert bool(re.search(Ensemble.CSV_EARTH_VEL, line[0]))
            test_value += 1.1


def test_encode_decode():

    num_bins = 30
    num_beams = 4

    vel = EarthVelocity(num_bins, num_beams)

    # Populate data
    val = 1.0
    for beam in range(vel.element_multiplier):
        for bin_num in range(vel.num_elements):
            vel.Velocities[bin_num][beam] = val
            val += 1.1
    vel.Magnitude, vel.Direction = EarthVelocity.generate_vectors(vel.Velocities)

    result = vel.encode()

    vel1 = EarthVelocity(num_bins, num_beams)
    vel1.decode(bytearray(result))

    for beam in range(vel1.element_multiplier):
        for bin_num in range(vel1.num_elements):
            assert vel.Velocities[bin_num][beam] == pytest.approx(vel1.Velocities[bin_num][beam], 0.1)
            assert vel.Magnitude[bin_num] == pytest.approx(vel1.Magnitude[bin_num], 0.1)
            assert vel.Direction[bin_num] == pytest.approx(vel1.Direction[bin_num], 0.1)



def test_magnitude():
    east = 1.33
    north = 1.45
    vert = 0.3
    result = Ensemble.calculate_magnitude(east, north, vert)
    assert 1.99 == pytest.approx(result, 0.01)


def test_direction():
    east = 1.33
    north = 1.45
    result = Ensemble.calculate_direction(east, north)
    assert 42.52 == pytest.approx(result, 0.01)


def test_vectors():

    earth = EarthVelocity(3, 4)

    earth.Velocities.clear()
    earth.Velocities.append([1.33, 1.45, 0.3, 0.0])
    earth.Velocities.append([1.33, 1.45, 0.3, 0.0])
    earth.Velocities.append([1.33, 1.45, 0.3, 0.0])

    earth.remove_vessel_speed(-1.1, -1.2, -0.1)

    mag, dir = EarthVelocity.generate_vectors(earth.Velocities)

    assert 3 == len(mag)
    assert 3 == len(dir)
    assert 0.394 == pytest.approx(mag[0], 0.01)
    assert 42.614 == pytest.approx(dir[0], 0.01)
    assert 0.394 == pytest.approx(mag[1], 0.01)
    assert 42.614 == pytest.approx(dir[1], 0.01)
    assert 0.394 == pytest.approx(mag[2], 0.01)
    assert 42.614 == pytest.approx(dir[2], 0.01)


def test_encode_csv_vector():
    num_bins = 30
    num_beams = 4

    vel = EarthVelocity(num_bins, num_beams)

    # Populate data
    val = 1.0
    for beam in range(vel.element_multiplier):
        for bin_num in range(vel.num_elements):
            vel.Velocities[bin_num][beam] = val

    vel.Magnitude, vel.Direction = EarthVelocity.generate_vectors(vel.Velocities)

    dt = datetime.datetime.now()

    # Create CSV lines
    result = vel.encode_csv(dt, 'A', 1, 1.3, 1.0)

    # Check the csv data
    test_value = 1.0
    for line in result:
        if bool(re.search(Ensemble.CSV_MAG, line[0])):
            assert bool(re.search(str(1.73), line[0]))
            assert bool(re.search(Ensemble.CSV_MAG, line[0]))
        elif bool(re.search(Ensemble.CSV_DIR, line[0])):
            assert bool(re.search(str(45.0), line[0]))
            assert bool(re.search(Ensemble.CSV_DIR, line[0]))
        elif bool(re.search(Ensemble.CSV_EARTH_VEL, line[0])):
            assert True
        else:
            assert False


def test_encode_csv_vector_bt():
    num_bins = 30
    num_beams = 4

    vel = EarthVelocity(num_bins, num_beams)

    # Populate data
    val = 2.0
    for beam in range(vel.element_multiplier):
        for bin_num in range(vel.num_elements):
            vel.Velocities[bin_num][beam] = val

    vel.remove_vessel_speed(-1.3, -1.4, 0.3)
    vel.Magnitude, vel.Direction = EarthVelocity.generate_vectors(vel.Velocities)

    dt = datetime.datetime.now()

    # Create CSV lines
    result = vel.encode_csv(dt, 'A', 1, 1.3, 1.0)

    # Check the csv data
    for line in result:
        if bool(re.search(Ensemble.CSV_MAG, line[0])):
            assert bool(re.search(str(2.477), line[0]))
            assert bool(re.search(Ensemble.CSV_MAG, line[0]))
        elif bool(re.search(Ensemble.CSV_DIR, line[0])):
            assert bool(re.search(str(49.3987), line[0]))
            assert bool(re.search(Ensemble.CSV_DIR, line[0]))
        elif bool(re.search(Ensemble.CSV_EARTH_VEL, line[0])):
            assert True
        else:
            assert False


def test_encode_csv_vector_no_remove():
    num_bins = 30
    num_beams = 4

    vel = EarthVelocity(num_bins, num_beams)

    # Populate data
    val = 2.0
    for beam in range(vel.element_multiplier):
        for bin_num in range(vel.num_elements):
            vel.Velocities[bin_num][beam] = val

    vel.Magnitude, vel.Direction = EarthVelocity.generate_vectors(vel.Velocities)

    dt = datetime.datetime.now()

    # Create CSV lines
    result = vel.encode_csv(dt, 'A', 1, 1.3, 1.0)

    # Check the csv data
    for line in result:
        if bool(re.search(Ensemble.CSV_MAG, line[0])):
            assert bool(re.search(str(3.464), line[0]))
            assert bool(re.search(Ensemble.CSV_MAG, line[0]))
        elif bool(re.search(Ensemble.CSV_DIR, line[0])):
            assert bool(re.search(str(45.0), line[0]))
            assert bool(re.search(Ensemble.CSV_DIR, line[0]))
        elif bool(re.search(Ensemble.CSV_EARTH_VEL, line[0])):
            assert True
        else:
            assert False

def test_encode_csv_vector_no_gen():
    num_bins = 30
    num_beams = 4

    vel = EarthVelocity(num_bins, num_beams)

    # Populate data
    val = 2.0
    for beam in range(vel.element_multiplier):
        for bin_num in range(vel.num_elements):
            vel.Velocities[bin_num][beam] = val
    vel.Magnitude, vel.Direction = EarthVelocity.generate_vectors(vel.Velocities)

    vel.remove_vessel_speed(-1.3, -1.4, 0.3)

    dt = datetime.datetime.now()

    # Create CSV lines
    result = vel.encode_csv(dt, 'A', 1, 1.3, 1.0)

    # Check the csv data
    for line in result:
        if bool(re.search(Ensemble.CSV_MAG, line[0])):
            assert bool(re.search(str(2.477), line[0]))
            assert bool(re.search(Ensemble.CSV_MAG, line[0]))
        elif bool(re.search(Ensemble.CSV_DIR, line[0])):
            assert bool(re.search(str(49.3987), line[0]))
            assert bool(re.search(Ensemble.CSV_DIR, line[0]))
        elif bool(re.search(Ensemble.CSV_EARTH_VEL, line[0])):
            assert True
        else:
            assert False

def test_avg_mag_dir():
    num_bins = 30
    num_beams = 4

    vel = EarthVelocity(num_bins, num_beams)

    vel.Magnitude = [5.0, 5.0, 5.0, 5.0]
    vel.Direction = [1.2, 1.2, 1.2, 1.2]

    avg_mag, avg_dir = vel.average_mag_dir()

    assert avg_mag == pytest.approx(5, 0.001)
    assert avg_dir == pytest.approx(1.2, 0.001)


def test_avg_mag_dir_nan():
    num_bins = 30
    num_beams = 4

    vel = EarthVelocity(num_bins, num_beams)

    vel.Magnitude = [5.0, 5.0, 5.0, 5.0, np.NaN]
    vel.Direction = [1.2, 1.2, 1.2, 1.2, np.NaN]

    avg_mag, avg_dir = vel.average_mag_dir()

    assert avg_mag == pytest.approx(5, 0.001)
    assert avg_dir == pytest.approx(1.2, 0.001)

def test_avg_mag_dir_nan():
    num_bins = 30
    num_beams = 4

    vel = EarthVelocity(num_bins, num_beams)

    vel.Magnitude = [np.NaN, np.NaN]
    vel.Direction = [np.NaN, np.NaN]

    avg_mag, avg_dir = vel.average_mag_dir()

    assert avg_mag is None
    assert avg_dir is None

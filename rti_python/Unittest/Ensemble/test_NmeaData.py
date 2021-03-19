import pytest
import datetime
import re
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Ensemble.NmeaData import NmeaData


def test_generate_header():

    value_type = 50             # Byte
    num_elements = 11           # 17 elements
    element_multiplier = 1      # no multiplier
    imag = 0                    # NOT USED
    name_length = 8             # Length of name
    name = "E000011\0"          # Ancillary name

    header = Ensemble.generate_header(value_type,
                                      num_elements,
                                      element_multiplier,
                                      imag,
                                      name_length,
                                      name)

    # Value type
    assert 0x32 == header[0]
    assert 0x0 == header[1]
    assert 0x0 == header[2]
    assert 0x0 == header[3]

    # Num Elements
    assert 0x0B == header[4]
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
    assert ord('1') == header[26]
    assert ord('\0') == header[27]


def test_nmea():

    nmea = NmeaData()
    nmea.nmea_sentences.append("$HEHDT,244.39,T*17")
    nmea.nmea_sentences.append("$GPGGA,195949.00,3254.8103248,N,11655.5779629,W,2,08,1.1,222.174,M,-32.602,M,6.0,0138*75")
    nmea.nmea_sentences.append("$GPVTG,306.20,T,294.73,M,0.13,N,0.24,K,D*2E")
    nmea.nmea_sentences.append("$HEHDT, 244.36, T * 18")

    # Populate data

    result = nmea.encode()

    # Value type
    assert 0x32 == result[0]
    assert 0x0 == result[1]
    assert 0x0 == result[2]
    assert 0x0 == result[3]

    # Num Elements
    assert 0xAF == result[4]
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
    assert ord('1') == result[26]
    assert ord('\0') == result[27]

    # Length
    assert len(result) == 28 + nmea.num_elements


def test_encode_csv():

    # Populate data
    nmea = NmeaData()
    nmea.add_nmea("$HEHDT,244.39,T*17\n")
    nmea.add_nmea("$GPGGA,195949.00,3254.8103248,N,11655.5779629,W,2,08,1.1,222.174,M,-32.602,M,6.0,0138*75\n")
    nmea.add_nmea("$GPVTG,306.20,T,294.73,M,0.13,N,0.24,K,D*2E\n")
    nmea.add_nmea("$HEHDT,244.36,T*18\n")

    dt = datetime.datetime.now()

    # Create CSV lines
    result = nmea.encode_csv(dt, 'A', 1)

    # Check the csv data
    for line in result:
        if Ensemble.CSV_NMEA in line:
            assert bool(re.search('$', line))
            assert bool(re.search(",", line))


def test_add_nmea():
    # Populate data
    nmea = NmeaData()
    nmea.add_nmea("$HEHDT,244.39,T*17\n")
    nmea.add_nmea("$GPGGA,195949.00,3254.8103248,N,11655.5779629,W,2,08,1.1,222.174,M,-32.602,M,6.0,0138*75\n")
    nmea.add_nmea("$GPVTG,306.20,T,294.73,M,0.13,N,0.24,K,D*2E\n")
    nmea.add_nmea("$HEHDT,244.36,T*18\n")

    result = nmea.encode()                   # Encode

    nmea1 = NmeaData()
    nmea1.decode(bytearray(result))                     # Decode

    assert nmea.nmea_sentences == nmea1.nmea_sentences
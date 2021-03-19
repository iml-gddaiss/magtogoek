import pytest
import datetime
import re
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Ensemble.BottomTrack import BottomTrack


def test_generate_header():

    value_type = 10             # Float
    num_elements = 74           # 74 elements
    element_multiplier = 1      # no multiplier
    imag = 0                    # NOT USED
    name_length = 8             # Length of name
    name = "E000010\0"          # Ensemble Dataset name

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
    assert 0x4A == header[4]
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
    assert ord('0') == header[26]
    assert ord('\0') == header[27]


def test_BottomTrackdata():
    bt = BottomTrack()
    bt.FirstPingTime = 12.5
    bt.LastPingTime = 12.8
    bt.Heading = 152.36
    bt.Pitch = 12.6
    bt.Roll = 223.1
    bt.WaterTemp = 15.23
    bt.SystemTemp = 78.58
    bt.Salinity = 35.0
    bt.Pressure = 23.36
    bt.TransducerDepth = 156.2
    bt.SpeedOfSound = 1402.36
    bt.Status = 9.0
    bt.NumBeams = 4.0
    bt.ActualPingCount = 23
    bt.Range = [1.1, 2.2, 3.3, 4.4]
    bt.SNR = [1.1, 2.2, 3.3, 4.4]
    bt.Amplitude = [1.1, 2.2, 3.3, 4.4]
    bt.Correlation = [1.1, 2.2, 3.3, 4.4]
    bt.BeamVelocity = [1.1, 2.2, 3.3, 4.4]
    bt.BeamGood = [1, 2, 3, 4]
    bt.InstrumentVelocity = [1.1, 2.2, 3.3, 4.4]
    bt.InstrumentGood = [1, 2, 3, 4]
    bt.EarthVelocity = [1.1, 2.2, 3.3, 4.4]
    bt.EarthGood = [1, 2, 3, 4]
    bt.SNR_PulseCoherent = [1, 2, 3, 4]
    bt.Amp_PulseCoherent = [1, 2, 3, 4]
    bt.Vel_PulseCoherent = [1, 2, 3, 4]
    bt.Noise_PulseCoherent = [1, 2, 3, 4]
    bt.Corr_PulseCoherent = [1, 2, 3, 4]

    # Populate data

    result = bt.encode()

    # Value type
    assert 0x0A == result[0]
    assert 0x0 == result[1]
    assert 0x0 == result[2]
    assert 0x0 == result[3]

    # Num Elements
    assert 0x4A == result[4]
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
    assert ord('0') == result[26]
    assert ord('\0') == result[27]

    # Length
    assert len(result) == (74 * Ensemble.BytesInFloat) + 28

    # Data
    # First Ping Time
    assert Ensemble.float_to_bytes(12.5)[0] == result[28]
    assert Ensemble.float_to_bytes(12.5)[1] == result[29]
    assert Ensemble.float_to_bytes(12.5)[2] == result[30]
    assert Ensemble.float_to_bytes(12.5)[3] == result[31]

    # Last Ping Time
    assert Ensemble.float_to_bytes(12.8)[0] == result[32]
    assert Ensemble.float_to_bytes(12.8)[1] == result[33]
    assert Ensemble.float_to_bytes(12.8)[2] == result[34]
    assert Ensemble.float_to_bytes(12.8)[3] == result[35]

    # Heading
    assert Ensemble.float_to_bytes(152.36)[0] == result[36]
    assert Ensemble.float_to_bytes(152.36)[1] == result[37]
    assert Ensemble.float_to_bytes(152.36)[2] == result[38]
    assert Ensemble.float_to_bytes(152.36)[3] == result[39]

    # Pitch
    assert Ensemble.float_to_bytes(12.6)[0] == result[40]
    assert Ensemble.float_to_bytes(12.6)[1] == result[41]
    assert Ensemble.float_to_bytes(12.6)[2] == result[42]
    assert Ensemble.float_to_bytes(12.6)[3] == result[43]

    # Roll
    assert Ensemble.float_to_bytes(223.1)[0] == result[44]
    assert Ensemble.float_to_bytes(223.1)[1] == result[45]
    assert Ensemble.float_to_bytes(223.1)[2] == result[46]
    assert Ensemble.float_to_bytes(223.1)[3] == result[47]

    # Water Temp
    assert Ensemble.float_to_bytes(15.23)[0] == result[48]
    assert Ensemble.float_to_bytes(15.23)[1] == result[49]
    assert Ensemble.float_to_bytes(15.23)[2] == result[50]
    assert Ensemble.float_to_bytes(15.23)[3] == result[51]

    # System Temp
    assert Ensemble.float_to_bytes(78.58)[0] == result[52]
    assert Ensemble.float_to_bytes(78.58)[1] == result[53]
    assert Ensemble.float_to_bytes(78.58)[2] == result[54]
    assert Ensemble.float_to_bytes(78.58)[3] == result[55]

    # Salinity
    assert Ensemble.float_to_bytes(35)[0] == result[56]
    assert Ensemble.float_to_bytes(35)[1] == result[57]
    assert Ensemble.float_to_bytes(35)[2] == result[58]
    assert Ensemble.float_to_bytes(35)[3] == result[59]

    # Pressure
    assert Ensemble.float_to_bytes(23.36)[0] == result[60]
    assert Ensemble.float_to_bytes(23.36)[1] == result[61]
    assert Ensemble.float_to_bytes(23.36)[2] == result[62]
    assert Ensemble.float_to_bytes(23.36)[3] == result[63]

    # XDCR Depth
    assert Ensemble.float_to_bytes(156.2)[0] == result[64]
    assert Ensemble.float_to_bytes(156.2)[1] == result[65]
    assert Ensemble.float_to_bytes(156.2)[2] == result[66]
    assert Ensemble.float_to_bytes(156.2)[3] == result[67]

    # Speed of Sound
    assert Ensemble.float_to_bytes(1402.36)[0] == result[68]
    assert Ensemble.float_to_bytes(1402.36)[1] == result[69]
    assert Ensemble.float_to_bytes(1402.36)[2] == result[70]
    assert Ensemble.float_to_bytes(1402.36)[3] == result[71]

    # Status
    assert Ensemble.float_to_bytes(9.0)[0] == result[72]
    assert Ensemble.float_to_bytes(9.0)[1] == result[73]
    assert Ensemble.float_to_bytes(9.0)[2] == result[74]
    assert Ensemble.float_to_bytes(9.0)[3] == result[75]

    # Number of Beams
    assert Ensemble.float_to_bytes(4)[0] == result[76]
    assert Ensemble.float_to_bytes(4)[1] == result[77]
    assert Ensemble.float_to_bytes(4)[2] == result[78]
    assert Ensemble.float_to_bytes(4)[3] == result[79]

    # Ping Count
    assert Ensemble.float_to_bytes(23)[0] == result[80]
    assert Ensemble.float_to_bytes(23)[1] == result[81]
    assert Ensemble.float_to_bytes(23)[2] == result[82]
    assert Ensemble.float_to_bytes(23)[3] == result[83]

    # Range Beam 0
    assert Ensemble.float_to_bytes(1.1)[0] == result[84]
    assert Ensemble.float_to_bytes(1.1)[1] == result[85]
    assert Ensemble.float_to_bytes(1.1)[2] == result[86]
    assert Ensemble.float_to_bytes(1.1)[3] == result[87]
    # Range Beam 1
    assert Ensemble.float_to_bytes(2.2)[0] == result[88]
    assert Ensemble.float_to_bytes(2.2)[1] == result[89]
    assert Ensemble.float_to_bytes(2.2)[2] == result[90]
    assert Ensemble.float_to_bytes(2.2)[3] == result[91]
    # Range Beam 2
    assert Ensemble.float_to_bytes(3.3)[0] == result[92]
    assert Ensemble.float_to_bytes(3.3)[1] == result[93]
    assert Ensemble.float_to_bytes(3.3)[2] == result[94]
    assert Ensemble.float_to_bytes(3.3)[3] == result[95]
    # Range Beam 3
    assert Ensemble.float_to_bytes(4.4)[0] == result[96]
    assert Ensemble.float_to_bytes(4.4)[1] == result[97]
    assert Ensemble.float_to_bytes(4.4)[2] == result[98]
    assert Ensemble.float_to_bytes(4.4)[3] == result[99]

    # SNR Beam 0
    assert Ensemble.float_to_bytes(1.1)[0] == result[100]
    assert Ensemble.float_to_bytes(1.1)[1] == result[101]
    assert Ensemble.float_to_bytes(1.1)[2] == result[102]
    assert Ensemble.float_to_bytes(1.1)[3] == result[103]
    # SNR Beam 1
    assert Ensemble.float_to_bytes(2.2)[0] == result[104]
    assert Ensemble.float_to_bytes(2.2)[1] == result[105]
    assert Ensemble.float_to_bytes(2.2)[2] == result[106]
    assert Ensemble.float_to_bytes(2.2)[3] == result[107]
    # SNR Beam 2
    assert Ensemble.float_to_bytes(3.3)[0] == result[108]
    assert Ensemble.float_to_bytes(3.3)[1] == result[109]
    assert Ensemble.float_to_bytes(3.3)[2] == result[110]
    assert Ensemble.float_to_bytes(3.3)[3] == result[111]
    # SNR Beam 3
    assert Ensemble.float_to_bytes(4.4)[0] == result[112]
    assert Ensemble.float_to_bytes(4.4)[1] == result[113]
    assert Ensemble.float_to_bytes(4.4)[2] == result[114]
    assert Ensemble.float_to_bytes(4.4)[3] == result[115]

    # Amp Beam 0
    assert Ensemble.float_to_bytes(1.1)[0] == result[116]
    assert Ensemble.float_to_bytes(1.1)[1] == result[117]
    assert Ensemble.float_to_bytes(1.1)[2] == result[118]
    assert Ensemble.float_to_bytes(1.1)[3] == result[119]
    # Amp Beam 1
    assert Ensemble.float_to_bytes(2.2)[0] == result[120]
    assert Ensemble.float_to_bytes(2.2)[1] == result[121]
    assert Ensemble.float_to_bytes(2.2)[2] == result[122]
    assert Ensemble.float_to_bytes(2.2)[3] == result[123]
    # Amp Beam 2
    assert Ensemble.float_to_bytes(3.3)[0] == result[124]
    assert Ensemble.float_to_bytes(3.3)[1] == result[125]
    assert Ensemble.float_to_bytes(3.3)[2] == result[126]
    assert Ensemble.float_to_bytes(3.3)[3] == result[127]
    # Amp Beam 3
    assert Ensemble.float_to_bytes(4.4)[0] == result[128]
    assert Ensemble.float_to_bytes(4.4)[1] == result[129]
    assert Ensemble.float_to_bytes(4.4)[2] == result[130]
    assert Ensemble.float_to_bytes(4.4)[3] == result[131]

    # Corr Beam 0
    assert Ensemble.float_to_bytes(1.1)[0] == result[132]
    assert Ensemble.float_to_bytes(1.1)[1] == result[133]
    assert Ensemble.float_to_bytes(1.1)[2] == result[134]
    assert Ensemble.float_to_bytes(1.1)[3] == result[135]
    # Corr Beam 1
    assert Ensemble.float_to_bytes(2.2)[0] == result[136]
    assert Ensemble.float_to_bytes(2.2)[1] == result[137]
    assert Ensemble.float_to_bytes(2.2)[2] == result[138]
    assert Ensemble.float_to_bytes(2.2)[3] == result[139]
    # Corr Beam 2
    assert Ensemble.float_to_bytes(3.3)[0] == result[140]
    assert Ensemble.float_to_bytes(3.3)[1] == result[141]
    assert Ensemble.float_to_bytes(3.3)[2] == result[142]
    assert Ensemble.float_to_bytes(3.3)[3] == result[143]
    # Corr Beam 3
    assert Ensemble.float_to_bytes(4.4)[0] == result[144]
    assert Ensemble.float_to_bytes(4.4)[1] == result[145]
    assert Ensemble.float_to_bytes(4.4)[2] == result[146]
    assert Ensemble.float_to_bytes(4.4)[3] == result[147]

    # Beam Velocity Beam 0
    assert Ensemble.float_to_bytes(1.1)[0] == result[148]
    assert Ensemble.float_to_bytes(1.1)[1] == result[149]
    assert Ensemble.float_to_bytes(1.1)[2] == result[150]
    assert Ensemble.float_to_bytes(1.1)[3] == result[151]
    # Beam Velocity Beam 1
    assert Ensemble.float_to_bytes(2.2)[0] == result[152]
    assert Ensemble.float_to_bytes(2.2)[1] == result[153]
    assert Ensemble.float_to_bytes(2.2)[2] == result[154]
    assert Ensemble.float_to_bytes(2.2)[3] == result[155]
    # Beam Velocity Beam 2
    assert Ensemble.float_to_bytes(3.3)[0] == result[156]
    assert Ensemble.float_to_bytes(3.3)[1] == result[157]
    assert Ensemble.float_to_bytes(3.3)[2] == result[158]
    assert Ensemble.float_to_bytes(3.3)[3] == result[159]
    # Beam Velocity Beam 3
    assert Ensemble.float_to_bytes(4.4)[0] == result[160]
    assert Ensemble.float_to_bytes(4.4)[1] == result[161]
    assert Ensemble.float_to_bytes(4.4)[2] == result[162]
    assert Ensemble.float_to_bytes(4.4)[3] == result[163]

    # Beam Good Beam 0
    assert Ensemble.float_to_bytes(1)[0] == result[164]
    assert Ensemble.float_to_bytes(1)[1] == result[165]
    assert Ensemble.float_to_bytes(1)[2] == result[166]
    assert Ensemble.float_to_bytes(1)[3] == result[167]
    # Beam Good Beam 1
    assert Ensemble.float_to_bytes(2)[0] == result[168]
    assert Ensemble.float_to_bytes(2)[1] == result[169]
    assert Ensemble.float_to_bytes(2)[2] == result[170]
    assert Ensemble.float_to_bytes(2)[3] == result[171]
    # Beam Good Beam 2
    assert Ensemble.float_to_bytes(3)[0] == result[172]
    assert Ensemble.float_to_bytes(3)[1] == result[173]
    assert Ensemble.float_to_bytes(3)[2] == result[174]
    assert Ensemble.float_to_bytes(3)[3] == result[175]
    # Beam Good Beam 3
    assert Ensemble.float_to_bytes(4)[0] == result[176]
    assert Ensemble.float_to_bytes(4)[1] == result[177]
    assert Ensemble.float_to_bytes(4)[2] == result[178]
    assert Ensemble.float_to_bytes(4)[3] == result[179]

    index = 180

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

    # Instrument Good Beam 0
    assert Ensemble.float_to_bytes(1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[3] == result[index]
    index += 1
    # Instrument Good Beam 1
    assert Ensemble.float_to_bytes(2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[3] == result[index]
    index += 1
    # Instrument Good Beam 2
    assert Ensemble.float_to_bytes(3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[3] == result[index]
    index += 1
    # Instrument Good Beam 3
    assert Ensemble.float_to_bytes(4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[3] == result[index]
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

    # Earth Good Beam 0
    assert Ensemble.float_to_bytes(1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[3] == result[index]
    index += 1
    # Earth Good Beam 1
    assert Ensemble.float_to_bytes(2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[3] == result[index]
    index += 1
    # Earth Good Beam 2
    assert Ensemble.float_to_bytes(3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[3] == result[index]
    index += 1
    # Earth Good Beam 3
    assert Ensemble.float_to_bytes(4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[3] == result[index]
    index += 1

    # SNR Pulse Coherent Beam 0
    assert Ensemble.float_to_bytes(1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[3] == result[index]
    index += 1
    # SNR Pulse Coherent Beam 1
    assert Ensemble.float_to_bytes(2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[3] == result[index]
    index += 1
    # SNR Pulse Coherent Beam 2
    assert Ensemble.float_to_bytes(3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[3] == result[index]
    index += 1
    # SNR Pulse Coherent Beam 3
    assert Ensemble.float_to_bytes(4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[3] == result[index]
    index += 1

    # Amp Pulse Coherent Beam 0
    assert Ensemble.float_to_bytes(1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[3] == result[index]
    index += 1
    # Amp Pulse Coherent Beam 1
    assert Ensemble.float_to_bytes(2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[3] == result[index]
    index += 1
    # Amp Pulse Coherent Beam 2
    assert Ensemble.float_to_bytes(3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[3] == result[index]
    index += 1
    # Amp Pulse Coherent Beam 3
    assert Ensemble.float_to_bytes(4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[3] == result[index]
    index += 1

    # Vel Pulse Coherent Beam 0
    assert Ensemble.float_to_bytes(1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[3] == result[index]
    index += 1
    # Vel Pulse Coherent Beam 1
    assert Ensemble.float_to_bytes(2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[3] == result[index]
    index += 1
    # Vel Pulse Coherent Beam 2
    assert Ensemble.float_to_bytes(3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[3] == result[index]
    index += 1
    # Vel Pulse Coherent Beam 3
    assert Ensemble.float_to_bytes(4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[3] == result[index]
    index += 1

    # Noise Pulse Coherent Beam 0
    assert Ensemble.float_to_bytes(1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[3] == result[index]
    index += 1
    # Noise Pulse Coherent Beam 1
    assert Ensemble.float_to_bytes(2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[3] == result[index]
    index += 1
    # Noise Pulse Coherent Beam 2
    assert Ensemble.float_to_bytes(3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[3] == result[index]
    index += 1
    # Noise Pulse Coherent Beam 3
    assert Ensemble.float_to_bytes(4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[3] == result[index]
    index += 1

    # Corr Pulse Coherent Beam 0
    assert Ensemble.float_to_bytes(1)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(1)[3] == result[index]
    index += 1
    # Corr Pulse Coherent Beam 1
    assert Ensemble.float_to_bytes(2)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(2)[3] == result[index]
    index += 1
    # Corr Pulse Coherent Beam 2
    assert Ensemble.float_to_bytes(3)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(3)[3] == result[index]
    index += 1
    # Corr Pulse Coherent Beam 3
    assert Ensemble.float_to_bytes(4)[0] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[1] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[2] == result[index]
    index += 1
    assert Ensemble.float_to_bytes(4)[3] == result[index]
    index += 1


def test_encode_csv():

    bt = BottomTrack()
    bt.FirstPingTime = 12.5
    bt.LastPingTime = 12.8
    bt.Heading = 152.36
    bt.Pitch = 12.6
    bt.Roll = 223.1
    bt.WaterTemp = 15.23
    bt.SystemTemp = 78.58
    bt.Salinity = 35.0
    bt.Pressure = 23.36
    bt.TransducerDepth = 156.2
    bt.SpeedOfSound = 1402.36
    bt.Status = 9.0
    bt.NumBeams = 4.0
    bt.ActualPingCount = 23
    bt.Range = [1.1, 2.2, 3.3, 4.4]
    bt.SNR = [1.1, 2.2, 3.3, 4.4]
    bt.Amplitude = [1.1, 2.2, 3.3, 4.4]
    bt.Correlation = [1.1, 2.2, 3.3, 4.4]
    bt.BeamVelocity = [1.1, 2.2, 3.3, 4.4]
    bt.BeamGood = [1, 2, 3, 4]
    bt.InstrumentVelocity = [1.1, 2.2, 3.3, 4.4]
    bt.InstrumentGood = [1, 2, 3, 4]
    bt.EarthVelocity = [1.1, 2.2, 3.3, 4.4]
    bt.EarthGood = [1, 2, 3, 4]
    bt.SNR_PulseCoherent = [1, 2, 3, 4]
    bt.Amp_PulseCoherent = [1, 2, 3, 4]
    bt.Vel_PulseCoherent = [1, 2, 3, 4]
    bt.Noise_PulseCoherent = [1, 2, 3, 4]
    bt.Corr_PulseCoherent = [1, 2, 3, 4]

    # Populate data

    dt = datetime.datetime.now()

    # Create CSV lines
    result = bt.encode_csv(dt, 'A', 1, 1.3, 1.0)

    # Check the csv data
    for line in result:
        if Ensemble.CSV_BT_STATUS in line:
            assert bool(re.search(str(9), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_BT_HEADING in line:
            assert bool(re.search(str(152.36), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_BT_PITCH in line:
            assert bool(re.search(str(12.6), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_BT_ROLL in line:
            assert bool(re.search(str(223.1), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_BT_PRESSURE in line:
            assert bool(re.search(str(23.36), line))
            assert bool(re.search(str(0), line))
        if Ensemble.CSV_BT_XDCR_DEPTH in line:
            assert bool(re.search(str(156.2), line))
            assert bool(re.search(str(0), line))


        if Ensemble.CSV_BT_RANGE in line:
            if "0,0" in line:
                assert bool(re.search(str(1.1), line))
            #if "0,1" in line:
            #    assert bool(re.search(str(2.2), line))
            if "0,2" in line:
                assert bool(re.search(str(3.3), line))
            if "0,3" in line:
                assert bool(re.search(str(4.4), line))

        if Ensemble.CSV_BT_BEAM_VEL in line:
            if "0,0" in line:
                assert bool(re.search(str(1.1), line))
            #if "0,1" in line:
            #    assert bool(re.search(str(2.2), line))
            if "0,2" in line:
                assert bool(re.search(str(3.3), line))
            if "0,3" in line:
                assert bool(re.search(str(4.4), line))
        if Ensemble.CSV_BT_BEAM_GOOD in line:
            if "0,0" in line:
                assert bool(re.search(str(1), line))
            #if "0,1" in line:
            #    assert bool(re.search(str(2.2), line))
            if "0,2" in line:
                assert bool(re.search(str(3), line))
            if "0,3" in line:
                assert bool(re.search(str(4), line))
        if Ensemble.CSV_BT_INSTR_VEL in line:
            if "0,0" in line:
                assert bool(re.search(str(1.1), line))
            #if "0,1" in line:
            #    assert bool(re.search(str(2.2), line))
            if "0,2" in line:
                assert bool(re.search(str(3.3), line))
            if "0,3" in line:
                assert bool(re.search(str(4.4), line))
        if Ensemble.CSV_BT_INSTR_GOOD in line:
            if "0,0" in line:
                assert bool(re.search(str(1), line))
            #if "0,1" in line:
            #    assert bool(re.search(str(2.2), line))
            if "0,2" in line:
                assert bool(re.search(str(3), line))
            if "0,3" in line:
                assert bool(re.search(str(4), line))
        if Ensemble.CSV_BT_EARTH_VEL in line:
            if "0,0" in line:
                assert bool(re.search(str(1.1), line))
            #if "0,1" in line:
            #    assert bool(re.search(str(2.2), line))
            if "0,2" in line:
                assert bool(re.search(str(3.3), line))
            if "0,3" in line:
                assert bool(re.search(str(4.4), line))
        if Ensemble.CSV_BT_EARTH_GOOD in line:
            if "0,0" in line:
                assert bool(re.search(str(1), line))
            #if "0,1" in line:
            #    assert bool(re.search(str(2.2), line))
            if "0,2" in line:
                assert bool(re.search(str(3), line))
            if "0,3" in line:
                assert bool(re.search(str(4), line))


def test_encode_decode():
    bt = BottomTrack()
    bt.FirstPingTime = 12.5
    bt.LastPingTime = 12.8
    bt.Heading = 152.36
    bt.Pitch = 12.6
    bt.Roll = 223.1
    bt.WaterTemp = 15.23
    bt.SystemTemp = 78.58
    bt.Salinity = 35.0
    bt.Pressure = 23.36
    bt.TransducerDepth = 156.2
    bt.SpeedOfSound = 1402.36
    bt.Status = 9.0
    bt.NumBeams = 4.0
    bt.ActualPingCount = 23
    bt.Range = [1.1, 2.2, 3.3, 4.4]
    bt.SNR = [1.1, 2.2, 3.3, 4.4]
    bt.Amplitude = [1.1, 2.2, 3.3, 4.4]
    bt.Correlation = [1.1, 2.2, 3.3, 4.4]
    bt.BeamVelocity = [1.1, 2.2, 3.3, 4.4]
    bt.BeamGood = [1, 2, 3, 4]
    bt.InstrumentVelocity = [1.1, 2.2, 3.3, 4.4]
    bt.InstrumentGood = [1, 2, 3, 4]
    bt.EarthVelocity = [1.1, 2.2, 3.3, 4.4]
    bt.EarthGood = [1, 2, 3, 4]
    bt.SNR_PulseCoherent = [1, 2, 3, 4]
    bt.Amp_PulseCoherent = [1, 2, 3, 4]
    bt.Vel_PulseCoherent = [1, 2, 3, 4]
    bt.Noise_PulseCoherent = [1, 2, 3, 4]
    bt.Corr_PulseCoherent = [1, 2, 3, 4]

    # Populate data

    result = bt.encode()

    bt1 = BottomTrack()
    bt1.decode(bytearray(result))

    assert bt.FirstPingTime == pytest.approx(bt1.FirstPingTime)
    assert bt.LastPingTime == pytest.approx(bt1.LastPingTime)
    assert bt.Heading == pytest.approx(bt1.Heading)
    assert bt.Pitch == pytest.approx(bt1.Pitch)
    assert bt.Roll == pytest.approx(bt1.Roll)
    assert bt.WaterTemp == pytest.approx(bt1.WaterTemp)
    assert bt.SystemTemp == pytest.approx(bt1.SystemTemp)
    assert bt.Salinity == pytest.approx(bt1.Salinity)
    assert bt.Pressure == pytest.approx(bt1.Pressure)
    assert bt.TransducerDepth == pytest.approx(bt1.TransducerDepth)
    assert bt.SpeedOfSound == pytest.approx(bt1.SpeedOfSound)
    assert bt.Status == pytest.approx(bt1.Status)
    assert bt.NumBeams == pytest.approx(bt1.NumBeams)
    assert bt.ActualPingCount == pytest.approx(bt1.ActualPingCount)
    assert bt.Range == pytest.approx(bt1.Range)
    assert bt.SNR == pytest.approx(bt1.SNR)
    assert bt.Amplitude == pytest.approx(bt1.Amplitude)
    assert bt.Correlation == pytest.approx(bt1.Correlation)
    assert bt.BeamVelocity == pytest.approx(bt1.BeamVelocity)
    assert bt.BeamGood == pytest.approx(bt1.BeamGood, 0.1)
    assert bt.InstrumentVelocity == pytest.approx(bt1.InstrumentVelocity)
    assert bt.InstrumentGood == pytest.approx(bt1.InstrumentGood, 0.1)
    assert bt.EarthVelocity == pytest.approx(bt1.EarthVelocity)
    assert bt.EarthGood == pytest.approx(bt1.EarthGood, 0.1)
    assert bt.SNR_PulseCoherent == pytest.approx(bt1.SNR_PulseCoherent, 0.1)
    assert bt.Amp_PulseCoherent == pytest.approx(bt1.Amp_PulseCoherent, 0.1)
    assert bt.Vel_PulseCoherent == pytest.approx(bt1.Vel_PulseCoherent, 0.1)
    assert bt.Noise_PulseCoherent == pytest.approx(bt1.Noise_PulseCoherent, 0.1)
    assert bt.Corr_PulseCoherent == pytest.approx(bt1.Corr_PulseCoherent, 0.1)
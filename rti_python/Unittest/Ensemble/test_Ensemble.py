import pytest

from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Ensemble.Amplitude import Amplitude
from rti_python.Ensemble.Correlation import Correlation
from rti_python.Ensemble.BeamVelocity import BeamVelocity
from rti_python.Ensemble.InstrumentVelocity import InstrumentVelocity
from rti_python.Ensemble.EarthVelocity import EarthVelocity
from rti_python.Ensemble.GoodBeam import GoodBeam
from rti_python.Ensemble.GoodEarth import GoodEarth
from rti_python.Ensemble.AncillaryData import AncillaryData
from rti_python.Ensemble.EnsembleData import EnsembleData
from rti_python.Ensemble.BottomTrack import BottomTrack
from rti_python.Ensemble.RangeTracking import RangeTracking
from rti_python.Ensemble.SystemSetup import SystemSetup
from rti_python.Codecs.BinaryCodec import BinaryCodec
from rti_python.Ensemble.NmeaData import NmeaData


def test_generate_header():

    value_type = 10             # Float
    num_elements = 30           # 30 bins
    element_multiplier = 4      # 4 Beams
    imag = 0                    # NOT USED
    name_length = 8             # Length of name
    name = "E000004\0"            # Amp name

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
    assert ord('4') == header[26]
    assert ord('\0') == header[27]


def test_amplitude():

    amp = Amplitude(30, 4)

    # Populate data
    val = 1.0
    for beam in range(amp.element_multiplier):
        for bin_num in range(amp.num_elements):
            amp.Amplitude[bin_num][beam] = val
            val += 1.1

    result = amp.encode()

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
    assert ord('4') == result[26]
    assert ord('\0') == result[27]

    # Length
    assert len(result) == 28 + ((amp.element_multiplier * amp.num_elements) * Ensemble.BytesInFloat)

    # Amplitude data
    result_val = 1.0
    index = 28                  # 28 = Header size
    for beam in range(amp.element_multiplier):
        for bin_num in range(amp.num_elements):
            test_val = Ensemble.GetFloat(index, Ensemble().BytesInFloat, bytearray(result))
            assert result_val == pytest.approx(test_val, 0.1)
            result_val += 1.1
            index += Ensemble().BytesInFloat


def test_encode_csv():

    num_bins = 33
    num_beams = 4

    ens = Ensemble()
    amp = Amplitude(num_bins, num_beams)
    corr = Correlation(num_bins, num_beams)
    beam_vel = BeamVelocity(num_bins, num_beams)
    inst_vel = InstrumentVelocity(num_bins, num_beams)
    earth_vel = EarthVelocity(num_bins, num_beams)
    gb = GoodBeam(num_bins, num_beams)
    ge = GoodEarth(num_bins, num_beams)
    anc = AncillaryData()
    ensData = EnsembleData()
    ss = SystemSetup()

    bt = BottomTrack()
    bt.NumBeams = 4
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

    ens.AddAmplitude(amp)
    ens.AddCorrelation(corr)
    ens.AddBeamVelocity(beam_vel)
    ens.AddInstrumentVelocity(inst_vel)
    ens.AddEarthVelocity(earth_vel)
    ens.AddGoodBeam(gb)
    ens.AddGoodEarth(ge)
    ens.AddAncillaryData(anc)
    ens.AddEnsembleData(ensData)
    ens.AddBottomTrack(bt)
    ens.AddRangeTracking(rt)
    ens.AddSystemSetup(ss)

    results = ens.encode_csv()
    total_lines = num_bins * num_beams * 7
    total_lines += num_bins * 2             # Mag and Direction in EarthVelocity
    total_lines += 6 + (num_beams * 7)      # Bottom Track
    total_lines += 1                        # Ensemble Data
    total_lines += 10                       # Ancillary Data
    total_lines += 5 * num_beams            # Range Tracking
    total_lines += 1                        # System Settings

    assert len(results) == total_lines

def test_encode_csv_no_bt():

    num_bins = 33
    num_beams = 4

    ens = Ensemble()
    amp = Amplitude(num_bins, num_beams)
    corr = Correlation(num_bins, num_beams)
    beam_vel = BeamVelocity(num_bins, num_beams)
    inst_vel = InstrumentVelocity(num_bins, num_beams)
    earth_vel = EarthVelocity(num_bins, num_beams)
    gb = GoodBeam(num_bins, num_beams)
    ge = GoodEarth(num_bins, num_beams)
    anc = AncillaryData()
    ensData = EnsembleData()
    ss = SystemSetup()

    bt = BottomTrack()
    bt.NumBeams = 4
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

    ens.AddAmplitude(amp)
    ens.AddCorrelation(corr)
    ens.AddBeamVelocity(beam_vel)
    ens.AddInstrumentVelocity(inst_vel)
    ens.AddEarthVelocity(earth_vel)
    ens.AddGoodBeam(gb)
    ens.AddGoodEarth(ge)
    ens.AddAncillaryData(anc)
    ens.AddEnsembleData(ensData)
    ens.AddBottomTrack(bt)
    ens.AddRangeTracking(rt)
    ens.AddSystemSetup(ss)

    results = ens.encode_csv(is_bottom_track=False)
    total_lines = num_bins * num_beams * 7
    total_lines += num_bins * 2             # Mag and Direction in EarthVelocity
    #total_lines += 6 + (num_beams * 7)      # Bottom Track
    total_lines += 1                        # Ensemble Data
    total_lines += 10                       # Ancillary Data
    total_lines += 5 * num_beams            # Range Tracking
    total_lines += 1                        # System Settings

    assert len(results) == total_lines


def test_encode_csv_no_anc():

    num_bins = 33
    num_beams = 4

    ens = Ensemble()
    amp = Amplitude(num_bins, num_beams)
    corr = Correlation(num_bins, num_beams)
    beam_vel = BeamVelocity(num_bins, num_beams)
    inst_vel = InstrumentVelocity(num_bins, num_beams)
    earth_vel = EarthVelocity(num_bins, num_beams)
    gb = GoodBeam(num_bins, num_beams)
    ge = GoodEarth(num_bins, num_beams)
    anc = AncillaryData()
    ensData = EnsembleData()
    ss = SystemSetup()

    bt = BottomTrack()
    bt.NumBeams = 4
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

    ens.AddAmplitude(amp)
    ens.AddCorrelation(corr)
    ens.AddBeamVelocity(beam_vel)
    ens.AddInstrumentVelocity(inst_vel)
    ens.AddEarthVelocity(earth_vel)
    ens.AddGoodBeam(gb)
    ens.AddGoodEarth(ge)
    ens.AddAncillaryData(anc)
    ens.AddEnsembleData(ensData)
    ens.AddBottomTrack(bt)
    ens.AddRangeTracking(rt)
    ens.AddSystemSetup(ss)

    results = ens.encode_csv(is_ancillary_data=False)
    total_lines = num_bins * num_beams * 7
    total_lines += num_bins * 2             # Mag and Direction in EarthVelocity
    total_lines += 6 + (num_beams * 7)      # Bottom Track
    total_lines += 1                        # Ensemble Data
    #total_lines += 10                       # Ancillary Data
    total_lines += 5 * num_beams            # Range Tracking
    total_lines += 1                        # System Settings

    assert len(results) == total_lines

def test_encode_decode():

    num_bins = 33
    num_beams = 4

    ens = Ensemble()

    ens_ds = EnsembleData()
    ens_ds.EnsembleNumber = 2668
    ens_ds.NumBins = 33
    ens_ds.NumBeams = 4
    ens_ds.DesiredPingCount = 45
    ens_ds.ActualPingCount = 46
    ens_ds.SerialNumber = "01H00000000000000000000000999999"
    ens_ds.SysFirmwareMajor = 2
    ens_ds.SysFirmwareMinor = 11
    ens_ds.SysFirmwareRevision = 5
    ens_ds.SysFirmwareSubsystemCode = "A"
    ens_ds.SubsystemConfig = 3
    ens_ds.Status = 9
    ens_ds.Year = 2019
    ens_ds.Month = 3
    ens_ds.Day = 9
    ens_ds.Hour = 12
    ens_ds.Minute = 23
    ens_ds.Second = 24
    ens_ds.HSec = 33

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
    anc.PitchGravityVector = 4.0  # Pitch Gravity Vector
    anc.RollGravityVector = 5.0  # Roll Gravity Vector
    anc.VerticalGravityVector = 6.0  # Vertical Gravity Vector

    amp = Amplitude(num_bins, num_beams)
    corr = Correlation(num_bins, num_beams)
    beam_vel = BeamVelocity(num_bins, num_beams)
    inst_vel = InstrumentVelocity(num_bins, num_beams)
    earth_vel = EarthVelocity(num_bins, num_beams)
    gb = GoodBeam(num_bins, num_beams)
    ge = GoodEarth(num_bins, num_beams)
    val = 1.0
    for beam in range(amp.element_multiplier):
        for bin_num in range(amp.num_elements):
            amp.Amplitude[bin_num][beam] = val
            corr.Correlation[bin_num][beam] = val
            beam_vel.Velocities[bin_num][beam] = val
            inst_vel.Velocities[bin_num][beam] = val
            earth_vel.Velocities[bin_num][beam] = val
            gb.GoodBeam[bin_num][beam] = 1 * int(beam)
            ge.GoodEarth[bin_num][beam] = 1 * int(beam)
            val += 1.1

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

    nmea = NmeaData()
    nmea.add_nmea("$HEHDT,244.39,T*17\n")
    nmea.add_nmea("$GPGGA,195949.00,3254.8103248,N,11655.5779629,W,2,08,1.1,222.174,M,-32.602,M,6.0,0138*75\n")
    nmea.add_nmea("$GPVTG,306.20,T,294.73,M,0.13,N,0.24,K,D*2E\n")
    nmea.add_nmea("$HEHDT,244.36,T*18\n")

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

    ens.AddAmplitude(amp)
    ens.AddCorrelation(corr)
    ens.AddBeamVelocity(beam_vel)
    ens.AddInstrumentVelocity(inst_vel)
    ens.AddEarthVelocity(earth_vel)
    ens.AddGoodBeam(gb)
    ens.AddGoodEarth(ge)
    ens.AddAncillaryData(anc)
    ens.AddEnsembleData(ens_ds)
    ens.AddBottomTrack(bt)
    ens.AddRangeTracking(rt)
    ens.AddSystemSetup(ss)
    ens.AddNmeaData(nmea)

    # Encode the ensemble to binar
    binary_ens = ens.encode()

    # Use the codec to decode the data
    ens1 = BinaryCodec.decode_data_sets(binary_ens[:-4])      # Remove the checksum

    assert ens.EnsembleData.EnsembleNumber == ens1.EnsembleData.EnsembleNumber
    assert ens.EnsembleData.NumBins == ens1.EnsembleData.NumBins
    assert ens.EnsembleData.NumBeams == ens1.EnsembleData.NumBeams
    assert ens.EnsembleData.DesiredPingCount == ens1.EnsembleData.DesiredPingCount
    assert ens.EnsembleData.ActualPingCount == ens1.EnsembleData.ActualPingCount
    assert ens.EnsembleData.SerialNumber == ens1.EnsembleData.SerialNumber
    assert ens.EnsembleData.SysFirmwareMajor == ens1.EnsembleData.SysFirmwareMajor
    assert ens.EnsembleData.SysFirmwareMinor == ens1.EnsembleData.SysFirmwareMinor
    assert ens.EnsembleData.SysFirmwareRevision == ens1.EnsembleData.SysFirmwareRevision
    assert ens.EnsembleData.SysFirmwareSubsystemCode == ens1.EnsembleData.SysFirmwareSubsystemCode
    assert ens.EnsembleData.SubsystemConfig == ens1.EnsembleData.SubsystemConfig
    assert ens.EnsembleData.Status == ens1.EnsembleData.Status
    assert ens.EnsembleData.Year == ens1.EnsembleData.Year
    assert ens.EnsembleData.Month == ens1.EnsembleData.Month
    assert ens.EnsembleData.Day == ens1.EnsembleData.Day
    assert ens.EnsembleData.Hour == ens1.EnsembleData.Hour
    assert ens.EnsembleData.Minute == ens1.EnsembleData.Minute
    assert ens.EnsembleData.Second == ens1.EnsembleData.Second
    assert ens.EnsembleData.HSec == ens1.EnsembleData.HSec

    assert anc.FirstBinRange == pytest.approx(ens1.AncillaryData.FirstBinRange, 0.1)
    assert anc.BinSize == pytest.approx(ens1.AncillaryData.BinSize, 0.1)
    assert anc.FirstPingTime == pytest.approx(ens1.AncillaryData.FirstPingTime, 0.1)
    assert anc.LastPingTime == pytest.approx(ens1.AncillaryData.LastPingTime, 0.1)
    assert anc.Heading == pytest.approx(ens1.AncillaryData.Heading, 0.1)
    assert anc.Pitch == pytest.approx(ens1.AncillaryData.Pitch, 0.1)
    assert anc.Roll == pytest.approx(ens1.AncillaryData.Roll, 0.1)
    assert anc.WaterTemp == pytest.approx(ens1.AncillaryData.WaterTemp, 0.1)
    assert anc.SystemTemp == pytest.approx(ens1.AncillaryData.SystemTemp, 0.1)
    assert anc.Salinity == pytest.approx(ens1.AncillaryData.Salinity, 0.1)
    assert anc.Pressure == pytest.approx(ens1.AncillaryData.Pressure, 0.1)
    assert anc.TransducerDepth == pytest.approx(ens1.AncillaryData.TransducerDepth, 0.1)
    assert anc.SpeedOfSound == pytest.approx(ens1.AncillaryData.SpeedOfSound, 0.1)
    assert anc.RawMagFieldStrength == pytest.approx(ens1.AncillaryData.RawMagFieldStrength, 0.1)
    assert anc.PitchGravityVector == pytest.approx(ens1.AncillaryData.PitchGravityVector, 0.1)
    assert anc.RollGravityVector == pytest.approx(ens1.AncillaryData.RollGravityVector, 0.1)
    assert anc.VerticalGravityVector == pytest.approx(ens1.AncillaryData.VerticalGravityVector, 0.1)

    for beam in range(amp.element_multiplier):
        for bin_num in range(amp.num_elements):
            assert amp.Amplitude[bin_num][beam] == pytest.approx(ens1.Amplitude.Amplitude[bin_num][beam], 0.1)

    for beam in range(corr.element_multiplier):
        for bin_num in range(corr.num_elements):
            assert corr.Correlation[bin_num][beam] == pytest.approx(ens1.Correlation.Correlation[bin_num][beam], 0.1)

    for beam in range(beam_vel.element_multiplier):
        for bin_num in range(beam_vel.num_elements):
            assert beam_vel.Velocities[bin_num][beam] == pytest.approx(ens1.Wt.Velocities[bin_num][beam], 0.1)

    for beam in range(beam_vel.element_multiplier):
        for bin_num in range(beam_vel.num_elements):
            assert inst_vel.Velocities[bin_num][beam] == pytest.approx(ens1.InstrumentVelocity.Velocities[bin_num][beam], 0.1)

    for beam in range(beam_vel.element_multiplier):
        for bin_num in range(beam_vel.num_elements):
            assert earth_vel.Velocities[bin_num][beam] == pytest.approx(ens1.EarthVelocity.Velocities[bin_num][beam], 0.1)

    #for beam in range(gb.element_multiplier):
    #    for bin_num in range(gb.num_elements):
    #        assert gb.GoodBeam[bin_num][beam] == pytest.approx(ens1.GoodBeam.GoodBeam[bin_num][beam], 0.1)

    for beam in range(ge.element_multiplier):
        for bin_num in range(ge.num_elements):
            assert ge.GoodEarth[bin_num][beam] == pytest.approx(ens1.GoodEarth.GoodEarth[bin_num][beam], 0.1)

    assert bt.FirstPingTime == pytest.approx(ens1.BottomTrack.FirstPingTime)
    assert bt.LastPingTime == pytest.approx(ens1.BottomTrack.LastPingTime)
    assert bt.Heading == pytest.approx(ens1.BottomTrack.Heading)
    assert bt.Pitch == pytest.approx(ens1.BottomTrack.Pitch)
    assert bt.Roll == pytest.approx(ens1.BottomTrack.Roll)
    assert bt.WaterTemp == pytest.approx(ens1.BottomTrack.WaterTemp)
    assert bt.SystemTemp == pytest.approx(ens1.BottomTrack.SystemTemp)
    assert bt.Salinity == pytest.approx(ens1.BottomTrack.Salinity)
    assert bt.Pressure == pytest.approx(ens1.BottomTrack.Pressure)
    assert bt.TransducerDepth == pytest.approx(ens1.BottomTrack.TransducerDepth)
    assert bt.SpeedOfSound == pytest.approx(ens1.BottomTrack.SpeedOfSound)
    assert bt.Status == pytest.approx(ens1.BottomTrack.Status)
    assert bt.NumBeams == pytest.approx(ens1.BottomTrack.NumBeams)
    assert bt.ActualPingCount == pytest.approx(ens1.BottomTrack.ActualPingCount)
    assert bt.Range == pytest.approx(ens1.BottomTrack.Range)
    assert bt.SNR == pytest.approx(ens1.BottomTrack.SNR)
    assert bt.Amplitude == pytest.approx(ens1.BottomTrack.Amplitude)
    assert bt.Correlation == pytest.approx(ens1.BottomTrack.Correlation)
    assert bt.BeamVelocity == pytest.approx(ens1.BottomTrack.Wt)
    assert bt.BeamGood == pytest.approx(ens1.BottomTrack.BeamGood, 0.1)
    assert bt.InstrumentVelocity == pytest.approx(ens1.BottomTrack.InstrumentVelocity)
    assert bt.InstrumentGood == pytest.approx(ens1.BottomTrack.InstrumentGood, 0.1)
    assert bt.EarthVelocity == pytest.approx(ens1.BottomTrack.EarthVelocity)
    assert bt.EarthGood == pytest.approx(ens1.BottomTrack.EarthGood, 0.1)
    assert bt.SNR_PulseCoherent == pytest.approx(ens1.BottomTrack.SNR_PulseCoherent, 0.1)
    assert bt.Amp_PulseCoherent == pytest.approx(ens1.BottomTrack.Amp_PulseCoherent, 0.1)
    assert bt.Vel_PulseCoherent == pytest.approx(ens1.BottomTrack.Vel_PulseCoherent, 0.1)
    assert bt.Noise_PulseCoherent == pytest.approx(ens1.BottomTrack.Noise_PulseCoherent, 0.1)
    assert bt.Corr_PulseCoherent == pytest.approx(ens1.BottomTrack.Corr_PulseCoherent, 0.1)

    assert rt.NumBeams == ens1.RangeTracking.NumBeams
    assert rt.Range == pytest.approx(ens1.RangeTracking.Range)
    assert rt.SNR == pytest.approx(ens1.RangeTracking.SNR)
    assert rt.Amplitude == pytest.approx(ens1.RangeTracking.Amplitude)
    assert rt.Correlation == pytest.approx(ens1.RangeTracking.Correlation)
    assert rt.BeamVelocity == pytest.approx(ens1.RangeTracking.Wt)
    assert rt.InstrumentVelocity == pytest.approx(ens1.RangeTracking.InstrumentVelocity)
    assert rt.EarthVelocity == pytest.approx(ens1.RangeTracking.EarthVelocity)

    assert nmea.nmea_sentences == ens1.NmeaData.nmea_sentences

    assert ss.BtSamplesPerSecond == pytest.approx(ens1.SystemSetup.BtSamplesPerSecond, 0.1)
    assert ss.BtSystemFreqHz == pytest.approx(ens1.SystemSetup.BtSystemFreqHz, 0.1)
    assert ss.BtCPCE == pytest.approx(ens1.SystemSetup.BtCPCE, 0.1)
    assert ss.BtNCE == pytest.approx(ens1.SystemSetup.BtNCE, 0.1)
    assert ss.BtRepeatN == pytest.approx(ens1.SystemSetup.BtRepeatN, 0.1)
    assert ss.WpSamplesPerSecond == pytest.approx(ens1.SystemSetup.WpSamplesPerSecond, 0.1)
    assert ss.WpSystemFreqHz == pytest.approx(ens1.SystemSetup.WpSystemFreqHz, 0.1)
    assert ss.WpCPCE == pytest.approx(ens1.SystemSetup.WpCPCE, 0.1)
    assert ss.WpNCE == pytest.approx(ens1.SystemSetup.WpNCE, 0.1)
    assert ss.WpRepeatN == pytest.approx(ens1.SystemSetup.WpRepeatN, 0.1)
    assert ss.WpLagSamples == pytest.approx(ens1.SystemSetup.WpLagSamples, 0.1)
    assert ss.Voltage == pytest.approx(ens1.SystemSetup.Voltage, 0.1)
    assert ss.XmtVoltage == pytest.approx(ens1.SystemSetup.XmtVoltage, 0.1)
    assert ss.BtBroadband == pytest.approx(ens1.SystemSetup.BtBroadband, 0.1)
    assert ss.BtLagLength == pytest.approx(ens1.SystemSetup.BtLagLength, 0.1)
    assert ss.BtNarrowband == pytest.approx(ens1.SystemSetup.BtNarrowband, 0.1)
    assert ss.BtBeamMux == pytest.approx(ens1.SystemSetup.BtBeamMux, 0.1)
    assert ss.WpBroadband == pytest.approx(ens1.SystemSetup.WpBroadband, 0.1)
    assert ss.WpLagLength == pytest.approx(ens1.SystemSetup.WpLagLength, 0.1)
    assert ss.WpTransmitBandwidth == pytest.approx(ens1.SystemSetup.WpTransmitBandwidth, 0.1)
    assert ss.WpReceiveBandwidth == pytest.approx(ens1.SystemSetup.WpReceiveBandwidth, 0.1)


def test_ones_compliment():
    value = 0x9E
    result = Ensemble.ones_complement(value)
    assert 0x61 == result

    value = 22
    result = Ensemble.oness_complement(value)
    assert 9 == result





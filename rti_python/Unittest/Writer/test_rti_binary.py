from rti_python.Writer.rti_binary import RtiBinaryWriter
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
from rti_python.Ensemble.NmeaData import NmeaData


def test_write_binary():
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

    rti_writer = RtiBinaryWriter("C:\RTI_capture")

    for ens_count in range(0, 100):
        bin_data = ens.encode()
        rti_writer.write(bin_data)
        ens.EnsembleData.EnsembleNumber += 1

    rti_writer.close()



class Ensemble_Compactor:
    """
    Compact an ensemble.  To reduce the data passed over the network
    and stored in the cloud.  The variable names are reduced.
    There are no dataset descriptions.  All the datasets are merged
    into one object.
    """


    def __init__(self):
        self.BVel = None                        # Beam Velocity
        self.IVel = None                        # Instrument Velocity
        self.EVel = None                        # Earth Velocity
        self.Amp = None                         # Amplitude
        self.Corr = None                        # Correlation
        self.GB = None                          # Good Beam
        self.GE = None                          # Good Earth

        self.EnsNum = 0                         # Ensemble Number
        self.NBins = 0                          # Number of bins
        self.NBeams = 0                         # Number of beams
        self.DPC = 0                            # Desired Ping Count
        self.APC = 0                            # Actual Ping Count
        self.SerialNum = ""
        self.FMajor = ""                        # Firmware Major
        self.FMinor = ""                        # Firmware Minor
        self.FRev = ""                          # Firmware Revision
        self.FSsCode = ""                       # Firmware Subsystem code
        self.SsConfig = ""                      # Subsystem Config
        self.Status = 0
        self.DT = ""                            # Date Time String

        self.FBR = 0.0                          # Blank.  Depth to the first bin in meters.
        self.BSize = 0.0                        # Size of a bin in meters.
        self.FPT = 0.0                          # First Ping Time in seconds.
        self.LPT = 0.0                          # Last Ping Time in seconds.  (If averaging pings, this will be the last ping)
        self.Hdg = 0.0                          # Heading in degrees.
        self.Ptch = 0.0                         # Pitch in degrees.
        self.Roll = 0.0                         # Roll in degrees.
        self.WTemp = 0.0                        # Water Temperature in fahrenheit
        self.STemp = 0.0                        # System Temperature in fahrenheit
        self.Sal = 0.0                          # Water Salinity set by the user in PPT
        self.Pres = 0.0                         # Pressure from pressure sensor in Pascals
        self.XdcrDepth = 0.0                    # Transducer Depth, used by Pressure sensor in meters
        self.SOS = 0.0                          # Speed of Sound in m/s.

        self.bt_Status = 0.0                    # Bottom Track Status
        self.bt_APCnt = 0.0                     # Bottom Track Actual Ping Count
        self.bt_Range = []                      # Bottom Track Range
        self.bt_SNR = []                        # Bottom Track Signal to Noise Ratio
        self.bt_Amp = []                        # Bottom Track Amplitude
        self.bt_Corr = []                       # Bottom Track Correlation
        self.bt_BVel = []                       # Bottom Track Beam Velocity
        self.bt_GB = []                         # Bottom Track Good Beam
        self.bt_IVel = []                       # Bottom Track Instrument Velocity
        self.bt_GI = []                         # Bottom Track Good Instrument
        self.bt_EVel = []                       # Bottom Track Earth Velocity
        self.bt_GE = []                         # Bottom Track Good Earth

        self.rt_SNR = []                        # Range Track SNR
        self.rt_Range = []                      # Range Track Range
        self.rt_Pings = []                      # Range Track Pings
        self.rt_Amp = []                        # Range Track Amplitude
        self.rt_Cor = []                        # Range Track Correlation
        self.rt_BVel = []                       # Range Track Beam Velocity
        self.rt_IVel = []                       # Range Track Instrument Velocity
        self.rt_EVel = []                       # Range Track Earth Velocity

    def compact(self, ens):
        """
        Compact the ensemble to smaller object.
        This is used to pass a smaller amount of data over the network.
        This will be a complete ensemble.
        :param ens: Ensemble to compact.
        :return:
        """
        if ens.IsBeamVelocity:
            self.BVel = ens.Wt.Velocities

        if ens.IsInstrumentVelocity:
            self.IVel = ens.InstrumentVelocity.Velocities

        if ens.IsEarthVelocity:
            self.EVel = ens.EarthVelocity.Velocities

        if ens.IsAmplitude:
            self.Amp = ens.Amplitude.Amplitude

        if ens.IsCorrelation:
            self.Corr = ens.Correlation.Correlation

        if ens.IsGoodBeam:
            self.GB = ens.GoodBeam.GoodBeam

        if ens.IsGoodEarth:
            self.GE = ens.GoodEarth.GoodEarth

        if ens.IsEnsembleData:
            self.EnsNum = ens.EnsembleData.EnsembleNumber
            self.NBins = ens.EnsembleData.NumBins
            self.NBeams = ens.EnsembleData.NumBeams
            self.DPC = ens.EnsembleData.DesiredPingCount
            self.APC = ens.EnsembleData.ActualPingCount
            self.SerNum = ens.EnsembleData.SerialNumber
            self.FMajor = ens.EnsembleData.SysFirmwareMajor
            self.FMinor = ens.EnsembleData.SysFirmwareMinor
            self.FRev = ens.EnsembleData.SysFirmwareRevision
            self.FSsCode = ens.EnsembleData.SysFirmwareSubsystemCode
            self.SsConfig = ens.EnsembleData.SubsystemConfig
            self.Status = ens.EnsembleData.Status
            self.DT = ens.EnsembleData.datetime_str()

        if ens.IsAncillaryData:
            self.FBR = ens.AncillaryData.FirstBinRange
            self.BSize = ens.AncillaryData.BinSize
            self.FPT = ens.AncillaryData.FirstPingTime
            self.LPT = ens.AncillaryData.LastPingTime
            self.Hdg = ens.AncillaryData.Heading
            self.Ptch = ens.AncillaryData.Pitch
            self.Roll = ens.AncillaryData.Roll
            self.WTemp = ens.AncillaryData.WaterTemp
            self.STemp = ens.AncillaryData.SystemTemp
            self.Sal = ens.AncillaryData.Salinity
            self.Pres = ens.AncillaryData.Pressure
            self.XdcrDepth = ens.AncillaryData.TransducerDepth
            self.SOS = ens.AncillaryData.SpeedOfSound

        if ens.IsBottomTrack:
            self.bt_Status = ens.BottomTrack.Status
            self.bt_APCnt = ens.BottomTrack.ActualPingCount
            self.bt_Range = ens.BottomTrack.Range
            self.bt_SNR = ens.BottomTrack.SNR
            self.bt_Amp = ens.BottomTrack.Amplitude
            self.bt_Corr = ens.BottomTrack.Correlation
            self.bt_BVel = ens.BottomTrack.Wt
            self.bt_GB = ens.BottomTrack.BeamGood
            self.bt_IVel = ens.BottomTrack.InstrumentVelocity
            self.bt_GI = ens.BottomTrack.InstrumentGood
            self.bt_EVel = ens.BottomTrack.EarthVelocity
            self.bt_GE = ens.BottomTrack.EarthGood

        if ens.IsRangeTracking:
            self.rt_SNR = ens.RangeTracking.SNR
            self.rt_Range = ens.RangeTracking.Range
            self.rt_Pings = ens.RangeTracking.Pings
            self.rt_Amp = ens.RangeTracking.Amplitude
            self.rt_Cor = ens.RangeTracking.Correlation
            self.rt_BVel = ens.RangeTracking.Wt
            self.rt_IVel = ens.RangeTracking.InstrumentVelocity
            self.rt_EVel = ens.RangeTracking.EarthVelocity
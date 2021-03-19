

class EnsembleJsonData:
    """
    Create an Ensemble data in JSON form.
    """

    def __init__(self):
        """
        Class to hold a complete ensemble.
        """
        self.EnsembleNumber = 0

        self.IsAmplitude = False
        self.Amplitude = None
        self.IsBeamVelocity = False
        self.BeamVelocity = None
        self.IsInstrumentVelocity = False
        self.InstrumentVelocity = None
        self.IsEarthVelocity = False
        self.EarthVelocity = None
        self.IsCorrelation = False
        self.Correlation = None
        self.IsBottomTrack = False
        self.BottomTrack = None
        self.IsEnsembleData = False
        self.EnsembleData = None
        self.IsAncillaryData = False
        self.AncillaryData = None
        self.IsRangeTracking = False
        self.RangeTracking = None

    def process(self, json_data):
        """
        Process the JSON data that contains the ADCP data.
        :param json_data: JSON ADCP data.
        :return:
        """
        #logger.info(jsonData["Name"])

        # Beam Velocity
        if "E000001" in json_data["Name"]:
            self.BeamVelocity = json_data
            self.IsBeamVelocity = True

        # Instrument Velocity
        if "E000002" in json_data["Name"]:
            self.InstrumentVelocity = json_data
            self.IsInstrumentVelocity = True

        # Earth Velocity
        if "E000003" in json_data["Name"]:
            self.EarthVelocity = json_data
            self.IsEarthVelocity = True

        # Amplitude
        if "E000004" in json_data["Name"]:
            self.Amplitude = json_data
            self.IsAmplitude = True

        # Correlation
        if "E000005" in json_data["Name"]:
            self.Correlation = json_data
            self.IsCorrelation = True

        # Ensemble Data
        if "E000008" in json_data["Name"]:
            self.EnsembleData = json_data
            self.IsEnsembleData = True

        # Ancillary Data
        if "E000009" in json_data["Name"]:
            self.AncillaryData = json_data
            self.AncillaryData = True

        # Bottom Track
        if "E000010" in json_data["Name"]:
            self.BottomTrack = json_data
            self.IsBottomTrack = True

        # Range Tracking
        if "E000015" in json_data["Name"]:
            self.RangeTracking = json_data
            self.IsRangeTracking = True

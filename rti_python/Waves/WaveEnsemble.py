import struct
import datetime
from rti_python.Ensemble.Ensemble import Ensemble


class WaveEnsemble:
    """
    Ensemble data specific to a wave ensemble.
    This will not need all the data that the entire ensemble will have.
    The float values will be converted to a byte array.
    """

    def __init__(self, ens, selected_bins, height_source=4, corr_thresh=0.25, pressure_offset=0.0):
        """
        Use the ensemble data to create a wave ensemble.  This will take only the data needed
        for waves processing.  It will also do some screening on the data.  The user can select
        how many bins that will be processed.
        :param ens: Ensemble to get the data.
        :param selected_bins: The bins selected to process.
        :param height_source: The height source.  Default: 4.  The default is to used vert_beam_height which is average of range tracking.
        :param corr_thresh: Correlation threshold.  Used to verify the data is good.  Default: 0.25
        :param pressure_offset: Pressure offset added to the depth measured from the pressure sensor in meters.  Default: 0
        """

        """
        Set flag if this data is a vertical ensemble.
        TRUE = Vertical beam ensemble.
        """
        self.is_vertical_ens = False

        """
        WZBM
        Vertical Beam velocity in meters/sec.
        """
        self.vert_beam_vel = []

        """
        WZHS
        Vertical beam height in meters.
        This is the average of all the range tracking values.
        """
        self.vert_beam_height = 0.0

        """
        WPS
        Pressure in meters.
        """
        self.pressure = 0.0

        """
        WTS
        Water temperature in degree fahrenheit.
        """
        self.water_temp = 0.0

        """
        WHG
        Heading in degrees.
        """
        self.heading = 0.0

        """
        WPH
        Pitch in degrees.
        """
        self.pitch = 0.0

        """
        WRL
        Roll in degrees.
        """
        self.roll = 0.0

        """
        WBM
        Beam velocity in m/s.
        [bin, beam]
        """
        self.beam_vel = []

        """
        WTS
        Time stamp in seconds.
        """
        self.time_stamp_seconds = 0.0

        """
        WSHS
        Range Tracking in meters.
        [Beams]
        """
        self.range_tracking = []

        """
        WAH
        Average range tracking.
        Average height.
        """
        self.avg_range_tracking = 0.0

        """
        Height source which is derived from the selected height source.
        """
        self.height = 0.0

        """
        Wave sample number.
        A burst will contain x ensembles(samples) in the burst.  This is the number
        of the sample within a burst.
        """
        self.sample_num = 0

        """
        Ensemble number.
        """
        self.ensemble_number = 0

        """
        Serial number
        """
        self.serial_number = ""

        """
        Subsystem Code.
        """
        self.ss_code = ""

        """
        Subsystem Configuration.
        """
        self.ss_config = 0

        """
        Date and time of ensemble
        """
        self.ens_datetime = datetime.datetime.now()

        """
        Number of beams.
        """
        self.num_beams = 1

        """
        Number of bins.
        """
        self.num_bins = 1

        """
        WUS
        East Velocity data for the given selected bins in m/s.
        [bins]
        """
        self.east_vel = []

        """
        WVS
        North Velocity data for the given selected bins in m/s.
        [bins]
        """
        self.north_vel = []

        """
        WZS
        Vertical velocity data for the given selected bins in m/s.
        """
        self.vertical_vel = []

        """USER OPTIONS"""

        """
        Correlation threshold.  Used to verify the beam data is good to use.
        Anything below 0.25 correlation is consided bad data.
        """
        self.corr_thresh = 0.25

        """
        Pressure offset.  This value is used if a known pressure offset is needed.
        """
        self.pressure_offset = 0.0

        """
        Height source.
        0 = Range Tracking Beam 0
        1 = Range Tracking Beam 1
        2 = Range Tracking Beam 2
        3 = Range Tracking Beam 3
        4 = Vertical Beam Height (Avg Range Tracking or Pressure)
        5 = Pressure
        """
        self.height_source = 4

        self.height_source = height_source
        self.corr_thresh = corr_thresh
        self.pressure_offset = pressure_offset

        # Get the number of beams
        self.num_beams = 1
        if ens.IsEnsembleData:
            self.num_beams = ens.EnsembleData.NumBeams

        # Get the number of bins
        self.num_bins = len(selected_bins)

        self.time_stamp_seconds = self.calc_time_stamp_seconds(ens)

        if ens.IsEnsembleData:
            self.ensemble_number = ens.EnsembleData.EnsembleNumber
            self.ens_datetime = ens.EnsembleData.datetime()
            self.serial_number = ens.EnsembleData.SerialNumber
            self.ss_code = ens.EnsembleData.SysFirmwareSubsystemCode
            self.ss_config = ens.EnsembleData.SubsystemConfig

        if ens.IsAncillaryData:
            #self.pressure = ens.AncillaryData.Pressure + pressure_offset
            self.pressure = ens.AncillaryData.TransducerDepth + pressure_offset
            self.water_temp = ens.AncillaryData.WaterTemp
            self.heading = ens.AncillaryData.Heading
            self.pitch = ens.AncillaryData.Pitch
            self.roll = ens.AncillaryData.Roll
            self.blank = ens.AncillaryData.FirstBinRange
            self.bin_size = ens.AncillaryData.BinSize

        # Add the data based off the number of beams
        if self.num_beams == 1:
            self.is_vertical_ens = True
            self.add_vertical_beam(ens, selected_bins, corr_thresh)
        else:
            self.is_vertical_ens = False
            self.add_4_beam(ens, selected_bins, corr_thresh)

    def add_vertical_beam(self, ens, selected_bins, corr_thresh):
        """
        Add the data for a vertical beam system.
        This will populate all the data.  It will also screen the data to verify the wave
        height is correct.  It will compare the range tracking data to the pressure sensor.
        If the range tracking is far off, it will use the pressure sensor as a backup.
        :param ens: Ensemble to get the data.
        :param selected_bins: Bins selected.
        :param corr_thresh: Correlation threshold.
        """
        # Get the number of bins
        num_bins = len(selected_bins)

        if ens.IsRangeTracking:
            self.range_tracking = ens.RangeTracking.Range
            self.vert_beam_height = ens.RangeTracking.Range[0]
        else:
            self.vert_beam_height = -1.0

        # Create enough entries for all the bins or (bins x beams)
        # Initialize with bad values
        for bins in range(num_bins):

            # Vertical Beam velocity
            if ens.IsBeamVelocity and ens.IsCorrelation:
                # Check the correlation against the correlation threshold
                if ens.Correlation.Correlation[selected_bins[bins]][0] >= corr_thresh:
                    self.vert_beam_vel.append(ens.Wt.Velocities[selected_bins[bins]][0])
                else:
                    self.vert_beam_vel.append(Ensemble.BadVelocity)
            # No correlation data, so just use the beam velocity
            elif ens.IsBeamVelocity:
                self.vert_beam_vel.append(ens.Wt.Velocities[selected_bins[bins]][0])


        # Cleanup
        # Check Vertical beam height data (avg range)
        # and use pressure as backup
        if self.pressure != 0:
            if self.vert_beam_height > 1.2 * self.pressure or self.vert_beam_height < 0.8 * self.pressure:
                self.vert_beam_height = self.pressure

        # Check for slant height data
        # Check Range tracking and use pressure as backup
        if ens.IsRangeTracking:
            if ens.RangeTracking.Range[0] != -1 and self.pressure != 0:
                if self.range_tracking[0] > 1.2 * self.pressure or self.range_tracking[0] < 0.8 * self.pressure:
                    self.range_tracking[0] = self.pressure

        # Height source
        if self.height_source == 0 or self.height_source == 1 or self.height_source == 2 or self.height_source == 3 or self.height_source == 4:
            self.height = self.vert_beam_height
        elif self.height_source == 5:
            self.height = self.pressure

    def add_4_beam(self, ens, selected_bins, corr_thresh):
        """
        Add the data for a 4 beam system.  This will also work for a 3 beam system.
        This will populate all the data.  It will also screen the data to verify the wave
        height is correct.  It will compare the range tracking data to the pressure sensor.
        If the range tracking is far off, it will use the pressure sensor as a backup.
        :param ens: Ensemble to get the data.
        :param selected_bins: Bins selected.
        :param corr_thresh: Correlation threshold.
        """
        # Get the number of bins
        num_selected_bins = len(selected_bins)
        num_bins = ens.EnsembleData.NumBins

        # Get the number of beams
        num_beams = 1
        if ens.IsEnsembleData:
            num_beams = ens.EnsembleData.NumBeams

        # Create enough entries for all the bins or (bins x beams)
        # Initialize with bad values
        for selected_bin in selected_bins:
            # Verify a good bin was selected
            if selected_bin < num_bins:
                beam_data = []
                for beam in range(num_beams):
                    # Check Correlation to use Beam velocity
                    if ens.IsBeamVelocity and ens.IsCorrelation and selected_bin < len(ens.Correlation.Correlation) and beam < ens.Correlation.element_multiplier:
                        # Check the correlation against the correlation threshold
                        if ens.Correlation.Correlation[selected_bin][beam] >= corr_thresh:
                            beam_data.append(ens.Wt.Velocities[selected_bin][beam])
                        else:
                            beam_data.append(Ensemble.BadVelocity)
                    # No correlation data, so just use the beam velocity
                    elif ens.IsBeamVelocity:
                        beam_data.append(ens.Wt.Velocities[selected_bin][beam])

                # Add the data for each bin
                self.beam_vel.append(beam_data)

                # Earth Velocity
                if ens.IsEarthVelocity:
                    self.east_vel.append(ens.EarthVelocity.Velocities[selected_bin][0])
                    self.north_vel.append(ens.EarthVelocity.Velocities[selected_bin][1])
                    self.vertical_vel.append(ens.EarthVelocity.Velocities[selected_bin][2])

        # Range Tracking
        # Average the ranges
        avg_range_ct = 0
        avg_range = 0.0
        for beam in range(num_beams):
            if ens.IsRangeTracking:
                if ens.RangeTracking.Range[beam] > 0:
                    avg_range += ens.RangeTracking.Range[beam]
                    avg_range_ct += 1
                    self.range_tracking.append(ens.RangeTracking.Range[beam])
                else:
                    self.range_tracking.append(-1.0)
            # If Range Tracking data is not available, use Pressure data as a backup
            elif ens.IsAncillaryData and ens.AncillaryData.TransducerDepth > 0:
                avg_range += ens.AncillaryData.TransducerDepth
                avg_range_ct += 1
                self.range_tracking.append(ens.AncillaryData.TransducerDepth)
            else:
                self.range_tracking.append(-1.0)

        # Include the pressure in the average of the range tracking
        if self.pressure >= 0:
            avg_range += self.pressure
            avg_range_ct += 1

        # Set the average range and vertical beam height as the average of the range tracking and pressure
        #if ens.IsRangeTracking:
        if avg_range_ct > 0:
            self.avg_range_tracking = avg_range / avg_range_ct
            self.vert_beam_height = self.avg_range_tracking
        else:
            self.vert_beam_height = 0.0
            self.avg_range_tracking = 0.0

        # Cleanup
        # Check Vertical beam height data (avg range)
        # and use pressure as backup
        #if self.pressure != 0:
        #    if self.vert_beam_height > 1.2 * self.pressure or self.vert_beam_height < 0.8 * self.pressure:
        #        self.vert_beam_height = self.pressure

        # Check for slant height data
        # Check Range tracking and use pressure as backup
        #if ens.IsRangeTracking:
        #    if ens.RangeTracking.Range[0] != -1 and self.pressure != 0:
        #        for beam in range(num_beams):
        #            if self.range_tracking[beam] > 1.2 * self.pressure or self.range_tracking[beam] < 0.8 * self.pressure:
        #                self.range_tracking[beam] = self.pressure

        # Height Source
        if self.height_source == 0:
            if ens.IsRangeTracking:
                self.height = ens.RangeTracking.Range[0]
            else:
                self.height = -1.0
        elif self.height_source == 1:
            if ens.IsRangeTracking and num_beams > 1:
                self.height = ens.RangeTracking.Range[1]
            else:
                self.height = -1.0
        elif self.height_source == 2:
            if ens.IsRangeTracking and num_beams > 2:
                self.height = ens.RangeTracking.Range[2]
            else:
                self.height = -1.0
        elif self.height_source == 3:
            if ens.IsRangeTracking and num_beams > 3:
                self.height = ens.RangeTracking.Range[3]
            else:
                self.height = -1.0
        elif self.height_source == 4:
            self.height = self.vert_beam_height             # Avg of 4 Range Tracking
        elif self.height_source == 5:
            self.height = self.pressure

    @staticmethod
    def calc_time_stamp_seconds(ens):
        """
        Calcualte the timestamp.  This is the number of seconds for the given
        date and time.
        :param ens: Ensemble to get the timestamp.
        :return: Timestamp in seconds.
        """

        ts = 0.0

        if ens.IsEnsembleData:
            year = ens.EnsembleData.Year
            month = ens.EnsembleData.Month
            day = ens.EnsembleData.Day
            hour = ens.EnsembleData.Hour
            minute = ens.EnsembleData.Minute
            second = ens.EnsembleData.Second
            hsec = ens.EnsembleData.HSec
            jdn = WaveEnsemble.julian_day_number(year, month, day)

            ts = (24.0 * 3600.0 * jdn) + (3600.0 * hour) + (60.0 * minute) + second + (hsec / 100.0)

        return ts

    @staticmethod
    def julian_day_number(year, month, day):
        """
        Count the number of calendar days there are for the given
        year, month and day.
        :param year: Years.
        :param month: Months.
        :param day: Days.
        :return: Number of days.
        """
        a = (14 - month) / 12
        y = year + 4800 - a
        m = month - 12 * a - 3

        return day + (153 * m + 2) / 5 + (365 * y) + y / 4 - y / 100 + y / 400 - 32045


from collections import deque
import logging
from rti_python.Ensemble.Ensemble import Ensemble
from threading import Lock
import copy


class AverageWaterColumn:
    """
    Average the water column
    This will average the Beam, Instrument and Earth veocity.

    Screening of the data should be done before data is added to the
    accumulator.

    This uses deque instead of a list because it has better performance
    for popping the first element.
    """

    # Index for the results
    INDEX_SS_CODE = 0
    INDEX_SS_CONFIG = 1
    INDEX_NUM_BEAM = 2
    INDEX_NUM_BINS = 3
    INDEX_BEAM = 4
    INDEX_INSTRUMENT = 5
    INDEX_EARTH = 6
    INDEX_MAG = 7
    INDEX_DIR = 8
    INDEX_PRESSURE = 9
    INDEX_XDCR_DEPTH = 10
    INDEX_FIRST_TIME = 11
    INDEX_LAST_TIME = 12
    INDEX_RANGE_TRACK = 13
    INDEX_BLANK = 14
    INDEX_BIN_SIZE = 15
    INDEX_BT_RANGE = 16
    INDEX_IS_UPWARD = 17
    INDEX_FIRST_ENS_NUM = 18
    INDEX_LAST_ENS_NUM = 19

    def __init__(self, num_ens, ss_code, ss_config):

        # Store the parameters
        self.num_ens = num_ens
        self.ss_code = ss_code
        self.ss_config = ss_config

        # Create the list to hold the ensembles
        self.ens_beam_list = deque([], self.num_ens)
        self.ens_instr_list = deque([], self.num_ens)
        self.ens_earth_list = deque([], self.num_ens)
        self.ens_magnitude = deque([], self.num_ens)
        self.ens_direction = deque([], self.num_ens)
        self.pressure = deque([], self.num_ens)
        self.xdcr_depth = deque([], self.num_ens)
        self.range_track_list = deque([], self.num_ens)
        self.bottom_track_range_list = deque([], self.num_ens)
        self.blank = 0.0
        self.bin_size = 0.0
        self.num_beams = 0
        self.num_bins = 0
        self.first_time = None
        self.last_time = None
        self.first_ens_num = 0
        self.last_ens_num = 0
        self.is_upward = False

        self.thread_lock = Lock()

    def add_ens(self, ens):
        """
        Check if the ensemble has the same subsystem configuration and subsystem code.
        If they match, then accumulate the velocity data if it exist.

        :param ens: Ensemble to accumulate and average
        :return:
        """
        if ens.IsEnsembleData:
            # Check if the subsystem config and code match
            # Then add the velocity data to the list
            if ens.EnsembleData.SubsystemConfig == self.ss_config and ens.EnsembleData.SysFirmwareSubsystemCode == self.ss_code:
                if ens.IsEnsembleData:
                    self.num_beams = ens.EnsembleData.NumBeams
                    self.num_bins = ens.EnsembleData.NumBins
                if ens.IsAncillaryData:
                    self.blank = ens.AncillaryData.FirstBinRange
                    self.bin_size = ens.AncillaryData.BinSize
                    self.pressure.append([ens.AncillaryData.Pressure])
                    self.xdcr_depth.append([ens.AncillaryData.TransducerDepth])
                    self.is_upward = ens.AncillaryData.is_upward_facing()               # Set if upward or downward
                if ens.IsBeamVelocity:
                    self.ens_beam_list.append(ens.Wt.Velocities)
                if ens.IsInstrumentVelocity:
                    self.ens_instr_list.append(ens.InstrumentVelocity.Velocities)
                if ens.IsEarthVelocity:
                    self.ens_earth_list.append(ens.EarthVelocity.Velocities)
                    self.ens_magnitude.append(ens.EarthVelocity.Magnitude)
                    self.ens_direction.append(ens.EarthVelocity.Direction)
                if ens.IsRangeTracking:
                    self.range_track_list.append(ens.RangeTracking.Range)
                if ens.IsBottomTrack:
                    self.bottom_track_range_list.append(ens.BottomTrack.Range)

                # Set the times
                if not self.first_time:
                    self.first_time = ens.EnsembleData.datetime()
                    self.first_ens_num = ens.EnsembleData.EnsembleNumber

                # Always store the last time
                self.last_time = ens.EnsembleData.datetime()
                self.last_ens_num = ens.EnsembleData.EnsembleNumber

    def average(self, is_running_avg=False):
        """
        Average the accumulated data.

        If there were any errors averaging, NONE is returned for the average result.  It no
        data existed, NONE is also returned.  If data type does not exist, NONE is returned.

        Use the INDEX variables to access all the data in the returned object.

        :return: Averaged data [ss_code, ss_config, num_beams, num_bins, Beam, Instrument, Earth, Mag, Dir, Pressure, xdcr_depth, first_time, last_time, range_track]
        """

        # These values get reset before the data is returned
        # So store them here so they remain valid for the returned value
        first_time = self.first_time
        last_time = self.last_time
        num_bins = self.num_bins
        num_beams = self.num_beams
        first_ens_num = self.first_ens_num
        last_ens_num = self.last_ens_num

        # Average the Beam data
        avg_beam_results = self.avg_beam_data()

        # Average the Instrument data
        avg_instr_results = self.avg_instr_data()

        # Average the Earth data
        avg_earth_results = self.avg_earth_data()

        # Average the Magnitude data
        avg_mag_results = self.avg_mag_data()

        # Average the Direction data
        avg_dir_results = self.avg_dir_data()

        # Average the Pressure data
        avg_pressure_results = self.avg_pressure_data()

        # Average the Pressure data
        avg_xdcr_depth_results = self.avg_xdcr_depth_data()

        # Average the Range Tracking
        avg_range_track_results = self.avg_range_track_data()

        # Average the Range Tracking
        avg_bottom_track_range_results = self.avg_bottom_track_range_data()

        # Clear the lists
        if not is_running_avg:
            self.reset()

        return [self.ss_code,                   # Subsystem Code (str)
                self.ss_config,                 # Subsystem Config (str)
                num_beams,                      # Number of beams (int)
                num_bins,                       # Number of bins (int)
                avg_beam_results,               # Beam Vel Avg (list[bin][beam])
                avg_instr_results,              # Instrument Vel Avg (list[bin][beam])
                avg_earth_results,              # Earth Vel Avg (list[bin][beam])
                avg_mag_results,                # Mag Avg (list[bin])
                avg_dir_results,                # Dir Avg (list[bin])
                avg_pressure_results,           # Pressure Avg (list[single value]float)
                avg_xdcr_depth_results,         # Xdcr Depth Avg (list[single value]float)
                first_time,                     # First Time in Avg (dt)
                last_time,                      # Last Time in Avg (dt)
                avg_range_track_results,        # Range Track Avg (list[beam])
                self.blank,                     # Blanking distance used to calculate bin depth
                self.bin_size,                  # Bins size for the  use to calculate bin depth
                avg_bottom_track_range_results, # Average bottom track value
                self.is_upward,                 # Flag if upward or downward facing
                first_ens_num,                  # First Ensemble number in average
                last_ens_num]                   # Last Ensemble number in average

    def reset(self):
        """
        Clear all the list of data.
        Clear the times.
        This can also be used to start the averaging over.
        :return:
        """
        self.ens_beam_list.clear()
        self.ens_instr_list.clear()
        self.ens_earth_list.clear()
        self.ens_magnitude.clear()
        self.ens_direction.clear()
        self.pressure.clear()
        self.xdcr_depth.clear()
        self.range_track_list.clear()
        self.bottom_track_range_list.clear()
        self.first_time = None
        self.last_time = None
        self.num_bins = 0
        self.num_beams = 0
        self.first_ens_num = 0
        self.last_ens_num = 0

    def avg_beam_data(self):
        """
        Average the Beam velocity data
        :return: Average velocity for each [bin][beam]
        """
        try:
            return self.avg_vel(self.ens_beam_list)
        except Exception as e:
            logging.error("Error processing data to average Beam water column.  " + str(e))
            if self.thread_lock.locked():
                self.thread_lock.release()
            return None

    def avg_instr_data(self):
        """
        Average the Instrument velocity data
        :return: Average velocity for each [bin][beam]
        """
        try:
            return self.avg_vel(self.ens_instr_list)
        except Exception as e:
            logging.error("Error processing data to average Instrument water column. " + str(e))
            if self.thread_lock.locked():
                self.thread_lock.release()
            return None

    def avg_earth_data(self):
        """
        Average the Earth velocity data
        :return: Average velocity for each [bin][beam]
        """
        try:
            return self.avg_vel(self.ens_earth_list)
        except Exception as e:
            logging.error("Error processing data to average Earth water column. " + str(e))
            if self.thread_lock.locked():
                self.thread_lock.release()
            return None

    def avg_mag_data(self):
        """
        Average the water current magnitude data
        :return: Average magnitude for each [bin]
        """
        try:
            return self.avg_mag_dir(self.ens_magnitude)
        except Exception as e:
            logging.error("Error processing data to average Magnitude water column. " + str(e))
            if self.thread_lock.locked():
                self.thread_lock.release()
            return None

    def avg_dir_data(self):
        """
        Average the water current direction data
        :return: Average direction for each [bin]
        """
        try:
            return self.avg_mag_dir(self.ens_direction)
        except Exception as e:
            logging.error("Error processing data to average Direction water column. " + str(e))
            if self.thread_lock.locked():
                self.thread_lock.release()
            return None

    def avg_pressure_data(self):
        """
        Average the water pressure data
        :return: Average pressure. Single value in list
        """
        try:
            return self.avg_mag_dir(self.pressure)
        except Exception as e:
            logging.error("Error processing data to average Pressure. " + str(e))
            if self.thread_lock.locked():
                self.thread_lock.release()
            return None

    def avg_xdcr_depth_data(self):
        """
        Average the water Tranducer Depth data
        :return: Average Transducer depth. Single value in list
        """
        try:
            return self.avg_mag_dir(self.xdcr_depth)
        except Exception as e:
            logging.error("Error processing data to average Transducer Depth. " + str(e))
            if self.thread_lock.locked():
                self.thread_lock.release()
            return None

    def avg_range_track_data(self):
        """
        Average the Range Tracking data
        :return:  Average Range for each [beam]
        """
        try:
            return self.avg_range(self.range_track_list)
        except Exception as e:
            logging.error("Error processing data to average Range Tracking. " + str(e))
            if self.thread_lock.locked():
                self.thread_lock.release()
            return None

    def avg_bottom_track_range_data(self):
        """
        Average the Bottom Track Range data
        :return:  Average Bottom Track Range for each [beam]
        """
        try:
            return self.avg_range(self.bottom_track_range_list)
        except Exception as e:
            logging.error("Error processing data to average Bottom Track Range. " + str(e))
            if self.thread_lock.locked():
                self.thread_lock.release()
            return None

    def avg_vel(self, vel):
        """
        Average the velocity data given.
        This will verify the number of bins and beams
        is the same between ensembles.  If any ensembles have a different
        number of beams or bins, then a exception will be thrown.

        This will not average the data if the data is BAD VELOCITY.

        :param vel:  Velocity data from each ensemble.
        :return: Average of all the velocities in the all the ensembles.
        """
        # Determine number of bins and beams
        num_bins = 0
        num_beams = 0
        avg_accum = []
        avg_count = []
        avg_vel = None

        # lock the thread when iterating the deque
        #self.thread_lock.acquire(True, 1000)

        # Create a deep copy of the data
        # This will make it thread safe
        #deep_copy_vel = copy.deepcopy(vel)

        for ens_vel in vel:
            temp_num_bins = len(ens_vel)
            temp_num_beams = len(ens_vel[0])

            # Verify the bins and beams has not changed
            if num_beams == 0:
                num_beams = temp_num_beams
            elif num_beams != temp_num_beams:
                logging.error("Number of beams is not consistent between ensembles")
                self.thread_lock.release()
                raise Exception("Number of beams is not consistent between ensembles")

            if num_bins == 0:
                num_bins = temp_num_bins
            elif num_bins != temp_num_bins:
                logging.error("Number of bins is not consistent between ensembles")
                self.thread_lock.release()
                raise Exception("Number of bins is not consistent between ensembles")

            # Create the average lists
            if num_bins != 0 and num_beams != 0 and len(avg_accum) == 0:
                avg_accum = [[0 for ens_bin in range(num_beams)] for beams in range(num_bins)]
                avg_count = [[0 for ens_bin in range(num_beams)] for beams in range(num_bins)]
                avg_vel = [[0 for ens_bin in range(num_beams)] for beams in range(num_bins)]

            # Accumulate the data
            for ens_bin in range(len(ens_vel)):
                for beam in range(len(ens_vel[0])):
                    if not Ensemble.is_bad_velocity(ens_vel[ens_bin][beam]):
                        avg_accum[ens_bin][beam] += ens_vel[ens_bin][beam]      # Accumulate velocity
                        avg_count[ens_bin][beam] += 1                           # Count good data

        # Unlock thread
        #self.thread_lock.release()

        # Average the data accumulate
        for ens_bin in range(len(avg_accum)):
            for beam in range(len(avg_accum[0])):
                if avg_count[ens_bin][beam] > 0:                                # Verify data was accumulated
                    avg_vel[ens_bin][beam] = avg_accum[ens_bin][beam] / avg_count[ens_bin][beam]    # Average data

        return avg_vel

    def avg_mag_dir(self, data):
        """
        Average the magnitude or direction data given.
        This will verify the number of bins
        is the same between ensembles.  If any ensembles have a different
        number of bins, then a exception will be thrown.

        This will not average the data if the data is BAD VELOCITY.

        :param data:  Magnitude or direction data from each ensemble.
        :return: Average of all the velocities in the all the ensembles.
        """
        # Determine number of bins and beams
        num_bins = 0
        avg_accum = []
        avg_count = []
        avg_vel = None

        for ens_data in data:
            temp_num_bins = len(ens_data)
            if num_bins == 0:
                num_bins = temp_num_bins
            elif num_bins != temp_num_bins:
                logging.error("Number of bins is not consistent between ensembles")
                self.thread_lock.release()
                raise Exception("Number of bins is not consistent between ensembles")

            # Create the average lists
            if num_bins != 0 and len(avg_accum) == 0:
                avg_accum = [0 for b in range(num_bins)]
                avg_count = [0 for b in range(num_bins)]
                avg_vel = [0 for b in range(num_bins)]

            # Accumulate the data
            for ens_bin in range(len(ens_data)):
                if not Ensemble.is_bad_velocity(ens_data[ens_bin]):
                    avg_accum[ens_bin] += ens_data[ens_bin]           # Accumulate velocity
                    avg_count[ens_bin] += 1                           # Count good data

        # Average the data accumulate
        for ens_bin in range(len(avg_accum)):
            if avg_count[ens_bin] > 0:                                # Verify data was accumulated
                avg_vel[ens_bin] = avg_accum[ens_bin] / avg_count[ens_bin]    # Average data

        return avg_vel

    def avg_range(self, rt):
        """
        Average the Range Tracking data given.
        This will verify the number of beams
        is the same between ensembles.  If any ensembles have a different
        number of beams, then a exception will be thrown.

        This will not average the data if the data is BAD VELOCITY.

        :param rt:  Range Tracking data from each ensemble.
        :return: Average of all the Range Tracking in the all the ensembles.
        """
        # Determine number of beams
        num_beams = 0
        avg_accum = []
        avg_count = []
        avg_range = None

        for ens_range in rt:
            temp_num_beams = len(ens_range)

            # Verify the bins and beams has not changed
            if num_beams == 0:
                num_beams = temp_num_beams
            elif num_beams != temp_num_beams:
                logging.error("Number of beams is not consistent between ensembles")
                self.thread_lock.release()
                raise Exception("Number of beams is not consistent between ensembles")

            # Create the average lists
            if num_beams != 0 and len(avg_accum) == 0:
                avg_accum = [0 for beam in range(num_beams)]
                avg_count = [0 for beam in range(num_beams)]
                avg_range = [0 for beam in range(num_beams)]

            # Accumulate the data
            for beam in range(len(ens_range)):
                if not Ensemble.is_bad_velocity(ens_range[beam]):
                    avg_accum[beam] += ens_range[beam]      # Accumulate range
                    avg_count[beam] += 1                    # Count good data

        # Average the data accumulate
        for beam in range(len(avg_accum)):
                if avg_count[beam] > 0:                                 # Verify data was accumulated
                    avg_range[beam] = avg_accum[beam] / avg_count[beam] # Average data

        return avg_range

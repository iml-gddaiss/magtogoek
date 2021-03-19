from enum import Enum


class AdcpCmd:
    """
    ADCP Command.
    """

    def __init__(self, cmd, value):
        self.cmd = cmd
        self.value = value

    def to_str(self, index):
        """
        Convert the command to a command string.
        Convert the index to a hex then remove the 0x from the value.
        :param index: CEPO index.
        :return: String with the index.
        """
        return self.cmd + '[' + hex(index)[2:] + "] " + self.value


def get_tooltip(desc_array):
    return '\n'.join([str(x) for x in desc_array])


def sec_to_hmss(sec):
    """
    Convert the seconds to a string of hh:mm:ss.ss
    :param sec: Seconds.
    :return: hh:mm:ss.ss
    """
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    hs_f = sec - int(sec)
    hs = round(hs_f * 100, 2)

    hour = str(int(h)).zfill(2)
    minute = str(int(m)).zfill(2)
    sec = str(int(s)).zfill(2)
    hsec = str(int(hs)).zfill(2)

    return hour + ":" + minute + ":" + sec + "." + hsec


def pretty_print_sec(sec):
    """
    Pretty print the seconds to days, hours, minutes, seconds and milliseconds.
    :param sec: Seconds in time.
    :return: Days, hours, minutes, seconds and milliseconds.
    """

    seconds = abs(int(sec))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    hs_f = sec - int(sec)
    hs = round(hs_f * 100, 2)
    ms = int(hs * 10)

    result = ""

    if days > 0:
        result += str(days) + " day"
        if days > 1:
            result += "s "
        else:
            result += " "
    if hours > 0:
        result += str(hours) + " hour"
        if hours > 1:
            result += "s "
        else:
            result += " "
    if minutes > 0:
        result += str(minutes) + " minute"
        if minutes > 1:
            result += "s "
        else:
            result += " "
    if seconds > 0:
        result += str(seconds) + " second"
        if seconds > 1:
            result += "s "
        else:
            result += " "
    if ms > 0:
        result += str(ms) + " millisecond"
        if ms > 1:
            result + "s"

    return result


def pretty_print_m(length):
    """
    Print the distance scaled.
    :param length: Length in meters.
    :return: String of the distanced scaled.
    """
    if length < 1.0:
        return str(round((length*100), 2)) + " cm"

    if length >= 1000:
        return str(round((length/1000), 2)) + " km"

    return str(round(length, 2)) + " m"


def pretty_print_m_per_sec(length):
    """
    Print the speed scaled.
    :param length: Length in meters.
    :return: String of the distanced scaled.
    """
    if length < 1.0:
        return str(round((length*100), 2)) + " cm/s"

    if length >= 1000:
        return str(round(length/1000), 2) + " km/s"

    return str(round(length, 2)) + " m/s"


def pretty_print_burst(cei, burst_interval, num_ens, cwpp, cwptbp):
    """
    Measure XXX ensembles in XXX days XXX hours XXX minutes XXX seconds XXX milliseconds.
    XXX minutes between each ensemble.
    Average XXX pings over XXX minutes.
    Burst length is XXX hours.
    BURST MEASUREMENT WILL TAKE LONGER THAN BURST LENGTH
    :param cei:
    :param burst_interval:
    :param num_ens:
    :return:
    """
    burst_interval_str = pretty_print_sec(burst_interval)
    cei_str = pretty_print_sec(cei)
    burst_measure = num_ens * cei
    avg_time = cwpp * cwptbp
    avg_time_str = pretty_print_sec(avg_time)
    if cwpp > 1:
        burst_measure = (num_ens * (cwpp * cwptbp)) * cei
    burst_measure_str = pretty_print_sec(burst_measure)

    result = ""
    error_msg = ""
    result += "-Measuring " + str(num_ens) + " ensembles in " + burst_measure_str + "\n"
    result += "-Output an ensemble every " + cei_str + "\n"
    if cwpp > 1:
        result += "-An ensemble averages " + str(cwpp) + " pings over " + avg_time_str + "\n"

        if avg_time > cei:
            error_msg += "*AVERAGING WILL TAKE LONGER THAN CEI\n"

    result += "-Take a burst measurement every " + burst_interval_str + "\n"

    if burst_measure > burst_interval:
        error_msg += "*BURST MEASUREMENT WILL TAKE LONGER THAN BURST LENGTH!\n"

    return result, error_msg


def pretty_print_standard(cei, cwpp, cwptbp):
    """
    Using the values, print out the pinging strategy.
    XXX seconds between each ensemble
    Average XXX pings over XXX minutes
    AVERAGING WILL TAKE LONGER THAN CEI
    :param cei: Time between ensembles.
    :param cwpp: Number of pings to average.
    :param cwptbp: Time between pings.
    :return: String describing the pinging.
    """

    cei_str = pretty_print_sec(cei)
    avg_time = cwpp * cwptbp
    avg_time_str = pretty_print_sec(avg_time)

    result = ""
    error_msg = ""
    result += "-Output an ensemble every " + cei_str + "\n"

    if cwpp > 1:
        result += "-An ensemble averages " + str(cwpp) + " pings over " + avg_time_str + "\n"

    if avg_time > cei:
        error_msg += "*AVERAGING WILL TAKE LONGER THAN CEI\n"

    return result, error_msg


def pretty_print_accuracy(max_vel, std):
    """
    Print out the max velocity and accuracy of the measurement.
    -The boat and water speed cannot exceed XXXm/s or XXXknots
    -The accuracy of the measurement is +/- XXXcm/s
    :param max_vel: Maximum Velocity in m/s.
    :param std: Standard Deviation in m/s.
    :return: String describing the max vel and accuracy.
    """
    max_vel_knots = max_vel * 1.94384
    max_vel_mph = max_vel * 2.23694
    #std_cm_s = std * 100
    max_vel_str = str(round(max_vel, 2))
    max_vel_knots_str = str(round(max_vel_knots, 2))
    max_vel_mph_str = str(round(max_vel_mph, 2))
    std_cm_str = pretty_print_m_per_sec(std)

    result = ""
    error_msg = ""
    result += "-The boat and water speed combined cannot exceed " + max_vel_str + " m/s or " + max_vel_knots_str + " knots or " + max_vel_mph_str + " mph\n"
    result += "-The accuracy of the measurement is +/- " + std_cm_str + "\n"

    if max_vel < 2.8:
        error_msg += "*If you are collecting data with a boat, you may want to adjust your settings to increase the maximum velocity to exceed 2.8 m/s.\n"

    return result, error_msg


def pretty_print_cfg_depth(blank, bin_size, num_bin, calc_first_bin):
    """
    Print the configured Water Profile depth of the ADCP and the first bin position.
    The first measurement will begin XXX m below the ADCP.
    It is configured to Water Profile to a depth of XXX m.
    :param blank: Blank setting in meters (CWPBL).
    :param bin_size: Bin size in meters (CWPBS).
    :param num_bin: Number of bins (CWPBN).
    :param calc_first_bin: Calculated first bin position in meters.
    :return: Configured water profile range and first bin position.
    """

    result = ""

    cfg_range = blank + (bin_size * num_bin)
    range_str = pretty_print_m(cfg_range)
    first_bin_str = pretty_print_m(calc_first_bin)

    result += "-The first measurement will begin " + first_bin_str + " below the ADCP.\n"
    result += "-Measure the Water Profile to a depth of " + range_str + ".\n"

    return result


class eCWPBB_TransmitPulseType(Enum):
    """
    Enum used to select the different transmit pulse types.
    """

    """
    (0) Non-Coded Narrowband.
     Provides long range profiles at the expense of variance.
     Not recommended for use with bin size less than the default
     bin size.

     Long Range but noisy data.  Usually take multiple pings and average
     them together.

     |---------------------------------|~
     |       o  o             o o      |  ~
     |     o      o          o    o    |    ~
     |   o           o     o        o  |      ~
     | o               o o            o|        ~
                Pulse Transmit             Receive Signal
               100% Carrier Cycle            Amplitude
     |-------------Bin Size------------|
     |-----------Transmit Length-------|
    """
    NARROWBAND = 0

    """
    /// (1) Coded Broadband.
    /// Typically 15% less range than narrow band but has greatly reduced
    /// variance (depending on lag length).
    /// Used in conjunction with CWPBP for small bins.
    /// 
    /// Shorter Range but clean data.
    /// 
    /// Broaband signal is a signal with modulation(phase changes).
    /// 
    /// |--|               |--|~
    /// |  |               |  |  ~
    /// |  |               |  |    ~     
    /// |  |               |  |      ~      ~    ~
    /// |  |_______________|  |        ~~~~~  ~~~  ~~
    /// 
    /// |----Lag Length----|
    /// 
    /// Lag Length or bin size, which ever is greater.
    /// 
    /// |---------------------------------------------------------| 
    /// |       o  o             o o         o o          o o     |
    /// |     o      o          o    o      o    o       o    o   |
    /// |   o           o     o        o   o       o    o       o |
    /// | o               o o            o           o o         o| 
    ///                                  |
    ///                             Phase Change
    /// |-----------------------Coded Element---------------------|
    /// 
    ///                        2 Carrier cycles
    ///                           BandWidth = 50%   
    ///                     BandWidth = 1 / # carrier cycles
    ///                        
    /// NB BandWidth: # carrier cycles in the pulse.
    /// BB BandWidth: # carrier cycles within a coded element.
    /// 
    /// 
    /// But with just 2 pulses it is not a lot of energy in the water.  Which limits the 
    /// profile range.  So more coded elements are put in the water to fill the gap between
    /// the lag length.  The group of coded elements for the first pulse are then repeated 
    /// a second time for the second pulse.  
    /// 
    /// 
    /// ||--||--|--|--|--||--||--|--|--|--|~
    /// ||  ||  |  |  |  ||  ||  |  |  |  |  ~
    /// || 0|| 1| 1| 0| 1|| 0|| 1| 1| 0| 1|    ~     
    /// ||  ||  |  |  |  ||  ||  |  |  |  |      ~      ~    ~
    /// ||  ||  |  |  |  ||  ||  |  |  |  |      ~~~~~  ~~~  ~~
    /// |-- Lag Length --|     
    /// 
    /// Wait for both groups of coded elements are sent out before looking at the receive data.  Then check the correlation between the 2 coded element groups.
    /// 
    /// Coded element groups are created with a pseudo random generator.
    /// BT uses M Sequence to generate the random code.  Bottom Track has a hard target so correlation is 100%. M Sequence good with 100% correlation.
    /// WP uses Barker Code to generate the random code.  Water Profile pulses interfere with each other so correlation is 50%.  So Barker Code is better to use.
    /// 
    /// Broadband             o 
    ///                     o   o
    ///                    o     o
    ///                   o       o
    ///                  o         o
    ///                 o           o
    ///        o o     o             o     o o
    ///  o o  o   o   o               o   o   o   o o
    /// o   o      o o                 o o     o o    o
    /// 
    /// Narrowband            o
    ///                      o o
    ///                     o   o
    ///                 o  o     o  o 
    ///                o oo       oo o
    /// 
    /// |------------------Frequency -----------------|
    /// 
    """
    BROADBAND = 1

    """
    /// (2) Non-Coded Pulse-To-Pulse.
    /// Narrowband and provides ultra low variance for small bin sizes.
    /// Non-coded has slightly higher variance than the coded
    /// transmit without the annoying autocorrelation side peaks.
    /// 
    /// Shallow water where blank can effect the measurement.  Measurements
    /// that need to be close to the instrument.  
    /// 
    /// Non-coded elements will work better because coded elements in small bins cause variance.
    /// 
    /// Normal processing will send out at least 2 pulses before processing the
    /// return information.  In shallower water, the return of the shallow depths would
    /// be lost.  In Pulse-to-Pulse, the First pulse is sent and then immediately listened
    /// to so it can see the shallower depths.  It then send out another pulse and the listens
    /// immediately.  The to pulses should have the same return to get good correlation (100%).
    /// But if the water is moving to fast, the pulses will not match and the correlation will
    /// be low.  
    /// 
    /// By processing earlier we can also have a smaller blank.  
    /// 
    /// One drawback is you can only receive data for the length of the lag.  After the lag, the
    /// next pulse will be sent out.  This limits the profile range.
    /// 
    /// PtoP 1st Bin Pos = Blank + (Xmt + BinSize)/2
    /// BB   1st Bin Pos = Blank + (Xmt + BinSize + Lag)/2
    /// 
    /// Xmt is the pulse.
    /// The lag is the length(time) needed to wait for both pulses to transmitted.
    /// 
    /// All the data (bins) processed within the lag length should have a 100%
    /// correlation.  Anything beyond the lag length will also include the second pulse
    /// and cause the correlation to drop to at least 50%.  The bins can still be seen but
    /// the data will not be as reliable.
    /// 
    /// |----|~         |----|~
    /// |    |  ~       |    |  ~
    /// |    |    ~     |    |    ~ 
    /// |    |      ~   |    |      ~
    /// |    |        ~ |    |        ~
    /// Pulse 1        Pulse 2
    ///      |BIN|.|BIN|......|BIN|
    ///      |-  100% -||-  50%  -|
    ///          Correlation
    /// 
    /// For Non-Coded PtoP, within the Pulse is a signal at the bandwidth.
    /// For BB PtoP, within the Pulse is a coded element (signal with modulation(phase changes)).
    /// 
    """
    NONCODED_PULSE_TO_PULSE = 2

    """
    /// (3) Broadband Pulse-To-Pulse. (no ambuguity resolver).
    /// Provides ultra low variance for small bin sizes.  Coded 
    /// has slightly lower variance than the non-coded transmit.
    /// 
    /// Shallow water where blank can effect the measurement.  Measurements
    /// that need to be close to the instrument.
    /// 
    /// Coded elements in small bins cause variance due to side peaks so not as good for really small bins sizes.
    /// 
    """
    BROADBAND_PULSE_TO_PULSE = 3

    """
    /// (4) Non Coded Broadband Pulse-To-Pulse. (no ambuguity resolver).
    /// Narrowband and provides ultra low variance for small bin sizes.  Coded 
    /// has slightly lower variance than the non-coded transmit.
    """
    NONCODED_BROADBAND_PULSE_TO_PULSE = 4

    """
    /// Broadband with ambuguity resolver ping.
    /// Used in conjunction with CWPBP.
    /// 
    /// Make lower variance measurements at a higher velocity.
    /// 
    /// Ambiguity Resolver is not perfect.
    /// 
    ///     / \         / \        */ \         / \
    ///    /  \       /   \       /   \       /   \
    ///   /   \    0/     \     /     \     /     \
    ///  /    \   /       \   /       \   /       \
    /// /     \ /         \/         \ /         \
    ///        |          |
    ///      -0.21m/s   0.21m/s 
    ///        | 1 Cycle  | 
    /// 
    /// 
    /// 
    /// Figure out how many times it went around the cycle.
    /// 
    /// * = 0.21(at least 1 cycle) + 0.18(mostly towards the top) = 0.39m/s
    /// 
    """
    BROADBAND_AMBIGUITY_RESOLVER = 5

    """
    /// Broadband pulse to pulse with ambiguity resolver ping.
    /// Used in conjunction with CWPAP.
    """
    BROADBAND_P2P_AMBIGUITY_RESOLVER = 6


class eCBTBB_Mode(Enum):
    """
    Bottom Track Mode.
    """

    """
    (0) Narrowband Long Range
    """
    NARROWBAND_LONG_RANGE = 0

    """
    (1) Coded Broadband Transmit.
    """
    BROADBAND_CODED = 1

    """
    (2) Broadband Non-coded Transmit.
    """
    BROADBAND_NON_CODED = 2

    """
    (3) NA.
    """
    NA_3 = 3

    """
    (4) Broadband Non-coded Pulse to Pulse
    """
    BROADBAND_NON_CODED_P2P = 4

    """
    (5) NA.
    """
    NA_5 = 5

    """
    (6) NA.
    """
    NA_6 = 6

    """
    (7) Auto switch between Narrowband, Broadband Non-Coded and Broadband Non-Coded Pulse to Pulse.
    """
    AUTO_SWITCH_NARROWBAND_BB_NONCODED_BB_NONCODED_P2P = 7


from mttkinter import mtTkinter
from tkinter import filedialog
from rti_python.Utilities.read_binary_file import ReadBinaryFile
from tqdm import tqdm
from obsub import event
from typing import List, Set, Dict, Tuple, Optional
import logging
from rti_python.Ensemble.Ensemble import Ensemble


class RtiCheckFile:
    """
    Check for any issues in binary ensemble file.
    """

    def __init__(self):
        self.ens_count = 0
        self.bad_ens = 0
        self.primary_beam_ens_count = 0
        self.vert_beam_ens_count = 0
        self.ens_pairs_count = 0
        self.found_issues = 0
        self.found_issue_str = ""
        self.prev_ens = None
        self.prev_ens_num = 0
        self.is_missing_ens = False
        self.is_status_issue = False
        self.is_voltage_issue = False
        self.is_amplitude_0db_issue = False
        self.is_correlation_100pct_issue = False
        self.is_datetime_jump_issue = False
        self.is_tilt_issue = False
        self.file_paths = ""
        self.pbar = None
        self.show_progress_bar = True
        self.first_ens = None
        self.last_ens = None
        self.show_live_errors = False
        self.bad_status_count = 0
        self.missing_ens_count = 0
        self.bad_voltage_count = 0
        self.bad_amp_0db_count = 0
        self.bad_corr_100pct_count = 0
        self.datetime_jump_count = 0
        self.ens_delta_time = 0
        self.ens_bad_delta_time = 0
        self.tilt_issue = 0
        self.prev_ens_datetime = None
        self.is_prev_ens_vertical = False
        self.is_upward = False
        self.ping_avgs = {}
        self.error_output_str = []
        self.summary_str = []

    def init(self):
        """
        Initialize the value for the next file.
        :return:
        """
        self.prev_ens_num = 0
        #self.is_missing_ens = False
        #self.is_status_issue = False
        self.file_paths = ""
        self.pbar = None
        self.first_ens = None
        self.last_ens = None

    def select_and_process(self, show_live_error=False):
        """
        Create a dialog box to select the files.
        Then process the files.
        :param show_live_error: TRUE = Show the errors as they are found.
        :return: Return the list of all the files processed.
        """

        files = self.select_files()
        self.process(files, show_live_error)

        return files

    def select_files(self):
        """
        Display a dialog box to select the files.
        :return: List of all the files selected.
        """
        # Dialog to ask for a file to select
        root = mtTkinter.Tk()
        root.overrideredirect(True)         # Used to Bring window to front and focused
        root.geometry('0x0+0+0')            # Used to Bring window to front and focused
        root.focus_force()                  # Used to Bring window to front and focused
        filetypes = [("DB files", "*.db"), ("ENS Files", "*.ens"), ("BIN Files", "*.bin"), ('All Files', '*.*')]
        self.file_paths = filedialog.askopenfilenames(parent=root, title="Select Binary Files to Playback", filetypes=filetypes)
        root.withdraw()

        return self.file_paths

    def process(self, file_paths: List, show_live_error: bool = False, show_progress_bar: bool = True):
        """
        Read the files and look for any issues in the files.
        :param file_paths: Path to file to process.
        :param show_live_error: TRUE = Show the errors as they are found.
        :param show_progress_bar: TRUE = Show the progress bar in the text console.
        :return: Summary containing a list of all the output.
        """
        self.file_paths = file_paths
        self.show_live_errors = show_live_error
        self.show_progress_bar = show_progress_bar

        if self.file_paths:
            for file in self.file_paths:
                reader = ReadBinaryFile()
                reader.ensemble_event += self.ens_handler               # Wait for ensembles
                reader.file_progress += self.file_progress_handler      # Monitor file progress
                self.init()                                             # Reinitialize values for next file
                reader.playback(file)                                   # Read the file for ensembles

                # Print the summary at the end
                self.print_summary(file)

                # Close the progress bar
                if self.show_progress_bar:
                    self.pbar.close()

    def get_summary(self):
        """
        Get the summary of the file check.
        :return: Dictionary containing lists of strings in "summary" and "errors".
        """
        # Remove any blank entries
        self.error_output_str = list(filter(None, self.error_output_str))
        self.summary_str = list(filter(None, self.summary_str))

        return { "summary": self.summary_str, "errors": self.error_output_str }

    def print_summary(self, file_path: str):
        """
        Print a summary of the results.
        :param file_path: File path for the file processed.
        :return:
        """
        self.summary_str.append("---------------------------------------------")
        self.summary_str.append("---------------------------------------------")

        # Check results for any fails
        if self.is_missing_ens or \
                self.is_status_issue or \
                self.is_voltage_issue or \
                self.is_amplitude_0db_issue or \
                self.is_correlation_100pct_issue or \
                self.is_datetime_jump_issue or \
                self.is_tilt_issue:
            self.summary_str.append("*********************************************")
            self.summary_str.append(str(self.found_issues) + " ISSUES FOUND WITH FILES")
            self.summary_str.append("Total Bad Status: " + str(self.bad_status_count))
            self.summary_str.append("Total Missing Ensembles: " + str(self.missing_ens_count))
            self.summary_str.append("Total Bad Voltage: " + str(self.bad_voltage_count))
            self.summary_str.append("Total Bad Amplitude (0dB): " + str(self.bad_amp_0db_count))
            self.summary_str.append("Total Bad Correlation (100%): " + str(self.bad_corr_100pct_count))
            self.summary_str.append("Total Extreme Tilt: " + str(self.tilt_issue))
            self.summary_str.append("Total Date/Time Jump (" + str(self.ens_delta_time) + "): " + str(self.datetime_jump_count))
            self.summary_str.append("*********************************************")
        else:
            if not self.prev_ens_num == 0:
                self.summary_str.append("File " + file_path + " checked and is all GOOD.")
            else:
                self.summary_str.append("No RTB Ensembles Found in: " + self.file_paths)

        # Upward or Downward Looking
        if self.is_upward:
            self.summary_str.append("ADCP is Upward Looking")
        else:
            self.summary_str.append("ADCP is Downward Looking")

        # Print info on first and last ensembles
        if self.first_ens and self.first_ens.IsEnsembleData:
            first_ens_dt = self.first_ens.EnsembleData.datetime_str()
            first_ens_num = self.first_ens.EnsembleData.EnsembleNumber
            self.summary_str.append("First ENS:\t[" + str(first_ens_num) + "] " + first_ens_dt)

        if self.last_ens and self.last_ens.IsEnsembleData:
            last_ens_dt = self.last_ens.EnsembleData.datetime_str()
            last_ens_num = self.last_ens.EnsembleData.EnsembleNumber
            self.summary_str.append("Last ENS:\t[" + str(last_ens_num) + "] " + last_ens_dt)

        self.summary_str.append(("Ensemble Time Delta: " + str(self.ens_delta_time)))

        # Print total number of ensembles in the file
        self.summary_str.append("Total number of bad ensembles in file: " + str(self.bad_ens))
        self.summary_str.append("Total number of ensembles in file:     " + str(self.ens_count))
        self.summary_str.append("Total number of Primary Beam ensembles in file:     " + str(self.primary_beam_ens_count))
        self.summary_str.append("Total number of Vertical Beam ensembles in file:     " + str(self.vert_beam_ens_count))
        self.summary_str.append("Total number of Ensemble Pairs in file:     " + str(self.ens_pairs_count))

        # Set the ping counts
        for ping_ct in self.ping_avgs.keys():
            self.summary_str.append("Average Ensemble Count: " + str(ping_ct) + " pings [" + str(self.ping_avgs[ping_ct]) + "]")

        if self.ens_count > 0:
            self.summary_str.append("Percentage of ensembles found bad:    " + str(round((self.bad_ens / self.ens_count) * 100.0, 3)) + "%")

        self.summary_str.append("---------------------------------------------")
        self.summary_str.append("---------------------------------------------")

        # Print the summary
        for line in self.summary_str:
            print(line)

        return self.summary_str

    def file_progress_handler(self, sender, bytes_read: int, total_size: int, file_name: str):
        """
        Monitor the file playback progress.
        :param sender: NOT USED
        :param total_size: Total size.
        :param bytes_read: Total Bytes read.
        :param file_name: File name being read..
        :return:
        """
        # Create the progress bar
        if self.pbar is None and self.show_progress_bar:
            self.pbar = tqdm(total=total_size)

        # Update the progress bar
        if self.show_progress_bar:
            self.pbar.update(int(bytes_read))

        # Pass the event to others
        self.file_progress_event(bytes_read, total_size, file_name)

    def ens_handler(self, sender, ens: Ensemble):
        """
        Process the ensemble data.  Check for any issues.
        :param sender: NOT USED.
        :param ens: Ensemble data
        :return:
        """

        # Set first and last ensemble
        if not self.first_ens:
            self.first_ens = ens
        self.last_ens = ens

        # Checking missing Ensemble
        is_missing_ens, prev_ens, err_str = RtiCheckFile.check_missing_ens(ens, self.prev_ens_num, self.show_live_errors)
        self.error_output_str.append(err_str)     # Keep track of all the errors
        self.prev_ens_num = prev_ens        # Log previous ens
        if is_missing_ens:
            self.is_missing_ens = True
            self.found_issues += 1
            self.found_issue_str += err_str + "\n"
            self.missing_ens_count += 1

        # Check ensemble status
        is_status_issue, err_str = self.check_status(ens, self.show_live_errors)
        self.error_output_str.append(err_str)  # Keep track of all the errors
        if is_status_issue:
            self.is_status_issue = True
            self.found_issues += 1
            self.found_issue_str += err_str + "\n"
            self.bad_status_count += 1

        # Check if voltage is bad
        is_voltage_issue, err_str = self.check_voltage(ens, self.show_live_errors)
        self.error_output_str.append(err_str)  # Keep track of all the errors
        if is_voltage_issue:
            self.is_voltage_issue = True
            self.found_issues += 1
            self.found_issue_str += err_str + "\n"
            self.bad_voltage_count += 1

        # Check if amplitude is bad
        is_amplitude_0db_issue, err_str = self.check_amplitude_0db(ens, self.show_live_errors)
        self.error_output_str.append(err_str)  # Keep track of all the errors
        if is_amplitude_0db_issue:
            self.is_amplitude_0db_issue = True
            self.found_issues += 1
            self.found_issue_str += err_str + "\n"
            self.bad_amp_0db_count += 1

        # Check correlation is bad
        is_correlation_100pct_issue, err_str = self.check_correlation_1pct(ens, self.show_live_errors)
        self.error_output_str.append(err_str)  # Keep track of all the errors
        if is_correlation_100pct_issue:
            self.is_correlation_100pct_issue = True
            self.found_issues += 1
            self.found_issue_str += err_str + "\n"
            self.bad_corr_100pct_count += 1

        # Check for datetime jump
        is_datetime_jump_issue, err_str, self.prev_ens_datetime, self.ens_delta_time = self.check_datetime_jump(ens,
                                                                                                                self.show_live_errors,
                                                                                                                self.prev_ens_datetime,
                                                                                                                self.ens_delta_time )
        self.error_output_str.append(err_str)  # Keep track of all the errors
        if is_datetime_jump_issue:
            self.is_datetime_jump_issue = True
            self.found_issues += 1
            self.found_issue_str += err_str + "\n"
            self.datetime_jump_count += 1

        # Check correlation is bad
        is_tilt_issue, err_str = self.check_tilt_extreme(ens, self.show_live_errors)
        self.error_output_str.append(err_str)  # Keep track of all the errors
        if is_tilt_issue:
            self.is_tilt_issue = True
            self.found_issues += 1
            self.found_issue_str += err_str + "\n"
            self.tilt_issue += 1

        # Check if upward looking
        if ens.IsAncillaryData:
            self.is_upward = ens.AncillaryData.is_upward_facing()

        # Count Ensembles and type of ensembles
        self.count_ens_types(ens)

        # Count Bad ensembles
        if is_missing_ens or is_status_issue or is_amplitude_0db_issue or is_correlation_100pct_issue or is_datetime_jump_issue or is_voltage_issue or is_tilt_issue:
            self.bad_ens += 1

        # Send ensemble to event to let other objects process the data
        self.ensemble_event(ens)

    def count_ens_types(self, ens: Ensemble):
        """
        Count the type of ensembles we have received.
        :param ens: Latest Ensemble.
        :type ens: Ensemble
        """
        # Count the number of ensembles
        self.ens_count += 1

        # Count how many vertical and 3 or 4 beam ensembles we have received
        if ens.EnsembleData.NumBeams == 1:
            self.vert_beam_ens_count += 1
        elif ens.EnsembleData.NumBeams >= 3:
            self.primary_beam_ens_count += 1

        # Check if we have 4 Beam and Vertical Beam pairs
        if self.prev_ens and self.prev_ens.EnsembleData.NumBeams >= 3 and ens.EnsembleData.NumBeams == 1:
            self.ens_pairs_count += 1

        # Count the ensemble ping numbers
        ping_count = ens.EnsembleData.ActualPingCount
        if ping_count in self.ping_avgs.keys():
            self.ping_avgs[ping_count] = self.ping_avgs[ping_count] + 1
        else:
            self.ping_avgs[ping_count] = 1

        # Store the ensemble to check next pass
        self.prev_ens = ens

    @event
    def ensemble_event(self, ens: Ensemble):
        """
        Event to subscribe to receive decoded ensembles.
        :param ens: Ensemble object.
        :return:
        """
        if ens.IsEnsembleData:
            logging.debug(str(ens.EnsembleData.EnsembleNumber))

    @event
    def file_progress_event(self, bytes_read: int, total_size: int, file_name: str):
        """
        Event to monitor the file progress.  This is passed through from the
        file playback.
        :param bytes_read: Bytes read.
        :type bytes_read: integer
        :param total_size: Total bytes to read.
        :type total_size: integer
        :param file_name: File name being read currently.
        :type file_name: string
        :return:
        :rtype:
        """
        logging.debug(file_name + " Bytes read: " + str(bytes_read) + " of " + str(total_size))

    @staticmethod
    def check_status(ens: Ensemble, show_live_errors: bool = False):
        """
        Check the status for any errors.
        :param ens: Ensemble data.
        :param show_live_errors: Show the errors occurring as file is read in or wait until entire file complete
        :return: True = Found an issue
        """
        err_str = ""
        found_issue = False

        if ens.IsEnsembleData:
            if not ens.EnsembleData.Status == 0:
                err_str = "Error in ensemble: " + str(ens.EnsembleData.EnsembleNumber) + "\tStatus: [" + str(hex(ens.EnsembleData.Status)) + "]: " + ens.EnsembleData.status_str()

                # Display the error if turned on
                if show_live_errors:
                    print(err_str)

                # Record the error
                found_issue = True

        return found_issue, err_str

    @staticmethod
    def check_missing_ens(ens, prev_ens_num, show_live_errors=False):
        """
        Check if the ensemble numbers are not in order.
        :param ens: Ensemble
        :param prev_ens_num: Previous ensemble number to compare against
        :param show_live_errors: Show the errors occurring as file is read in or wait until entire file complete
        :return: TRUE = Found an Issue
        """
        found_issue = False
        err_str = ""

        if ens.IsEnsembleData:
            if not prev_ens_num == 0:
                if not ens.EnsembleData.EnsembleNumber == (prev_ens_num + 1):
                    err_str = "Missing Ensemble: " + str(prev_ens_num + 1)

                    # Display the error if turned on
                    if show_live_errors:
                        print(err_str)

                    # Record the error
                    found_issue = True

            # Keep track of the previous ensemble number
            prev_ens_num = ens.EnsembleData.EnsembleNumber

        return found_issue, prev_ens_num, err_str

    @staticmethod
    def check_voltage(ens, show_live_errors):
        """
        Check if the voltage is above 36 volts or below 12v.
        The ADCP cannot handle these voltages.
        :param ens: Ensemble data.
        :param show_live_errors: Show the errors occurring as file is read in or wait until entire file complete
        :return: True = Found an issue
        """
        err_str = ""
        found_issue = False

        if ens.IsEnsembleData and ens.IsSystemSetup:
            if ens.SystemSetup.Voltage > 38 or ens.SystemSetup.Voltage < 12:
                err_str = "Error in ensemble: " + str(ens.EnsembleData.EnsembleNumber) + "\tVoltage: [" + str(ens.SystemSetup.Voltage) + "]"

                # Display the error if turned on
                if show_live_errors:
                    print(err_str)

                # Record the error
                found_issue = True

        return found_issue, err_str

    @staticmethod
    def check_datetime_jump(ens, show_live_errors, prev_ens_dt, ens_delta_time=0):
        """
        Check if the datetime has jumped.  Determine the time between ensembles.
        Then verify that all additional ensembles are the same time apart.
        :param ens: Ensemble data.
        :param prev_ens_dt: Previous Ensemble
        :param show_live_errors: Show the errors occurring as file is read in or wait until entire file complete
        :param prev_ens_dt: Previous Ensemble Delta Time
        :return: True = Found an issue, Err String, Ensemble DateTime, Ensemble DT
        """
        err_str = ""
        found_issue = False
        dt = 0
        ens_datetime = None

        if ens.IsEnsembleData:
            if not prev_ens_dt or prev_ens_dt == 0:
                # Get the current datetime
                ens_datetime = ens.EnsembleData.datetime()
                dt = 0
            elif ens.EnsembleData.is_vertical_beam():
                # Ignore vertical beam to combine 4beam and vertical beam
                return found_issue, err_str, prev_ens_dt, ens_delta_time
            else:
                # Get the current datetime
                ens_datetime = ens.EnsembleData.datetime()
                is_prev_ens_vertical = ens.EnsembleData.is_vertical_beam()

                # Calculate the difference in time between the previous and this ensemble
                dt = (ens_datetime - prev_ens_dt).total_seconds()

                # Verify the times are available
                # Then verify the ensemble delta time are the same from last ensemble
                if ens_delta_time != 0 and dt != 0 and dt != ens_delta_time:
                    err_str = "Error in ensemble: " + str(ens.EnsembleData.EnsembleNumber) + "\tDateTime Jump: [Actual DT: " + str(ens_delta_time) + " DT:" + str(dt) + " Curr:" + str(ens_datetime) + " Prev: " + str(prev_ens_dt) + "]"

                    # Display the error if turned on
                    if show_live_errors:
                        print(err_str)

                    # Record the error
                    found_issue = True

        return found_issue, err_str, ens_datetime, dt

    @staticmethod
    def check_amplitude_0db(ens, show_live_errors):
        """
        Check if the amplitude is less than 10 db.  If a majority of the
        bins are less then 10 dB, then there is an issue.
        :param ens: Ensemble data.
        :param show_live_errors: Show the errors occurring as file is read in or wait until entire file complete
        :return: True = Found an issue
        """
        err_str = ""
        found_issue = False

        if ens.IsAmplitude:

            # Get the number of bins and beams
            bin_count = ens.Amplitude.num_elements

            # Initialize the list with all 0's with each beam
            bad_bin = [0] * ens.Amplitude.element_multiplier

            for beam in range(ens.Amplitude.element_multiplier):
                for bin_num in range(ens.Amplitude.num_elements):

                    # Accumulate the bad bins
                    if ens.Amplitude.Amplitude[bin_num][beam] <= 7.0:
                        bad_bin[beam] += 1

            # Log all the bad beams
            bad_beams = ""
            for beam_check in range(ens.Amplitude.element_multiplier):
                if bad_bin[beam_check] > int(bin_count * 0.8):
                    bad_beams += str(beam_check) + ","

            if bad_beams:
                err_str = "Error in ensemble: " + str(ens.EnsembleData.EnsembleNumber) + " Amplitude[" + str(bad_beams[:-1]) + "] : 0 dB"

                # Display the error if turned on
                if show_live_errors:
                    print(err_str)

                # Record the error
                found_issue = True

        return found_issue, err_str

    @staticmethod
    def check_correlation_1pct(ens, show_live_errors):
        """
        Check if the correlation is less than 100 percent (1.0).  If a majority of the
        bins are 100 percent, then there is an issue.
        :param ens: Ensemble data.
        :param show_live_errors: Show the errors occurring as file is read in or wait until entire file complete
        :return: True = Found an issue
        """
        err_str = ""
        found_issue = False

        if ens.IsCorrelation:

            # Get the number of bins and beams
            bin_count = ens.Correlation.num_elements

            # Initialize the list with all 0's with each beam
            bad_bin = [0] * ens.Correlation.element_multiplier

            for beam in range(ens.Correlation.element_multiplier):
                for bin_num in range(ens.Correlation.num_elements):

                    # Accumulate the bad bins
                    if ens.Correlation.Correlation[bin_num][beam] >= 1.0:
                        bad_bin[beam] += 1

            # Log all the bad beams
            bad_beams = ""
            for beam_check in range(ens.Correlation.element_multiplier):
                if bad_bin[beam_check] > int(bin_count * 0.8):
                    bad_beams += str(beam_check) + ","

            if bad_beams:
                err_str = "Error in ensemble: " + str(ens.EnsembleData.EnsembleNumber) + " Correlation[" + str(bad_beams[:-1]) + "] : 100%"

                # Display the error if turned on
                if show_live_errors:
                    print(err_str)

                # Record the error
                found_issue = True

        return found_issue, err_str

    @staticmethod
    def check_tilt_extreme(ens, show_live_errors, max_tilt=30.0):
        """
        Check if the tilts exceed the given max_tilt in degrees.
        If the tilt is extreme, bin mapping will not profile completely.
        :param ens: Ensemble data.
        :param show_live_errors: Show the errors occurring as file is read in or wait until entire file complete
        :param max_tilt: Check for this maximum tilt value in degrees.
        :return: True = Found an issue
        """
        err_str = ""
        found_issue = False

        # Check the Pitch for extreme
        if ens.IsEnsembleData and ens.IsAncillaryData:
            if ens.AncillaryData.is_upward_facing():
                # Upward looking, if roll is greater than max tilt
                # Good tilt is 0 to max_tilt
                if ens.AncillaryData.Roll > max_tilt:
                    err_str = "Error in ensemble: " + str(ens.EnsembleData.EnsembleNumber) + "\t Roll Tilt Extreme: [" + str(ens.AncillaryData.Roll) + "]"

                    # Display the error if turned on
                    if show_live_errors:
                        print(err_str)

                    # Record the error
                    found_issue = True
            else:
                # Downward facing 180-max_tilt to 180 is OK
                if (180.0 - max_tilt) > ens.AncillaryData.Roll > (-180.0 + max_tilt):
                    err_str = "Error in ensemble: " + str(ens.EnsembleData.EnsembleNumber) + "\t Roll Tilt Extreme: [" + str(ens.AncillaryData.Roll) + "]"

                    # Display the error if turned on
                    if show_live_errors:
                        print(err_str)

                    # Record the error
                    found_issue = True

            # Check the Roll for extreme
            # Roll is -180 to 180
            # Upward looking, if roll is greater than max tilt
            # Good tilt is 0-max_tilt to max_tilt
            if ens.AncillaryData.Pitch < (0.0 - max_tilt) or ens.AncillaryData.Pitch > max_tilt:
                # Add new line if pitch error also found
                if found_issue:
                    err_str += "/n"

                err_str += "Error in ensemble: " + str(ens.EnsembleData.EnsembleNumber) + "\tPitch Tilt Extreme: [" + str(ens.AncillaryData.Roll) + "]"

                # Display the error if turned on
                if show_live_errors:
                    print(err_str)

                # Record the error
                found_issue = True

        return found_issue, err_str


if __name__ == "__main__":
    checker = RtiCheckFile()
    checker.select_and_process()

import logging
import datetime
from netCDF4 import Dataset
from pathlib import Path
import os
from obsub import event
from typing import List, Set, Dict, Tuple, Optional
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Utilities.check_binary_file import RtiCheckFile
from rti_python.Utilities.read_binary_file import ReadBinaryFile
import numpy as np
import copy

"""
Convert full profile Rowe Technologies Inc. ADCP data ensembles currents to a netCDF4 file.

Reference:
    Code referenced from https://github.com/mmartini-usgs/ADCPy
"""


class RtiNetcdf:

    def __init__(self):
        self.cdf_file_path = []
        self.ensemble_count = 0
        self.netcdf_index = 0

        # netCDF setup
        self.is_netcdf_setup = False
        self.netcdf_file_path = ""
        self.ensembles_to_process = [0, 0]

        # Store previous 4 beam ensemble to combine with a vertical beam ensemble
        self.prev_4_beam_ens = None
        self.ens_delta_time = 0
        self.first_ens_dt = None

        # Create the CDF file
        self.cdf_file = None

    def analyze_file(self, file_path: str):
        """
        Read in the file to determine all the attributes of the file.
        :param file_path: File path.
        :type file_path: str
        :return: Dictionary of all the attributes.
        :rtype: dictionary
        """
        # Get the information about the file
        logging.debug("----------------------------------")
        logging.debug("Start Analyzing File: " + file_path)
        file_check = RtiCheckFile()
        file_check.file_progress_event += self.file_progress_handler
        file_check.process([file_path], show_live_error=False, show_progress_bar=False)
        self.ensemble_count = file_check.ens_count

        # Check if pairs is 0, then use ensemble count
        # There are no pairs of ensemble is this data
        total_ensembles = file_check.ens_pairs_count
        if total_ensembles == 0:
            total_ensembles = file_check.ens_count

        logging.debug("Total Ensembles: " + str(total_ensembles))

        file_results = {
            'EnsCount': file_check.ens_count,
            'PrimaryEnsCount': file_check.primary_beam_ens_count,
            'VerticalEnsCount': file_check.vert_beam_ens_count,
            'EnsPairCount': file_check.ens_pairs_count,
            'FirstEnsDateTime': file_check.first_ens.EnsembleData.datetime_str(),
            'LastEnsDateTime': file_check.last_ens.EnsembleData.datetime_str(),
            'EnsembleDeltaTime': file_check.ens_delta_time,
            'BadEnsCount': file_check.bad_ens,
            'EnsErrors': file_check.error_output_str,
            'IsUpward': file_check.is_upward,
            'FilePath': file_path,
            'CompleteFileDesc': file_path + " - Total Ensembles: " + str(total_ensembles) + " Delta: " + str(file_check.ens_delta_time) + " Start: " + file_check.first_ens.EnsembleData.datetime_str() + " End: " + file_check.last_ens.EnsembleData.datetime_str(),
        }

        logging.debug("Completed Analyzing File: " + file_path)
        logging.debug("----------------------------------")

        return file_results

    def file_progress_handler(self, sender, bytes_read: int, total_size: int, file_name: str):
        """
        Pass the event handler to this objects event so others can monitor the process.
        :param sender: NOT USED
        :type sender:
        :param bytes_read: Bytes read.
        :type bytes_read: int
        :param total_size: Total bytes of the file.
        :type total_size: int
        :param file_name: File name being processed.
        :type file_name: str
        :return:
        :rtype:
        """
        # Pass the event to subscribers
        self.file_progress_event(bytes_read, total_size, file_name)
        logging.debug("File Progress: " + str(bytes_read) + " Total: " + str(total_size) + " " + file_name)

    @event
    def file_progress_event(self, bytes_read: int, total_size: int, file_name: str):
        """
        Monitor this event for the file progress.  This will give the number of bytes
        currently read.
        :param bytes_read: Bytes read.
        :type bytes_read: integer
        :param total_size: Total bytes in the file.
        :type total_size: integer
        :param file_name: File name currently reading.
        :type file_name: string
        :return:
        :rtype:
        """
        logging.debug(file_name + ' Bytes Read: ' + str(bytes_read) + " of " + str(total_size))

    @event
    def ensemble_progress_event(self, ens: Ensemble):
        """
        Monitor the ensembles being processed.
        This will pass the event to subcribers when a new
        ensemble is received to process.
        :param ens: Ensemble to process.
        :type ens: Ensemble
        :return:
        :rtype:
        """
        if ens.IsEnsembleData:
            logging.debug(str(ens.EnsembleData.EnsembleNumber))

    def export(self, file_path: str, ens_to_process: List, ens_delta_time: float):
        """
        Write the netCDF file based on the files given.  Each file will get an individual
        netCDF file.  The file path will be based on the file path of the original file.
        :param file_path: File to process.
        :type file_path: str file paths.
        :param ens_to_process: List of ensembles to process.
        :type ens_to_process: [min, max]
        :param ens_delta_time: Delta time in seconds between ensembles.
        :type ens_delta_time: Float
        :return:
        :rtype:
        """
        # Set the values based on analyzing the file
        self.ensembles_to_process = ens_to_process
        self.ens_delta_time = ens_delta_time

        if os.path.exists(file_path):
            b_file_path = Path(file_path)                                   # Create A path to dissect
            file_dir = b_file_path.parent                                   # Directory of the file
            base_file_name = b_file_path.stem                               # Base file name of the selected file
            netcdf_name = base_file_name + ".nc"                            # Create a netCDF file with same file name
            self.netcdf_file_path = os.path.join(file_dir, netcdf_name)     # Create file path for netCDF file

            # Set flag to setup the netCDF file
            self.is_netcdf_setup = False

            logging.debug("Start Exporting " + file_path + " to " + self.netcdf_file_path)

            # Create the file reader to read the binary file
            read_binary = ReadBinaryFile()
            read_binary.ensemble_event += self.process_ens_handler          # Receive ensemble to process
            read_binary.file_progress += self.file_progress_handler         # Monitor file progress
            read_binary.playback(file_path)

            logging.debug("Exporting Complete for " + file_path + " to " + self.netcdf_file_path)

    def process_ens_handler(self, sender, ens: Ensemble):
        """
        Receive the data from the file.  It will process the file.
        When an ensemble is found, it will call this function with the
        complete ensemble.
        :param sender NOT USED
        :param ens: Ensemble to process.
        :return:
        """
        # Ensure we have data
        if ens:
            # Log output
            if ens and ens.IsEnsembleData:
                logging.debug(str(ens.EnsembleData.EnsembleNumber))

            # Check if the given data is a vertical beam.  We want to group the 4Beam and vertical beam
            if ens.EnsembleData.is_vertical_beam():
                # Verify we have some 4 Beam data
                # If it is only vertical beam data, then a netCDF file is not created
                if self.prev_4_beam_ens:
                    # Check if the netCDF file needs to be created
                    if not self.is_netcdf_setup:
                        # Create the netCDF file
                        self.cdf_file = self.setup_netcdf_file(self.netcdf_file_path,                   # netCDF file path
                                                               self.prev_4_beam_ens,                    # 4 Beam Ensemble
                                                               ens,                                     # Vertical Beam Ensemble
                                                               self.ensembles_to_process,               # Ensembles indexes to process
                                                               self.ens_delta_time)                     # Delta time between 2 ensemble pairs

                    # Process the ensemble
                    self.add_ens_to_netcdf(self.prev_4_beam_ens,                                        # 4 Beam Ensemble
                                           ens,                                                         # Vertical Beam Ensemble
                                           None,                                                        # Ignore Errors
                                           self.ensembles_to_process,                                   # Indexes to process
                                           self.first_ens_dt)                                           # Time of first ensemble

                    # Clear the previous ensemble
                    self.prev_4_beam_ens = None

            # Also check if we are only getting 4 beam data
            elif not ens.EnsembleData.is_vertical_beam() and self.prev_4_beam_ens and not self.prev_4_beam_ens.EnsembleData.is_vertical_beam():
                # Check if the netCDF file needs to be created
                if not self.is_netcdf_setup:
                    # Create the netCDF file
                    self.cdf_file = self.setup_netcdf_file(self.netcdf_file_path,                   # netCDF file path
                                                           self.prev_4_beam_ens,                    # 4 Beam Ensemble
                                                           None,                                    # No Vertical Beam data
                                                           self.ensembles_to_process,               # Ensembles indexes to process
                                                           self.ens_delta_time)                     # Delta time between 2 ensemble pairs

                    # Add the missing previous ensemble since it was never added
                    self.add_ens_to_netcdf(self.prev_4_beam_ens,                                    # 4 Beam Ensemble
                                           None,                                                    # No Vertical Beam Ensemble
                                           None,                                                    # Ignore Errors
                                           self.ensembles_to_process,                               # Indexes to process
                                           self.first_ens_dt)                                       # Ensemble first time
                # Add the new ensemble
                self.add_ens_to_netcdf(ens,                                                         # 4 Beam Ensemble
                                       None,                                                        # No Vertical Beam Ensemble
                                       None,                                                        # Ignore Errors
                                       self.ensembles_to_process,                                   # Indexes to process
                                       self.first_ens_dt)                                           # Ensemble first time

                # Do not set prev_4_beam_ens to None here
                # It is assumed that the order will not change
                # So we can just call this block every time now
                # Which will write all the new ensembles to the netCDF file
            else:
                # Store the 4 Beam data
                self.prev_4_beam_ens = ens

                # Check if the first ensemble time needs to be set
                if not self.first_ens_dt:
                    self.first_ens_dt = ens.EnsembleData.datetime()

            # Pass the ensemble to the event for others to process
            self.ensemble_progress_event(ens)

            logging.debug(ens.EnsembleData.EnsembleNumber)

    def setup_netcdf_file(self, netcdf_file_name: str, ens: Ensemble, vert_ens: Ensemble, ensembles_to_process: Tuple, delta_t: str):
        """
        create the netcdf output file, define dimensions and variables
        :param str netcdf_file_name: path and name of netcdf file
        :param Ensemble ens: Ensemble data from the first ensemble to be read
        :param Ensemble vert_ens: Vertical Beam Ensemble data from the first ensemble to read.  Set NONE for no vertical beam.
        :param tuple ensembles_to_process: start and end ensemble indices
        :param str delta_t: time between ensembles
        :return: netcdf file object, string describing the time units for CF time
        """
        # note that
        # f4 = 4 byte, 32 bit float
        # maxfloat = 3.402823*10**38;
        # where the variable is based ona  single dimension, usually time, it is still expressed as a tuple ("time") and
        # needs to be kept that way, even though pylint complains
        intfill = -32768
        floatfill = 1E35

        logging.debug("Setting up netCDF file: " + netcdf_file_name)

        # is it possible for delta_t to be none or an int.  Deal with that here
        if delta_t is None:
            delta_t = "none"
        if isinstance(delta_t, int):
            delta_t = str(delta_t)

        # Determine how many ensembles to process
        # I am not sure why they subtract by 1 except for 0 based i guess
        nens = ensembles_to_process[1] - ensembles_to_process[0] - 1
        print('creating netCDF file %s with %s records' % (netcdf_file_name, str(nens)))

        # Create the netCDF file
        cdf = Dataset(netcdf_file_name, "w", clobber=True, format="NETCDF4")

        # dimensions, in EPIC order
        cdf.createDimension('time', nens)                               # Number of Ensembles
        cdf.createDimension('depth', ens.EnsembleData.NumBins)          # Number of bins
        cdf.createDimension('lat', 1)                                   # Latitude
        cdf.createDimension('lon', 1)                                   # Longitude

        # write global attributes
        cdf.history = "translated to netCDF by rti_netcdf.py"
        cdf.sensor_type = "Rowe"
        cdf.serial_number = ens.EnsembleData.SerialNumber
        cdf.DELTA_T = delta_t
        #cdf.sample_rate = ens_data['FLeader']['Time_Between_Ping Groups']

        cdf.setncattr("Rowe_Number_of_Cells", ens.EnsembleData.NumBins)
        cdf.setncattr("Rowe_Number_of_Beams", ens.EnsembleData.NumBeams)
        cdf.setncattr("Rowe_Bin_Depth_Cell_Length", ens.AncillaryData.BinSize * 100.0)      # Convert to cm
        cdf.setncattr("Rowe_Pings_Per_Ensemble", ens.EnsembleData.ActualPingCount)
        cdf.setncattr("Rowe_Serial_Number", ens.EnsembleData.SerialNumber)
        cdf.setncattr("Rowe_Firmware", ens.EnsembleData.firmware_str())
        cdf.setncattr("Rowe_Salinity_PPT", ens.AncillaryData.Salinity)
        cdf.setncattr("Rowe_Subsystem_Code", ens.EnsembleData.SysFirmwareSubsystemCode)
        cdf.setncattr("Rowe_Subsystem_Config_Index", ens.EnsembleData.SubsystemConfig)
        if ens.IsSystemSetup:
            cdf.setncattr("Rowe_BT_Samples_Per_Second", ens.SystemSetup.BtSamplesPerSecond)
            cdf.setncattr("Rowe_BT_System_Freq", ens.SystemSetup.BtSystemFreqHz)
            cdf.setncattr("Rowe_BT_Cycles_Per_Code_Element", ens.SystemSetup.BtCPCE)
            cdf.setncattr("Rowe_BT_Number_Code_Elements", ens.SystemSetup.BtNCE)
            cdf.setncattr("Rowe_WP_Samples_Per_Second", ens.SystemSetup.WpSamplesPerSecond)
            cdf.setncattr("Rowe_WP_System_Freq", ens.SystemSetup.WpSystemFreqHz)
            cdf.setncattr("Rowe_WP_Cycles_Per_Code_Elements", ens.SystemSetup.WpCPCE)
            cdf.setncattr("Rowe_WP_Number_Code_Elements", ens.SystemSetup.WpNCE)
            cdf.setncattr("Rowe_WP_Number_Code_Repeats", ens.SystemSetup.WpRepeatN)
            cdf.setncattr("Rowe_WP_Lag_Samples", ens.SystemSetup.WpLagSamples)
            cdf.setncattr("Rowe_Voltage", ens.SystemSetup.Voltage)
            cdf.setncattr("Rowe_Xmt_Voltage", ens.SystemSetup.XmtVoltage)
            cdf.setncattr("Rowe_BT_Broadband_Mode", ens.SystemSetup.BtBroadband)
            cdf.setncattr("Rowe_BT_Lag_Length", ens.SystemSetup.BtLagLength)
            cdf.setncattr("Rowe_BT_Long_Range_Switch_Depth", ens.SystemSetup.BtNarrowband)
            cdf.setncattr("Rowe_BT_Beam_Mux", ens.SystemSetup.BtBeamMux)
            cdf.setncattr("Rowe_WP_Broadband_Mode", ens.SystemSetup.WpBroadband)
            cdf.setncattr("Rowe_WP_Lag_Length", ens.SystemSetup.WpLagLength)
            cdf.setncattr("Rowe_WP_Transmit_Bandwidth", ens.SystemSetup.WpTransmitBandwidth)
            cdf.setncattr("Rowe_WP_Receive_Bandwidth", ens.SystemSetup.WpReceiveBandwidth)
            cdf.setncattr("Rowe_Transmit_Boost_Neg_Volt", ens.SystemSetup.TransmitBoostNegVolt)
            cdf.setncattr("Rowe_WP_Beam_Mux", ens.SystemSetup.WpBeamMux)

        varobj = cdf.createVariable('Rec',              # Name
                                    'u4',               # Unsigned 32bit integer
                                    'time',             # Time Dimension created above
                                    fill_value=intfill) # Fill missing values with this value
        varobj.units = "count"
        varobj.long_name = "Ensemble Number"
        # the ensemble number is a two byte LSB and a one byte MSB (for the rollover)
        # varobj.valid_range = [0, 2**23]

        """
        # it's not yet clear which way to go with this.  python tools like xarray
        # and panoply demand that time be a CF defined time.
        # USGS CMG MATLAB tools need time and time2
        # TODO - CF_time can come out as YYYY-M-D for dates with single digit months and days, check to see if this is ISO
        # and fix if it is not.  This is a better way:
        # d = datetime.datetime(2010, 7, 4, 12, 15, 58)
        # '{:%Y-%m-%d %H:%M:%S}'.format(d)
        if time_type == 'EPIC_with_CF':
            # we include time and time2 for EPIC compliance
            varobj = cdf.createVariable('time', 'u4', ('time',))
            varobj.units = "True Julian Day"
            varobj.epic_code = 624
            varobj.datum = "Time (UTC) in True Julian Days: 2440000 = 0000 h on May 23, 1968"
            varobj.NOTE = "Decimal Julian day [days] = time [days] + ( time2 [msec] / 86400000 [msec/day] )"
            varobj = cdf.createVariable('time2', 'u4', ('time',))
            varobj.units = "msec since 0:00 GMT"
            varobj.epic_code = 624
            varobj.datum = "Time (UTC) in True Julian Days: 2440000 = 0000 h on May 23, 1968"
            varobj.NOTE = "Decimal Julian day [days] = time [days] + ( time2 [msec] / 86400000 [msec/day] )"
            cf_units = ""
            # we include cf_time for cf compliance and use by python packages like xarray
            # if f8, 64 bit is not used, time is clipped
            # for ADCP fast sampled, single ping data, need millisecond resolution
            varobj = cdf.createVariable('cf_time', 'f8', 'time')
            # for cf convention, always assume UTC for now, and use the UNIX Epoch as the reference
            varobj.units = "seconds since %d-%d-%d %d:%d:%f 0:00" % (ens.EnsembleData.Year - 2000,
                                                                     ens.EnsembleData.Month,
                                                                     ens.EnsembleData.Day,
                                                                     ens.EnsembleData.Hour,
                                                                     ens.EnsembleData.Minute,
                                                                     ens.EnsembleData.Second +
                                                                     ens.EnsembleData.HSec / 100)

            varobj.standard_name = "time"
            varobj.axis = "T"
        elif time_type == "CF_with_EPIC":
            # cf_time for cf compliance and use by python packages like xarray
            # if f8, 64 bit is not used, time is clipped
            # for ADCP fast sampled, single ping data, need millisecond resolution
            varobj = cdf.createVariable('time', 'f8', ('time',))
            # for cf convention, always assume UTC for now, and use the UNIX Epoch as the reference
            varobj.units = "seconds since %d-%d-%d %d:%d:%f 0:00" % (ens.EnsembleData.Year - 2000,
                                                                     ens.EnsembleData.Month,
                                                                     ens.EnsembleData.Day,
                                                                     ens.EnsembleData.Hour,
                                                                     ens.EnsembleData.Minute,
                                                                     ens.EnsembleData.Second +
                                                                     ens.EnsembleData.HSec / 100)

            cf_units = "seconds since %d-%d-%d %d:%d:%f 0:00" % (
                ens.EnsembleData.Year - 2000,
                ens.EnsembleData.Month,
                ens.EnsembleData.Day,
                ens.EnsembleData.Hour,
                ens.EnsembleData.Minute,
                ens.EnsembleData.Second + ens.EnsembleData.HSec / 100)

            varobj.standard_name = "time"
            varobj.axis = "T"
            varobj.type = "UNEVEN"
            # we include time and time2 for EPIC compliance
            # this statement resulted in a fill value of -1??
            # varobj = cdf.createVariable('EPIC_time','u4',('time',))
            varobj = cdf.createVariable('EPIC_time', 'u4', ('time',), fill_value=False)
            varobj.units = "True Julian Day"
            varobj.epic_code = 624
            varobj.datum = "Time (UTC) in True Julian Days: 2440000 = 0000 h on May 23, 1968"
            varobj.NOTE = "Decimal Julian day [days] = time [days] + ( time2 [msec] / 86400000 [msec/day] )"
            # this statement resulted in a fill value of -1??
            # varobj = cdf.createVariable('EPIC_time2','u4',('time',))
            varobj = cdf.createVariable('EPIC_time2', 'u4', ('time',), fill_value=False)
            varobj.units = "msec since 0:00 GMT"
            varobj.epic_code = 624
            varobj.datum = "Time (UTC) in True Julian Days: 2440000 = 0000 h on May 23, 1968"
            varobj.NOTE = "Decimal Julian day [days] = time [days] + ( time2 [msec] / 86400000 [msec/day] )"
        elif time_type == "EPIC":
            varobj = cdf.createVariable('time', 'u4', ('time',))
            varobj.units = "True Julian Day"
            varobj.epic_code = 624
            varobj.datum = "Time (UTC) in True Julian Days: 2440000 = 0000 h on May 23, 1968"
            varobj.NOTE = "Decimal Julian day [days] = time [days] + ( time2 [msec] / 86400000 [msec/day] )"
            varobj = cdf.createVariable('time2', 'u4', ('time',))
            varobj.units = "msec since 0:00 GMT"
            varobj.epic_code = 624
            varobj.datum = "Time (UTC) in True Julian Days: 2440000 = 0000 h on May 23, 1968"
            varobj.NOTE = "Decimal Julian day [days] = time [days] + ( time2 [msec] / 86400000 [msec/day] )"
            cf_units = ""
        else:  # only CF time
        """
        # this is best for use by python packages like xarray
        # if f8, 64 bit is not used, time is clipped
        # for ADCP fast sampled, single ping data, need millisecond resolution
        varobj = cdf.createVariable('time', 'f8', ('time',))
        # for cf convention, always assume UTC for now, and use the UNIX Epoch as the reference
        varobj.units = "seconds since %d-%d-%d %d:%d:%f 0:00" % (ens.EnsembleData.Year - 2000,
                                                                 ens.EnsembleData.Month,
                                                                 ens.EnsembleData.Day,
                                                                 ens.EnsembleData.Hour,
                                                                 ens.EnsembleData.Minute,
                                                                 ens.EnsembleData.Second + ens.EnsembleData.HSec / 100)

        cf_units = "seconds since %d-%d-%d %d:%d:%f 0:00" % (
            ens.EnsembleData.Year - 2000,
            ens.EnsembleData.Month,
            ens.EnsembleData.Day,
            ens.EnsembleData.Hour,
            ens.EnsembleData.Minute,
            ens.EnsembleData.Second + ens.EnsembleData.HSec / 100)
        varobj.standard_name = "time"
        varobj.axis = "T"
        varobj.type = "UNEVEN"

        varobj = cdf.createVariable('bindist', 'f4', ('depth',), fill_value=floatfill)
        # note name is one of the netcdf4 reserved attributes, use setncattr
        varobj.setncattr('name', "bindist")
        varobj.units = "m"
        varobj.long_name = "bin distance from instrument for slant beams"
        varobj.epic_code = 0
        # varobj.valid_range = [0 0]
        varobj.NOTE = "distance is calculated from center of bin 1 and bin size"
        bindist = []
        for idx in range(ens.EnsembleData.NumBins):
            bindist.append(idx * (ens.AncillaryData.BinSize) + ens.AncillaryData.FirstBinRange)
        varobj[:] = bindist[:]

        varobj = cdf.createVariable('depth', 'f4', ('depth',))  # no fill for ordinates
        varobj.units = "m"
        varobj.long_name = "distance from transducer, depth placeholder"
        varobj.center_first_bin_m = ens.AncillaryData.FirstBinRange
        #varobj.blanking_distance_m = ens_data['FLeader']['Blank_after_Transmit_cm'] / 100
        varobj.bin_size_m = ens.AncillaryData.BinSize
        varobj.bin_count = ens.EnsembleData.NumBins
        varobj[:] = bindist[:]

        varobj = cdf.createVariable('sv', 'f4', ('time',), fill_value=floatfill)
        varobj.units = "m s-1"
        varobj.long_name = "sound velocity (m s-1)"
        # varobj.valid_range = [1400, 1600]

        for i in range(ens.EnsembleData.NumBeams):
            varname = "vel%d" % (i + 1)
            varobj = cdf.createVariable(varname, 'f4', ('time', 'depth'), fill_value=floatfill)
            varobj.units = "mm s-1"
            varobj.long_name = "Beam %d velocity (mm s-1)" % (i + 1)
            varobj.epic_code = 1277 + i
            # varobj.valid_range = [-32767, 32767]

        for i in range(ens.EnsembleData.NumBeams):
            varname = "cor%d" % (i + 1)
            varobj = cdf.createVariable(varname, 'u2', ('time', 'depth'), fill_value=intfill)
            varobj.units = "counts"
            varobj.long_name = "Beam %d correlation" % (i + 1)
            varobj.epic_code = 1285 + i
            # varobj.valid_range = [0, 255]

        for i in range(ens.EnsembleData.NumBeams):
            varname = "att%d" % (i + 1)
            varobj = cdf.createVariable(varname, 'u2', ('time', 'depth'), fill_value=intfill)
            varobj.units = "counts"
            varobj.epic_code = 1281 + i
            varobj.long_name = "ADCP attenuation of beam %d" % (i + 1)
            # varobj.valid_range = [0, 255]

        if ens.IsGoodBeam:
            for i in range(ens.EnsembleData.NumBeams):
                varname = "PGd%d" % (i + 1)
                varobj = cdf.createVariable(varname, 'u2', ('time', 'depth'), fill_value=intfill)
                varobj.units = "counts"
                varobj.long_name = "Percent Good Beam %d" % (i + 1)
                varobj.epic_code = 1241 + i
                # varobj.valid_range = [0, 100]

        if ens.IsRangeTracking:
            for i in range(ens.EnsembleData.NumBeams):
                varname = "RTR%d" % (i + 1)
                varobj = cdf.createVariable(varname, 'f4', ('time',), fill_value=floatfill)
                varobj.units = "meters"
                varobj.long_name = "Range Tracking Range Beam %d" % (i + 1)
                #varobj.epic_code = 1241 + i

            for i in range(ens.EnsembleData.NumBeams):
                varname = "RTSNR%d" % (i + 1)
                varobj = cdf.createVariable(varname, 'f4', ('time',), fill_value=floatfill)
                varobj.units = "dB"
                varobj.long_name = "Range Tracking SNR Beam %d" % (i + 1)
                #varobj.epic_code = 1241 + i

            for i in range(ens.EnsembleData.NumBeams):
                varname = "RTAmp%d" % (i + 1)
                varobj = cdf.createVariable(varname, 'f4', ('time',), fill_value=floatfill)
                varobj.units = "dB"
                varobj.long_name = "Range Tracking Amplitude Beam %d" % (i + 1)
                #varobj.epic_code = 1241 + i

            for i in range(ens.EnsembleData.NumBeams):
                varname = "RTCorr%d" % (i + 1)
                varobj = cdf.createVariable(varname, 'f4', ('time',), fill_value=floatfill)
                varobj.units = "percent"
                varobj.long_name = "Range Tracking Correlation Beam %d" % (i + 1)
                #varobj.epic_code = 1241 + i

        varobj = cdf.createVariable('Hdg', 'f4', ('time',), fill_value=floatfill)
        varobj.units = "hundredths of degrees"
        varobj.long_name = "INST Heading"
        varobj.epic_code = 1215
        #varobj.heading_alignment = ens_data['FLeader']['Heading_Alignment_Hundredths_of_Deg']
        #varobj.heading_bias = ens_data['FLeader']['Heading_Bias_Hundredths_of_Deg']
        # varobj.valid_range = [0, 36000]
        #if ens_data['FLeader']['Heading_Bias_Hundredths_of_Deg'] == 0:
        #    varobj.NOTE_9 = "no heading bias was applied by EB during deployment or by wavesmon"
        #else:
        #    varobj.NOTE_9 = "a heading bias was applied by EB during deployment or by wavesmon"

        varobj = cdf.createVariable('Ptch', 'f4', ('time',), fill_value=floatfill)
        varobj.units = "hundredths of degrees"
        varobj.long_name = "INST Pitch"
        varobj.epic_code = 1216
        # varobj.valid_range = [-18000, 18000] # physical limit, not sensor limit

        varobj = cdf.createVariable('Roll', 'f4', ('time',), fill_value=floatfill)
        varobj.units = "hundredths of degrees"
        varobj.long_name = "INST Roll"
        varobj.epic_code = 1217
        # varobj.valid_range = [-18000, 18000] # physical limit, not sensor limit

        #varobj = cdf.createVariable('HdgSTD', 'f4', ('time',), fill_value=floatfill)
        #varobj.units = "degrees"
        #varobj.long_name = "Heading Standard Deviation"

        #varobj = cdf.createVariable('PtchSTD', 'f4', ('time',), fill_value=floatfill)
        #varobj.units = "tenths of degrees"
        #varobj.long_name = "Pitch Standard Deviation"

        #varobj = cdf.createVariable('RollSTD', 'f4', ('time',), fill_value=floatfill)
        #varobj.units = "tenths of degrees"
        #varobj.long_name = "Roll Standard Deviation"

        varobj = cdf.createVariable('Tx', 'f4', ('time',), fill_value=floatfill)
        varobj.units = "hundredths of degrees"
        varobj.long_name = "ADCP Transducer Temperature"
        varobj.epic_code = 3017
        # varobj.valid_range = [-500, 4000]

        varobj = cdf.createVariable('S', 'f4', ('time',), fill_value=floatfill)
        varobj.units = "PPT"
        varobj.long_name = "SALINITY (PPT)"
        varobj.epic_code = 40
        # varobj.valid_range = [0, 40]

        #varobj = cdf.createVariable('xmitc', 'f4', ('time',), fill_value=floatfill)
        #varobj.units = "amps"
        #varobj.long_name = "transmit current"

        varobj = cdf.createVariable('voltage', 'f4', ('time',), fill_value=floatfill)
        varobj.units = "volts"
        varobj.long_name = "Input voltage"

        varobj = cdf.createVariable('xmitv', 'f4', ('time',), fill_value=floatfill)
        varobj.units = "volts"
        varobj.long_name = "transmit voltage"

        varobj = cdf.createVariable('Ambient_Temp', 'i2', ('time',), fill_value=intfill)
        varobj.units = "C"
        varobj.long_name = "Ambient_Temp"

        #varobj = cdf.createVariable('Pressure+', 'i2', ('time',), fill_value=intfill)
        #varobj.units = "unknown"
        #varobj.long_name = "Pressure+"

        #varobj = cdf.createVariable('Pressure-', 'i2', ('time',), fill_value=intfill)
        #varobj.units = "unknown"
        #varobj.long_name = "Pressure-"

        #varobj = cdf.createVariable('Attitude_Temp', 'i2', ('time',), fill_value=intfill)
        #varobj.units = "C"
        #varobj.long_name = "Attitude_Temp"

        varobj = cdf.createVariable('Status', 'i2', ('time',), fill_value=intfill)
        varobj.units = "STATUS BITS"
        varobj.long_name = "Status"

        #for i in range(4):
        #    varname = "EWD%d" % (i + 1)
        #    varobj = cdf.createVariable(varname, 'u2', ('time',), fill_value=intfill)
        #    varobj.units = "binary flag"
        #    varobj.long_name = "Error Status Word %d" % (i + 1)

        if ens.AncillaryData.Pressure > 0:
            varobj = cdf.createVariable('Pressure', 'f4', ('time',), fill_value=floatfill)
            varobj.units = "deca-pascals"
            varobj.long_name = "ADCP Transducer Pressure"
            varobj.epic_code = 4

        if ens.IsNmeaData:
            varobj = cdf.createVariable('Lat', 'f4', ('time',), fill_value=floatfill)
            varobj.units = "degrees"
            varobj.long_name = "Latitude Decimal Degrees"

            varobj = cdf.createVariable('Lon', 'f4', ('time',), fill_value=floatfill)
            varobj.units = "degrees"
            varobj.long_name = "Longitude Decimal Degrees"

            #varobj = cdf.createVariable('PressVar', 'f4', ('time',), fill_value=floatfill)
            #varobj.units = "deca-pascals"
            #varobj.long_name = "ADCP Transducer Pressure Variance"

        if ens.IsBottomTrack:
            # write globals attributable to BT setup
            cdf.setncattr('Rowe', ens.BottomTrack.ActualPingCount)
            #cdf.setncattr('TRDI_BT_reacquire_delay', ens_data['BTData']['delay_before_reacquire'])
            #cdf.setncattr('TRDI_BT_min_corr_mag', ens_data['BTData']['Corr_Mag_Min'])
            #cdf.setncattr('TRDI_BT_min_eval_mag', ens_data['BTData']['Eval_Amp_Min'])
            #cdf.setncattr('TRDI_BT_min_percent_good', ens_data['BTData']['PGd_Minimum'])
            #cdf.setncattr('TRDI_BT_mode', ens_data['BTData']['Mode'])
            #cdf.setncattr('TRDI_BT_max_err_vel', ens_data['BTData']['Err_Vel_Max'])
            # cdf.setncattr('TRDI_BT_max_tracking_depth',ens_data['BTData'][''])
            # cdf.setncattr('TRDI_BT_shallow_water_gain',ens_data['BTData'][''])

            for i in range(int(ens.BottomTrack.NumBeams)):
                varname = "BTR%d" % (i + 1)
                varobj = cdf.createVariable(varname, 'u8', ('time',), fill_value=intfill)
                varobj.units = "cm"
                varobj.long_name = "BT Range %d" % (i + 1)

            for i in range(int(ens.BottomTrack.NumBeams)):
                #varnames = ('BTWe', 'BTWu', 'BTWv', 'BTWd')
                #longnames = ('BT Error Velocity', 'BT Eastward Velocity', 'BT Northward Velocity', 'BT Vertical Velocity')
                #if ens_data['FLeader']['Coord_Transform'] == 'EARTH':
                #    varobj = cdf.createVariable(varnames[i + 1], 'i2', ('time',), fill_value=intfill)
                #    varobj.units = "mm s-1"
                #    varobj.long_name = "%s, mm s-1" % longnames[i + 1]
                #else:
                varname = "BTV%d" % (i + 1)
                varobj = cdf.createVariable(varname, 'i2', ('time',), fill_value=intfill)
                varobj.units = "mm s-1"
                varobj.long_name = "BT velocity, mm s-1 %d" % (i + 1)

            for i in range(int(ens.BottomTrack.NumBeams)):
                varname = "BTc%d" % (i + 1)
                varobj = cdf.createVariable(varname, 'u2', ('time',), fill_value=intfill)
                varobj.units = "counts"
                varobj.long_name = "BT correlation %d" % (i + 1)

            for i in range(int(ens.BottomTrack.NumBeams)):
                varname = "BTe%d" % (i + 1)
                varobj = cdf.createVariable(varname, 'u2', ('time',), fill_value=intfill)
                varobj.units = "counts"
                varobj.long_name = "BT evaluation amplitude %d" % (i + 1)

            for i in range(int(ens.BottomTrack.NumBeams)):
                varname = "BTp%d" % (i + 1)
                varobj = cdf.createVariable(varname, 'u2', ('time',), fill_value=intfill)
                varobj.units = "percent"
                varobj.long_name = "BT percent good %d" % (i + 1)
                # varobj.valid_range = [0, 100]

            for i in range(int(ens.BottomTrack.NumBeams)):
                varname = "BTRSSI%d" % (i + 1)
                varobj = cdf.createVariable(varname, 'u2', ('time',), fill_value=intfill)
                varobj.units = "counts"
                varobj.long_name = "BT Receiver Signal Strength Indicator %d" % (i + 1)

            #if ens_data['BTData']['Mode'] == 0:  # water reference layer was used
            #    varobj = cdf.createVariable('BTRmin', 'f4', ('time',), fill_value=floatfill)
            #    varobj.units = 'dm'
            #    varobj.long_name = "BT Ref. min"
            #    varobj = cdf.createVariable('BTRnear', 'f4', ('time',), fill_value=floatfill)
            #    varobj.units = 'dm'
            #    varobj.long_name = "BT Ref. near"
            #    varobj = cdf.createVariable('BTRfar', 'f4', ('time',), fill_value=floatfill)
            #    varobj.units = 'dm'
            #    varobj.long_name = "BT Ref. far"

            #    for i in range(4):
            #        varname = "BTRv%d" % (i + 1)
            #        varobj = cdf.createVariable(varname, 'i2', ('time',), fill_value=intfill)
            #        varobj.units = "mm s-1"
            #        varobj.long_name = "BT Ref. velocity, mm s-1 %d" % (i + 1)

            #    for i in range(4):
            #        varname = "BTRc%d" % (i + 1)
            #        varobj = cdf.createVariable(varname, 'u2', ('time',), fill_value=intfill)
            #        varobj.units = "counts"
            #        varobj.long_name = "BT Ref. correlation %d" % (i + 1)

            #    for i in range(4):
            #        varname = "BTRi%d" % (i + 1)
            #        varobj = cdf.createVariable(varname, 'u2', ('time',), fill_value=intfill)
            #        varobj.units = "counts"
            #        varobj.long_name = "BT Ref. intensity %d" % (i + 1)

            #    for i in range(4):
            #        varname = "BTRp%d" % (i + 1)
            #        varobj = cdf.createVariable(varname, 'u2', ('time',), fill_value=intfill)
            #        varobj.units = "percent"
            #        varobj.long_name = "BT Ref. percent good %d" % (i + 1)
            #        varobj.epic_code = 1269 + i

        # If there is a vertical beam
        if vert_ens:
            # Set the Global Attributes
            cdf.setncattr("Rowe_VBeam_Number_of_Cells", vert_ens.EnsembleData.NumBins)
            cdf.setncattr("Rowe_VBeam_Number_of_Beams", vert_ens.EnsembleData.NumBeams)
            cdf.setncattr("Rowe_VBeam_Bin_Depth_Cell_Length", vert_ens.AncillaryData.BinSize * 100.0)  # Convert to cm
            cdf.setncattr("Rowe_VBeam_Pings_Per_Ensemble", vert_ens.EnsembleData.ActualPingCount)
            cdf.setncattr("Rowe_VBeam_Serial_Number", vert_ens.EnsembleData.SerialNumber)
            cdf.setncattr("Rowe_VBeam_Firmware", vert_ens.EnsembleData.firmware_str())
            cdf.setncattr("Rowe_VBeam_Salinity_PPT", vert_ens.AncillaryData.Salinity)
            cdf.setncattr("Rowe_VBeam_Subsystem_Code", vert_ens.EnsembleData.SysFirmwareSubsystemCode)
            cdf.setncattr("Rowe_VBeam_Subsystem_Config_Index", vert_ens.EnsembleData.SubsystemConfig)
            if vert_ens.IsBottomTrack:
                cdf.setncattr("Rowe_VBeam_BT_Pings_Per_Ensemble", vert_ens.BottomTrack.ActualPingCount)
            if vert_ens.IsSystemSetup:
                cdf.setncattr("Rowe_VBeam_BT_Samples_Per_Second", vert_ens.SystemSetup.BtSamplesPerSecond)
                cdf.setncattr("Rowe_VBeam_BT_System_Freq", vert_ens.SystemSetup.BtSystemFreqHz)
                cdf.setncattr("Rowe_VBeam_BT_Cycles_Per_Code_Element", vert_ens.SystemSetup.BtCPCE)
                cdf.setncattr("Rowe_VBeam_BT_Number_Code_Elements", vert_ens.SystemSetup.BtNCE)
                cdf.setncattr("Rowe_VBeam_WP_Samples_Per_Second", vert_ens.SystemSetup.WpSamplesPerSecond)
                cdf.setncattr("Rowe_VBeam_WP_System_Freq", vert_ens.SystemSetup.WpSystemFreqHz)
                cdf.setncattr("Rowe_VBeam_WP_Cycles_Per_Code_Elements", vert_ens.SystemSetup.WpCPCE)
                cdf.setncattr("Rowe_VBeam_WP_Number_Code_Elements", vert_ens.SystemSetup.WpNCE)
                cdf.setncattr("Rowe_VBeam_WP_Number_Code_Repeats", vert_ens.SystemSetup.WpRepeatN)
                cdf.setncattr("Rowe_VBeam_WP_Lag_Samples", vert_ens.SystemSetup.WpLagSamples)
                cdf.setncattr("Rowe_VBeam_Voltage", vert_ens.SystemSetup.Voltage)
                cdf.setncattr("Rowe_VBeam_Xmt_Voltage", vert_ens.SystemSetup.XmtVoltage)
                cdf.setncattr("Rowe_VBeam_BT_Broadband_Mode", vert_ens.SystemSetup.BtBroadband)
                cdf.setncattr("Rowe_VBeam_BT_Lag_Length", vert_ens.SystemSetup.BtLagLength)
                cdf.setncattr("Rowe_VBeam_BT_Long_Range_Switch_Depth", vert_ens.SystemSetup.BtNarrowband)
                cdf.setncattr("Rowe_VBeam_BT_Beam_Mux", vert_ens.SystemSetup.BtBeamMux)
                cdf.setncattr("Rowe_VBeam_WP_Broadband_Mode", vert_ens.SystemSetup.WpBroadband)
                cdf.setncattr("Rowe_VBeam_WP_Lag_Length", vert_ens.SystemSetup.WpLagLength)
                cdf.setncattr("Rowe_VBeam_WP_Transmit_Bandwidth", vert_ens.SystemSetup.WpTransmitBandwidth)
                cdf.setncattr("Rowe_VBeam_WP_Receive_Bandwidth", vert_ens.SystemSetup.WpReceiveBandwidth)
                cdf.setncattr("Rowe_VBeam_Transmit_Boost_Neg_Volt", vert_ens.SystemSetup.TransmitBoostNegVolt)
                cdf.setncattr("Rowe_VBeam_WP_Beam_Mux", vert_ens.SystemSetup.WpBeamMux)

            if vert_ens.EnsembleData.NumBins == ens.EnsembleData.NumBins:
                varobj = cdf.createVariable("vel5", 'f4', ('time', 'depth'), fill_value=floatfill)
                varobj.units = "mm s-1"
                varobj.long_name = "Beam 5 velocity (mm s-1)"
                varobj = cdf.createVariable("cor5", 'u2', ('time', 'depth'), fill_value=intfill)
                varobj.units = "counts"
                varobj.long_name = "Beam 5 correlation"
                varobj = cdf.createVariable("att5", 'u2', ('time', 'depth'), fill_value=intfill)
                varobj.units = "counts"
                varobj.long_name = "ADCP attenuation of beam 5"
                if vert_ens.IsGoodBeam:
                    varobj = cdf.createVariable("PGd5", 'u2', ('time', 'depth'), fill_value=intfill)
                    varobj.units = "counts"
                    varobj.long_name = "Percent Good Beam 5"
                else:
                    cdf.TRDI_VBeam_note1 = 'Vertical beam data found without Percent Good'
                if vert_ens.IsRangeTracking:
                    varobj = cdf.createVariable("RTR5", 'f4', ('time',), fill_value=floatfill)
                    varobj.units = "meters"
                    varobj.long_name = "Range Tracking Range Beam 5"
                    varobj = cdf.createVariable("RTSNR5", 'f4', ('time',), fill_value=floatfill)
                    varobj.units = "dB"
                    varobj.long_name = "Range Tracking SNR Beam 5"
                    varobj = cdf.createVariable("RTAmp5", 'f4', ('time',), fill_value=floatfill)
                    varobj.units = "dB"
                    varobj.long_name = "Range Tracking Amplitude Beam 5"
                    varobj = cdf.createVariable("RTCorr5", 'f4', ('time',), fill_value=floatfill)
                    varobj.units = "percent"
                    varobj.long_name = "Range Tracking Correlation Beam 5"
                else:
                    cdf.TRDI_VBeam_note2 = 'Vertical beam data found without Range Tracking'

            else:
                print("Vertical beam data found with different number of cells.")
                cdf.TRDI_VBeam_note = "Vertical beam data found with different number of cells. " + \
                                      "Vertical beam data not exported to netCDF"
                print("Vertical beam data not exported to netCDF")

        #if 'WaveParams' in ens_data:
        #    # no units given for any of these in the TRDI docs
        #    varobj = cdf.createVariable("Hs", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "m"
        #    varobj.long_name = "Significant Wave Height (m)"
        #    varobj = cdf.createVariable("Tp", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "s"
        #    varobj.long_name = "Peak Wave Period (s)"
        #    varobj = cdf.createVariable("Dp", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "Deg."
        #    varobj.long_name = "Peak Wave Direction (Deg.)"
        #    varobj = cdf.createVariable("Dm", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "Deg."
        #    varobj.long_name = "Mea Peak Wave Direction (Deg.)"
        #    varobj = cdf.createVariable("SHmax", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "m"
        #    varobj.long_name = "Maximum Wave Height (m)"
        #    varobj.note = "from zero crossing analysis of surface track time series"
        #    varobj = cdf.createVariable("SH13", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "m"
        #    varobj.long_name = "Significant Wave Height of the largest 1/3 of the waves (m)"
        #    varobj.note = "in the field from zero crossing anaylsis of surface track time series"
        #    varobj = cdf.createVariable("SH10", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "m"
        #    varobj.long_name = "Significant Wave Height of the largest 1/10 of the waves (m)"
        #    varobj.note = "in the field from zero crossing anaylsis of surface track time series"
        #    varobj = cdf.createVariable("STmax", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "s"
        #    varobj.long_name = "Maximum Peak Wave Period (s)"
        #    varobj.note = "from zero crossing analysis of surface track time series"
        #    varobj = cdf.createVariable("ST13", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "s"
        #    varobj.long_name = "Period associated with the peak wave height of the largest 1/3 of the waves (s)"
        #    varobj.note = "in the field from zero crossing analysis of surface track time series"
        #    varobj = cdf.createVariable("ST10", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "s"
        #    varobj.long_name = "Period associated with the peak wave height of the largest 1/10 of the waves (s)"
        #    varobj.note = "in the field from zero crossing anaylsis of surface track time series"
        #    varobj = cdf.createVariable("T01", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = " "
        #    varobj = cdf.createVariable("Tz", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = " "
        #    varobj = cdf.createVariable("Tinv1", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = " "
        #    varobj = cdf.createVariable("S0", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = " "
        #    varobj = cdf.createVariable("Source", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = " "

        #if 'WaveSeaSwell' in ens_data:
        #    # no units given for any of these in the TRDI docs
        #    varobj = cdf.createVariable("HsSea", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "m"
        #    varobj.long_name = "Significant Wave Height (m)"
        #    varobj.note = "in the sea region of the power spectrum"
        #    varobj = cdf.createVariable("HsSwell", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "m"
        #    varobj.long_name = "Significant Wave Height (m)"
        #    varobj.note = "in the swell region of the power spectrum"
        #    varobj = cdf.createVariable("TpSea", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "s"
        #    varobj.long_name = "Peak Wave Period (s)"
        #    varobj.note = "in the sea region of the power spectrum"
        #    varobj = cdf.createVariable("TpSwell", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "s"
        #    varobj.long_name = "Peak Wave Period (s)"
        #    varobj.note = "in the swell region of the power spectrum"
        #    varobj = cdf.createVariable("DpSea", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "Deg."
        #    varobj.long_name = "Peak Wave Direction (Deg.)"
        #    varobj.note = "in the sea region of the power spectrum"
        #    varobj = cdf.createVariable("DpSwell", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "Deg."
        #    varobj.long_name = "Peak Wave Direction (Deg.)"
        #    varobj.note = "in the swell region of the power spectrum"
        #    varobj = cdf.createVariable("SeaSwellPeriod", 'f4', ('time',), fill_value=floatfill)
        #    varobj.units = "s"
        #    varobj.long_name = "Transition Period between Sea and Swell (s)"

        # Set the flag that the netCDF file was created
        self.is_netcdf_setup = True

        logging.debug("Completed setting up netCDF file: " + netcdf_file_name)

        return cdf

    def add_ens_to_netcdf(self, ens: Ensemble, vert_ens: Ensemble, ens_error, ens2process: List, first_ens_dt: datetime):
        """
        Add the given ensemble to netCDF file.

        :param ens: Ensemble data to add to the netCDF
        :type ens: Ensemble
        :param vert_ens: Vertical Beam Ensemble to add to the netCDF.  If no vertical beam, set to NONE.
        :type vert_ens: Ensemble
        :param ens_error:
        :type ens_error:
        :param list ens2process: [start, end] ensembles to export.  end = -1 for all ensembles in file
        :type ens2process: List of start and end ensemble to export. end = -1 for all ensembles in file
        :param first_ens_dt: First ensemble datetime to calculate the delta.
        :return:
        :rtype:
        """

        logging.debug("Add Ensemble to netCDF file: " + self.netcdf_file_path + " " + str(ens.EnsembleData.EnsembleNumber) + " " + str(self.ensemble_count))

        # Number of beams for 4 Beam system
        nslantbeams = ens.EnsembleData.NumBeams

        # Number of code repeats for converting correlation data
        num_repeats = 1
        if ens.IsSystemSetup:
            num_repeats = ens.SystemSetup.WpRepeatN

        # Pings per Ensemble
        pings_per_ens = ens.EnsembleData.ActualPingCount

        if (ens_error is None) and (self.ensemble_count >= ens2process[0]):
            # write to netCDF
            if self.netcdf_index == 0:
                print('--- first ensembles read at %s and Rowe #%d' % (ens.EnsembleData.datetime_str(), ens.EnsembleData.EnsembleNumber))

            varobj = self.cdf_file.variables['Rec']
            try:
                varobj[self.netcdf_index] = ens.EnsembleData.EnsembleNumber
            except Exception as ex:
                logging.debug(ex)
                # here we have reached the end of the netCDF file
                self.cdf_file.close()
                return

            """
            # time calculations done when vleader is read
            if time_type == 'EPIC_with_CF':
                varobj = self.cdf_file.variables['time']
                varobj[self.netcdf_index] = ens_data['VLeader']['EPIC_time']
                varobj = self.cdf_file.variables['time2']
                varobj[self.netcdf_index] = ens_data['VLeader']['EPIC_time2']
                varobj = self.cdf_file.variables['cf_time']
                elapsed = ens.EnsembleData.datetime() - first_ens_dt  # timedelta
                elapsed_sec = elapsed.total_seconds()
                varobj[self.netcdf_index] = elapsed_sec
            elif time_type == 'CF_with_EPIC':
                varobj = self.cdf_file.variables['time']
                elapsed = ens.EnsembleData.datetime() - first_ens_dt  # timedelta
                elapsed_sec = elapsed.total_seconds()
                if elapsed_sec == 0:
                    print('elapsed seconds from ensemble {} is {}'.format(self.ensemble_count, elapsed_sec))

                varobj[self.netcdf_index] = elapsed_sec
                t1, t2 = cftime2EPICtime(elapsed_sec, cf_units)
                varobj = self.cdf_file.variables['EPIC_time']
                varobj[self.netcdf_index] = t1
                varobj = self.cdf_file.variables['EPIC_time2']
                varobj[self.netcdf_index] = t2
            elif time_type == 'EPIC':
                varobj = self.cdf_file.variables['time']
                varobj[self.netcdf_index] = ens_data['VLeader']['EPIC_time']
                varobj = self.cdf_file.variables['time2']
                varobj[self.netcdf_index] = ens_data['VLeader']['EPIC_time2']
            else:  # only CF time, the default
            """
            varobj = self.cdf_file.variables['time']
            elapsed = ens.EnsembleData.datetime() - first_ens_dt  # timedelta
            elapsed_sec = elapsed.total_seconds()
            varobj[self.netcdf_index] = elapsed_sec

            # diagnostic
            if (ens2process[1]-ens2process[0]-1) < 100:
                print('%d %s' % (ens.EnsembleData.EnsembleNumber, ens.EnsembleData.datetime_str()))

            varobj = self.cdf_file.variables['sv']
            varobj[self.netcdf_index] = round(ens.AncillaryData.SpeedOfSound)

            # RTB and PD0 do not share the same Beam Order
            # RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1
            # RTB XYZ  0,1,2,3 = PD0 XYZ 1,0,-2,3
            # RTB ENU  0,1,2,3 = PD0 ENU 0,1,2,3
            # Beams will need to be reordered to match

            # Convert from m/s to mm/s
            for i in range(nslantbeams):
                varname = "vel%d" % (i+1)
                varobj = self.cdf_file.variables[varname]
                varobj[self.netcdf_index, :] = ens.BeamVelocity.pd0_mm_per_sec(pd0_beam_num=i)                          # Convert to mm/s and reorder beams

            for i in range(nslantbeams):
                varname = "cor%d" % (i+1)
                varobj = self.cdf_file.variables[varname]
                varobj[self.netcdf_index, :] = ens.Correlation.pd0_counts(num_repeat=num_repeats, pd0_beam_num=i)       # Convert to counts and reorder beams

            for i in range(nslantbeams):
                varname = "att%d" % (i+1)
                varobj = self.cdf_file.variables[varname]
                varobj[self.netcdf_index, :] = ens.Amplitude.pd0_counts(pd0_beam_num=i)                                 # Convert to counts and reorder beams

            if ens.IsGoodBeam:
                for i in range(nslantbeams):
                    varname = "PGd%d" % (i+1)
                    varobj = self.cdf_file.variables[varname]
                    varobj[self.netcdf_index, :] = ens.GoodBeam.pd0_percent(pings_per_ens=pings_per_ens, pd0_beam_num=i) # Convert to percent and reorder beams

            if ens.IsRangeTracking:
                for i in range(nslantbeams):
                    varname = "RTR%d" % (i+1)
                    varobj = self.cdf_file.variables[varname]
                    varobj[self.netcdf_index] = ens.RangeTracking.Range[i]

                    varname = "RTSNR%d" % (i + 1)
                    varobj = self.cdf_file.variables[varname]
                    varobj[self.netcdf_index] = ens.RangeTracking.SNR[i]

                    varname = "RTAmp%d" % (i + 1)
                    varobj = self.cdf_file.variables[varname]
                    varobj[self.netcdf_index] = ens.RangeTracking.Amplitude[i]

                    varname = "RTCorr%d" % (i + 1)
                    varobj = self.cdf_file.variables[varname]
                    varobj[self.netcdf_index] = ens.RangeTracking.Correlation[i]

            varobj = self.cdf_file.variables['Rec']
            varobj[self.netcdf_index] = ens.EnsembleData.EnsembleNumber
            varobj = self.cdf_file.variables['Hdg']
            varobj[self.netcdf_index] = round(ens.AncillaryData.Heading * 100.0)    # Convert to hundredth of degree
            varobj = self.cdf_file.variables['Ptch']
            varobj[self.netcdf_index] = round(ens.AncillaryData.Pitch * 100.0)      # Convert to hundredth of degree
            varobj = self.cdf_file.variables['Roll']
            roll = 0
            if ens.AncillaryData.Roll > 90:
                roll = -1 * (180.0 - ens.AncillaryData.Roll)
            elif ens.AncillaryData.Roll < -90:
                roll = 180.0 + ens.AncillaryData.Roll
            else:
                roll = ens.AncillaryData.Roll
            varobj[self.netcdf_index] = round(roll * 100.0)                         # Convert to hundredth of degree
            #varobj = self.cdf_file.variables['HdgSTD']
            #varobj[self.netcdf_index] = ens_data['VLeader']['H/Hdg_Std_Dev']
            #varobj = self.cdf_file.variables['PtchSTD']
            #varobj[self.netcdf_index] = ens_data['VLeader']['P/Pitch_Std_Dev']
            #varobj = self.cdf_file.variables['RollSTD']
            #varobj[self.netcdf_index] = ens_data['VLeader']['R/Roll_Std_Dev']
            varobj = self.cdf_file.variables['Tx']
            varobj[self.netcdf_index] = ens.AncillaryData.WaterTemp
            varobj = self.cdf_file.variables['S']
            varobj[self.netcdf_index] = round(ens.AncillaryData.Salinity)
            #varobj = self.cdf_file.variables['xmitc']
            #varobj[self.netcdf_index] = ens_data['VLeader']['Xmit_Current']
            varobj = self.cdf_file.variables['voltage']
            varobj[self.netcdf_index] = ens.SystemSetup.Voltage
            varobj = self.cdf_file.variables['xmitv']
            varobj[self.netcdf_index] = ens.SystemSetup.XmtVoltage
            varobj = self.cdf_file.variables['Ambient_Temp']
            varobj[self.netcdf_index] = ens.AncillaryData.SystemTemp
            #varobj = self.cdf_file.variables['Pressure+']
            #varobj[self.netcdf_index] = ens_data['VLeader']['Pressure_(+)']
            #varobj = self.cdf_file.variables['Pressure-']
            #varobj[self.netcdf_index] = ens_data['VLeader']['Pressure_(-)']
            #varobj = self.cdf_file.variables['Attitude_Temp']
            #varobj[self.netcdf_index] = ens_data['VLeader']['Attitude_Temp']
            #varobj = self.cdf_file.variables['EWD1']
            #varobj[self.netcdf_index] = int(ens_data['VLeader']['Error_Status_Word_Low_16_bits_LSB'])
            #varobj = self.cdf_file.variables['EWD2']
            #varobj[self.netcdf_index] = int(ens_data['VLeader']['Error_Status_Word_Low_16_bits_MSB'])
            #varobj = self.cdf_file.variables['EWD3']
            #varobj[self.netcdf_index] = int(ens_data['VLeader']['Error_Status_Word_High_16_bits_LSB'])
            #varobj = self.cdf_file.variables['EWD4']
            #varobj[self.netcdf_index] = int(ens_data['VLeader']['Error_Status_Word_High_16_bits_MSB'])
            varobj = self.cdf_file.variables['Status']
            varobj[self.netcdf_index] = ens.EnsembleData.Status

            #if ens_data['FLeader']['Depth_sensor_available'] == 'Yes':
            #    varobj = self.cdf_file.variables['Pressure']
            #    varobj[netcdf_index] = ens_data['VLeader']['Pressure_deca-pascals']
            #    varobj = self.cdf_file.variables['PressVar']
            #    varobj[netcdf_index] = ens_data['VLeader']['Pressure_variance_deca-pascals']
            if ens.AncillaryData.Pressure > 0:
                varobj = self.cdf_file.variables['Pressure']
                varobj[self.netcdf_index] = int(round(0.0001 * ens.AncillaryData.Pressure))

            if ens.IsNmeaData:
                varobj = self.cdf_file.variables['Lat']
                varobj[self.netcdf_index] = ens.NmeaData.latitude

                varobj = self.cdf_file.variables['Lon']
                varobj[self.netcdf_index] = ens.NmeaData.longitude

            # add bottom track data write to cdf here
            if ens.IsBottomTrack:
                #if ens_data['BTData']['Mode'] == 0:
                #    varobj = self.cdf_file.variables['BTRmin']
                #    varobj[self.netcdf_index] = ens_data['BTData']['Ref_Layer_Min']
                #    varobj = self.cdf_file.variables['BTRnear']
                #    varobj[self.netcdf_index] = ens_data['BTData']['Ref_Layer_Near']
                #    varobj = self.cdf_file.variables['BTRfar']
                #    varobj[self.netcdf_index] = ens_data['BTData']['Ref_Layer_Far']

                #varnames = ('BTWe', 'BTWu', 'BTWv', 'BTWd')
                for i in range(nslantbeams):
                    varname = "BTR%d" % (i+1)
                    varobj = self.cdf_file.variables[varname]
                    varobj[self.netcdf_index] = ens.BottomTrack.pd0_range_cm(pd0_beam_num=i)
                    varname = "BTV%d" % (i+1)
                    varobj = self.cdf_file.variables[varname]
                    varobj[self.netcdf_index] = ens.BottomTrack.pd0_beam_vel_mm_per_sec(pd0_beam_num=i)
                    varname = "BTc%d" % (i+1)
                    varobj = self.cdf_file.variables[varname]
                    varobj[self.netcdf_index] = ens.BottomTrack.pd0_corr_counts(pd0_beam_num=i)
                    varname = "BTe%d" % (i+1)
                    varobj = self.cdf_file.variables[varname]
                    varobj[self.netcdf_index] = ens.BottomTrack.pd0_amp_counts(pd0_beam_num=i)
                    varname = "BTp%d" % (i+1)
                    varobj = self.cdf_file.variables[varname]
                    varobj[self.netcdf_index] = ens.BottomTrack.pd0_good_beam_percent(pd0_beam_num=i)
                    #varname = "BTRSSI%d" % (i+1)
                    #varobj = self.cdf_file.variables[varname]
                    #varobj[self.netcdf_index] = ens_data['BTData']['RSSI_Amp'][i]

                    #if ens_data['BTData']['Mode'] == 0:
                    #    varobj[self.netcdf_index] = ens_data['BTData']['Ref_Layer_Vel'][i]
                    #    varname = "BTRc%d" % (i+1)
                    #    varobj = self.cdf_file.variables[varname]
                    #    varobj[self.netcdf_index] = ens_data['BTData']['Ref_Layer_Corr'][i]
                    #    varname = "BTRi%d" % (i+1)
                    #    varobj = self.cdf_file.variables[varname]
                    #    varobj[self.netcdf_index] = ens_data['BTData']['Ref_Layer_Amp'][i]
                    #    varname = "BTRp%d" % (i+1)
                    #    varobj = self.cdf_file.variables[varname]
                    #    varobj[self.netcdf_index] = ens_data['BTData']['Ref_Layer_PGd'][i]

            if vert_ens:
                # Number of code repeats for converting correlation data
                num_repeats = 1
                if vert_ens.IsSystemSetup:
                    num_repeats = vert_ens.SystemSetup.WpRepeatN

                if vert_ens.EnsembleData.NumBins == ens.EnsembleData.NumBins:
                    varobj = self.cdf_file.variables['vel5']
                    varobj[self.netcdf_index, :] = vert_ens.BeamVelocity.pd0_mm_per_sec(pd0_beam_num=0)
                    varobj = self.cdf_file.variables['cor5']
                    varobj[self.netcdf_index, :] = vert_ens.Correlation.pd0_counts(num_repeat=num_repeats, pd0_beam_num=0)
                    varobj = self.cdf_file.variables['att5']
                    varobj[self.netcdf_index, :] = vert_ens.Amplitude.pd0_counts(pd0_beam_num=0)
                    if vert_ens.IsGoodBeam:
                        varobj = self.cdf_file.variables['PGd5']
                        varobj[self.netcdf_index, :] = vert_ens.GoodBeam.pd0_percent(pings_per_ens=vert_ens.EnsembleData.ActualPingCount, pd0_beam_num=0)
                    if vert_ens.IsRangeTracking:
                        varobj = self.cdf_file.variables['RTR5']
                        varobj[self.netcdf_index] = vert_ens.RangeTracking.Range[0]
                        varobj = self.cdf_file.variables['RTSNR5']
                        varobj[self.netcdf_index] = vert_ens.RangeTracking.SNR[0]
                        varobj = self.cdf_file.variables['RTAmp5']
                        varobj[self.netcdf_index] = vert_ens.RangeTracking.Amplitude[0]
                        varobj = self.cdf_file.variables['RTCorr5']
                        varobj[self.netcdf_index] = vert_ens.RangeTracking.Correlation[0]

            #if 'WaveParams' in ens_data:
            #    # we can get away with this because the key names and var names are the same
            #    for key in ens_data['WaveParams']:
            #        varobj = self.cdf_file.variables[key]
            #        varobj[self.netcdf_index] = ens_data['WaveParams'][key]

            #if 'WaveSeaSwell' in ens_data:
            #    # we can get away with this because the key names and var names are the same
            #    for key in ens_data['WaveSeaSwell']:
            #        varobj = self.cdf_file.variables[key]
            #        varobj[self.netcdf_index] = ens_data['WaveSeaSwell'][key]

            self.netcdf_index += 1

        elif ens_error == 'no ID':
            print('Stopping because ID tracking lost')
            self.cdf_file.close()

        # Increment the ensemble count
        self.ensemble_count += 1

        logging.debug("Completed Adding Ensemble to netCDF file: " + self.netcdf_file_path + " " + str(ens.EnsembleData.EnsembleNumber) + " " + str(self.ensemble_count))

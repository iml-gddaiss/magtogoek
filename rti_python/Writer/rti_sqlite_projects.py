from rti_python.Writer.rti_sql import RtiSQL
from rti_python.Ensemble import Ensemble
import logging
from datetime import datetime, date, time
from tqdm import tqdm
from pathlib import Path, PurePath
from rti_python.Utilities.read_binary_file import ReadBinaryFile
from rti_python.River.Transect import Transect


class RtiSqliteProjects:
    """
    This is used to create the database file and add ensembles to the database.
    This is not intended to playback of the file.

    Projects within the database are used to separate river transects, waves bursts
    or other data when collected at the same time.

    Revision A: Initial Setup
    Revision B: Added Transect Table

    """

    # File extension to use with this file
    FILE_EXT = '.rdb'

    def __init__(self, file_path='C:\\rti_capture\\project.rdb'):

        """
        Maintain projects in a database.  The project will have ensembles associated with it.
        :param file_path: Is using SQLite, set the SQLite database file name.
        """
        self.REVISION = "B"

        # Construct connection string for SQLite
        self.sql_conn_string = file_path
        self.is_sqlite = True
        self.file_path = file_path

        # Sql connection when doing batch inserts
        self.batch_sql = None
        self.batch_prj_id = 0
        self.batch_count = 0

        self.pbar = None

    def load_files(self, file_paths):
        """
        Load the files given.  This will go through the list of files
        and add all the data to the sqlite database file.

        :param file_paths: List of file paths to load.
        """
        if file_paths:

            # Create the tables in the database if they do not exist
            self.create_tables()

            for file in file_paths:
                reader = ReadBinaryFile()
                reader.ensemble_event += self.ens_handler               # Wait for ensembles
                reader.file_progress += self.file_progress_handler      # Monitor file progress

                # Get the file name and file path
                prj_name = Path(file).stem
                prj_path = file

                # Create the project from the file name
                self.add_prj_sql(str(prj_name), prj_path)

                # Begin the batch writing to the database
                self.begin_batch(str(prj_name))

                # Read the file for ensembles
                reader.playback(file)

                # End any remaining batch
                self.end_batch()

    def ens_handler(self, sender, ens):
        """
        Handle the incoming ensembles from the file playback.
        :param sender: NOT USED
        :param ens: Ensemble data.
        """
        self.add_ensemble(ens)

    def file_progress_handler(self, sender, bytes_read, total_size, file_name):
        """
        Monitor the file playback progress.
        :param sender: NOT USED
        :param total_size: Total size.
        :param bytes_read: Total Bytes read.
        :param file_name: File name being read..
        :return:
        """
        if self.pbar is None:
            self.pbar = tqdm(total=total_size)

        self.pbar.update(int(bytes_read))

    def add_prj_sql(self, prj_name, prj_file_path):
        """
        Add the given project name to the projects table.
        :param prj_name: Project name
        :param prj_file_path: Path for the project to find the raw data.
        :return: TRUE = Project added.  FALSE = Project already exists and could not add.
        """
        # Check if the project exist
        project_exist = self.check_project_exist(prj_name)

        if project_exist == 0:
            # Add project to database
            dt = datetime.now()
            sql = RtiSQL(self.sql_conn_string, is_sqlite=self.is_sqlite)

            # Postgres uses %s and sqlite uses ? in the query string
            query = 'INSERT INTO projects (name, path, created, modified, revision) VALUES (?,?,?,?,?);'
            sql.cursor.execute(query, [prj_name, prj_file_path, dt, dt, self.REVISION])

            # Get the index of the project
            result = sql.query('SELECT id FROM projects WHERE name = \'{0}\' LIMIT 1;'.format(prj_name))
            if not result:
                prj_idx = 0
            else:
                prj_idx = result[0][0]

            sql.conn.commit()
            logging.debug(prj_idx)
            sql.close()

            return prj_idx
        elif project_exist > 0:
            # Send a warning and make them give a new name
            return -1

    def check_project_exist(self, prj_name):
        """
        Check if the given project name exist in the projects table.
        :param prj_name: Project Name.
        :return: Project ID.  If the value is negative, then it does not exist.
        """
        idx = -1

        # Make connection
        try:
            sql = RtiSQL(self.sql_conn_string, is_sqlite=self.is_sqlite)
        except Exception as e:
            logging.error("Unable to connect to the database")
            return -1

        # Check if the project exists
        try:
            result = sql.query('SELECT id FROM projects WHERE name = \'{0}\' LIMIT 1;'.format(prj_name))

            # Check for a result
            if not result:
                idx = 0                     # No project found
            else:
                idx = result[0][0]          # Index found

        except Exception as e:
            logging.error("Unable to run query", e)
            sql.close()
            return -2

        # Close connection
        sql.close()

        return idx

    def get_all_projects(self):
        """
        Select all the projects from the database.
        :return: All the databases in the projects table.
        """
        result = None

        # Make connection
        try:
            sql = RtiSQL(self.sql_conn_string, is_sqlite=self.is_sqlite)
        except Exception as e:
            logging.error("Unable to connect to the database")
            return result

        # Get all projects
        try:
            result = sql.query('SELECT * FROM projects;')
        except Exception as e:
            logging.error("Unable to run query", e)
            return result

        # Close connection
        sql.close()

        return result

    def get_summary(self, prj_idx):
        """
        Get the project summary based on the project index given.
        :param prj_idx: Project Index.
        :return: JSON of project summary.
        """
        result = {}

        # Make connection
        try:
            sql = RtiSQL(self.sql_conn_string, is_sqlite=self.is_sqlite)
        except Exception as e:
            logging.error("Unable to connect to the database")
            return result

        # Get all projects
        try:
            sql_query_str = 'SELECT summary FROM projects WHERE id = {0};'.format(prj_idx)
            result = sql.query(sql_query_str)
        except Exception as e:
            logging.error("Unable to run query", e)
            return result

        # Close connection
        sql.close()

        return result

    def begin_batch(self, prj_name):
        # Make connection
        try:
            self.batch_sql = RtiSQL(self.sql_conn_string, is_sqlite=self.is_sqlite)
        except Exception as e:
            logging.error("Unable to connect to the database")

        # Get the index for the given project name
        prj_id = self.batch_sql.query('SELECT id FROM projects WHERE name=\'{0}\''.format(prj_name))
        self.batch_prj_id = prj_id[0][0]
        logging.debug("Batch Project ID: " + str(self.batch_prj_id))

    def end_batch(self):

        # Commit the batch
        self.batch_sql.commit()

        # Close connection
        #self.batch_sql.close()

        # Set the connection to none
        #self.batch_sql = None

    def add_summary(self, json_summary, project_id):
        """
        Add a file summary to a project.  This will set a JSON summary to the summary columan and
        modify the datetime for the project.
        :param json_summary: JSON summary of the data or file.
        :param project_id: Project ID to modify
        """
        if self.batch_sql is not None:
            try:
                # Postgres uses %s and sqlite uses ? in the query string
                query = 'UPDATE projects SET summary = ?, modified = ? WHERE id=?;'
                self.batch_sql.cursor.execute(query, [json_summary, datetime.now(), project_id])

            except Exception as ex:
                logging.error("Error adding summary to project.", ex)
                return

    def add_ensemble(self, ens, burst_num=0, is_batch_write=True):
        '''
        Add the ensemble to the database.
        :param ens: Ensemble to store data.
        :param burst_num: Burst number if a waves deployment.
        :param is_batch_write: If batch writing is not setup, then set to false so a connection can be made.
        :return: Ensemble index.
        '''
        ens_idx = 0

        # If you are not using batch writing for bulk writing,
        # then setup a connection
        if not self.batch_sql and not is_batch_write:
            # Make connection
            try:
                self.batch_sql = RtiSQL(self.sql_conn_string, is_sqlite=self.is_sqlite)
            except Exception as e:
                logging.error("Unable to connect to the database")

        if self.batch_sql is not None:
            # Ensemble and Ancillary dataset
            try:
                ens_idx = self.add_ensemble_ds(ens, burst_num)
            except Exception as ex:
                logging.error("Error adding Ensemble, Ancillary and System Setup Dataset to project.", ex)
                return ens_idx

            bin_size = None
            blank = None
            if ens.IsAncillaryData:
                bin_size = ens.AncillaryData.BinSize
                blank = ens.AncillaryData.FirstBinRange

            # Correlation
            try:
                if ens.IsCorrelation:
                    self.add_dataset("correlation",
                                     ens.Correlation.Correlation,
                                     ens.Correlation.num_elements,
                                     ens.Correlation.element_multiplier,
                                     ens_idx,
                                     bin_size,
                                     blank)
            except Exception as ex:
                logging.error("Error adding Correlation to project.", ex)

            # Amplitude
            try:
                if ens.IsAmplitude:
                    self.add_dataset("amplitude",
                                     ens.Amplitude.Amplitude,
                                     ens.Amplitude.num_elements,
                                     ens.Amplitude.element_multiplier,
                                     ens_idx,
                                     bin_size,
                                     blank)
            except Exception as ex:
                logging.error("Error adding Amplitude to project.", ex)

            # Beam Velocity
            try:
                if ens.IsBeamVelocity:
                    self.add_dataset("beamvelocity",
                                     ens.BeamVelocity.Velocities,
                                     ens.BeamVelocity.num_elements,
                                     ens.BeamVelocity.element_multiplier,
                                     ens_idx,
                                     bin_size,
                                     blank)
            except Exception as ex:
                logging.error("Error adding Beam Velocity to project.", ex)

            # Instrument Velocity
            try:
                if ens.IsInstrumentVelocity:
                    self.add_dataset("instrumentvelocity",
                                     ens.InstrumentVelocity.Velocities,
                                     ens.InstrumentVelocity.num_elements,
                                     ens.InstrumentVelocity.element_multiplier,
                                     ens_idx,
                                     bin_size,
                                     blank)
            except Exception as ex:
                logging.error("Error adding Instrument Velocity to project.", ex)

            # Earth Velocity
            try:
                if ens.IsEarthVelocity:
                    self.add_dataset("earthvelocity",
                                     ens.EarthVelocity.Velocities,
                                     ens.EarthVelocity.num_elements,
                                     ens.EarthVelocity.element_multiplier,
                                     ens_idx,
                                     bin_size,
                                     blank)

                    # Add the magnitude and direction table data
                    self.add_mag_dir(ens,
                                     ens_idx,
                                     bin_size,
                                     blank)
            except Exception as ex:
                logging.error("Error adding Earth Velocity to project.", ex)

            # Good Beam Ping
            try:
                if ens.IsGoodBeam:
                    self.add_dataset("goodbeamping",
                                     ens.GoodBeam.GoodBeam,
                                     ens.GoodBeam.num_elements,
                                     ens.GoodBeam.element_multiplier,
                                     ens_idx,
                                     bin_size,
                                     blank,
                                     bad_val=0)
            except Exception as ex:
                logging.error("Error adding Good Beam to project.", ex)

            # Good Earth Ping
            try:
                if ens.IsGoodEarth:
                    self.add_dataset("goodearthping",
                                     ens.GoodEarth.GoodEarth,
                                     ens.GoodEarth.num_elements,
                                     ens.GoodEarth.element_multiplier,
                                     ens_idx,
                                     bin_size,
                                     blank,
                                     bad_val=0)
            except Exception as ex:
                logging.error("Error adding Good Earth to project.", ex)

            # Bottom Track
            try:
                if ens.IsBottomTrack:
                    self.add_bottomtrack_ds(ens, ens_idx)
            except Exception as ex:
                logging.error("Error adding Bottom Track to project.", ex)

            # Range Tracking
            try:
                if ens.IsRangeTracking:
                    self.add_rangetracking_ds(ens, ens_idx)
            except Exception as ex:
                logging.error("Error adding Range Tracking to project.", ex)

            # NMEA
            try:
                if ens.IsNmeaData:
                    year = 2020
                    month = 1
                    day = 1
                    if ens.IsEnsembleData:
                        year = ens.EnsembleData.Year
                        month = ens.EnsembleData.Month
                        day = ens.EnsembleData.Day
                    self.add_nmea_ds(ens, ens_idx, year=year, month=month, day=day)
            except Exception as ex:
                logging.error("Error adding NMEA to project.", ex)

            # Return the index of the ensemble created
            return ens_idx

        else:
            logging.error("Batch import not started.  Please call begin_batch() first.")
            return ens_idx

    def add_ensemble_ds(self, ens, burst_num=0):
        """
        Add the Ensemble dataset to the database.
        :param ens: Ensemble data.
        :param burst_num: Burst Number if using bursting
        :return Return the index to ensemble in the db.
        """
        if not ens.IsEnsembleData or not ens.IsAncillaryData or not ens.IsSystemSetup:
            return

        # Get the average magnitude and direction
        avg_mag = 0.0
        avg_dir = 0.0
        if ens.IsEarthVelocity:
            avg_mag, avg_dir = ens.EarthVelocity.average_mag_dir()

        # Switch bool to an int
        is_upward_looking = 0
        if ens.AncillaryData.is_upward_facing():
            is_upward_looking = 1

        # Add line for each dataset type
        ens_query = "INSERT INTO ensembles (" \
                    "ensnum, " \
                    "numbins, " \
                    "numbeams, " \
                    "desiredpings, " \
                    "actualpings, " \
                    "status, " \
                    "datetime, " \
                    "serialnumber, " \
                    "firmware, " \
                    "subsystemCode, " \
                    "subsystemConfig, " \
                    'rangeFirstBin, ' \
                    'binSize, ' \
                    'firstPingTime, ' \
                    'lastPingTime, ' \
                    'heading, ' \
                    'pitch, ' \
                    'roll, ' \
                    'waterTemp, ' \
                    'sysTemp, ' \
                    'salinity, ' \
                    'pressure, ' \
                    'xdcrDepth, ' \
                    'sos, ' \
                    'rawMagFieldStrength,' \
                    'pitchGravityVector, ' \
                    'rollGravityVector, ' \
                    'verticalGravityVector, ' \
                    'BtSamplesPerSecond, ' \
                    'BtSystemFreqHz, ' \
                    'BtCPCE, ' \
                    'BtNCE, ' \
                    'BtRepeatN, ' \
                    'WpSamplesPerSecond, ' \
                    'WpSystemFreqHz, ' \
                    'WpCPCE, ' \
                    'WpNCE, ' \
                    'WpRepeatN, ' \
                    'WpLagSamples, ' \
                    'Voltage, ' \
                    'XmtVoltage, ' \
                    'BtBroadband, ' \
                    'BtLagLength, ' \
                    'BtNarrowband, ' \
                    'BtBeamMux, ' \
                    'WpBroadband, ' \
                    'WpLagLength, ' \
                    'WpTransmitBandwidth, ' \
                    'WpReceiveBandwidth, ' \
                    'AvgMagnitude, ' \
                    'AvgDirection, ' \
                    'isUpwardLooking, ' \
                    'burstNum, ' \
                    'project_id)' \
                    'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?); '

        self.batch_sql.cursor.execute(ens_query, (ens.EnsembleData.EnsembleNumber,
                                                  ens.EnsembleData.NumBins,
                                                  ens.EnsembleData.NumBeams,
                                                  ens.EnsembleData.DesiredPingCount,
                                                  ens.EnsembleData.ActualPingCount,
                                                  ens.EnsembleData.Status,
                                                  ens.EnsembleData.datetime(),
                                                  ens.EnsembleData.SerialNumber,
                                                  ens.EnsembleData.firmware_str(),
                                                  ens.EnsembleData.SysFirmwareSubsystemCode,
                                                  ens.EnsembleData.SubsystemConfig,
                                                  ens.AncillaryData.FirstBinRange,
                                                  ens.AncillaryData.BinSize,
                                                  ens.AncillaryData.FirstPingTime,
                                                  ens.AncillaryData.LastPingTime,
                                                  ens.AncillaryData.Heading,
                                                  ens.AncillaryData.Pitch,
                                                  ens.AncillaryData.Roll,
                                                  ens.AncillaryData.WaterTemp,
                                                  ens.AncillaryData.SystemTemp,
                                                  ens.AncillaryData.Salinity,
                                                  ens.AncillaryData.Pressure,
                                                  ens.AncillaryData.TransducerDepth,
                                                  ens.AncillaryData.SpeedOfSound,
                                                  ens.AncillaryData.RawMagFieldStrength,
                                                  ens.AncillaryData.PitchGravityVector,
                                                  ens.AncillaryData.RollGravityVector,
                                                  ens.AncillaryData.VerticalGravityVector,
                                                  ens.SystemSetup.BtSamplesPerSecond,
                                                  ens.SystemSetup.BtSystemFreqHz,
                                                  ens.SystemSetup.BtCPCE,
                                                  ens.SystemSetup.BtNCE,
                                                  ens.SystemSetup.BtRepeatN,
                                                  ens.SystemSetup.WpSamplesPerSecond,
                                                  ens.SystemSetup.WpSystemFreqHz,
                                                  ens.SystemSetup.WpCPCE,
                                                  ens.SystemSetup.WpNCE,
                                                  ens.SystemSetup.WpRepeatN,
                                                  ens.SystemSetup.WpLagSamples,
                                                  ens.SystemSetup.Voltage,
                                                  ens.SystemSetup.XmtVoltage,
                                                  ens.SystemSetup.BtBroadband,
                                                  ens.SystemSetup.BtLagLength,
                                                  ens.SystemSetup.BtNarrowband,
                                                  ens.SystemSetup.BtBeamMux,
                                                  ens.SystemSetup.WpBroadband,
                                                  ens.SystemSetup.WpLagLength,
                                                  ens.SystemSetup.WpTransmitBandwidth,
                                                  ens.SystemSetup.WpReceiveBandwidth,
                                                  avg_mag,
                                                  avg_dir,
                                                  is_upward_looking,
                                                  burst_num,
                                                  self.batch_prj_id))
        ens_idx = self.batch_sql.cursor.lastrowid
        #print("rti_projects:add_ensemble_ds() Ens Index: " + str(ens_idx))

        # Monitor how many inserts have been done so it does not get too big
        #self.batch_count += 1
        #if self.batch_count > 10:
        #    self.batch_sql.commit()
        #    self.batch_count = 0

        return ens_idx

    def add_bottomtrack_ds(self, ens, ens_idx):
        if not ens.IsBottomTrack:
            return

        query_range_label = ""
        query_range_val = ""
        query_snr_label = ""
        query_snr_val = ""
        query_amp_label = ""
        query_amp_val = ""
        query_corr_label = ""
        query_corr_val = ""
        query_beam_vel_label = ""
        query_beam_vel_val = ""
        query_beam_ping_label = ""
        query_beam_ping_val = ""
        query_instr_vel_label = ""
        query_instr_vel_val = ""
        query_instr_good_label = ""
        query_instr_good_val = ""
        query_earth_vel_label = ""
        query_earth_vel_val = ""
        query_earth_good_label = ""
        query_earth_good_val = ""
        query_snr_pc_label = ""
        query_snr_pc_val = ""
        query_amp_pc_label = ""
        query_amp_pc_val = ""
        query_vel_pc_label = ""
        query_vel_pc_val = ""
        query_noise_pc_label = ""
        query_noise_pc_val = ""
        query_corr_pc_label = ""
        query_corr_pc_val = ""

        for beam in range(int(ens.BottomTrack.NumBeams)):
            query_range_label += "rangeBeam{0}, ".format(beam)
            query_range_val += "{0}, ".format(ens.BottomTrack.Range[beam])

            query_snr_label += "snrBeam{0}, ".format(beam)
            query_snr_val += "{0}, ".format(ens.BottomTrack.SNR[beam])

            query_amp_label += "ampBeam{0}, ".format(beam)
            query_amp_val += "{0}, ".format(ens.BottomTrack.Amplitude[beam])

            query_corr_label += "corrBeam{0}, ".format(beam)
            query_corr_val += "{0}, ".format(ens.BottomTrack.Correlation[beam])

            query_beam_vel_label += "beamVelBeam{0}, ".format(beam)
            query_beam_vel_val += "{0}, ".format(ens.BottomTrack.BeamVelocity[beam])

            query_beam_ping_label += "beamGoodBeam{0}, ".format(beam)
            query_beam_ping_val += "{0}, ".format(int(ens.BottomTrack.BeamGood[beam]))

            query_instr_vel_label += "instrVelBeam{0}, ".format(beam)
            query_instr_vel_val += "{0}, ".format(ens.BottomTrack.InstrumentVelocity[beam])

            query_instr_good_label += "instrGoodBeam{0}, ".format(beam)
            query_instr_good_val += "{0}, ".format(int(ens.BottomTrack.InstrumentGood[beam]))

            query_earth_vel_label += "earthVelBeam{0}, ".format(beam)
            query_earth_vel_val += "{0}, ".format(ens.BottomTrack.EarthVelocity[beam])

            query_earth_good_label += "earthGoodBeam{0}, ".format(beam)
            query_earth_good_val += "{0}, ".format(int(ens.BottomTrack.EarthGood[beam]))

            query_snr_pc_label += "snrPulseCoherentBeam{0}, ".format(beam)
            query_snr_pc_val += "{0}, ".format(ens.BottomTrack.SNR_PulseCoherent[beam])

            query_amp_pc_label += "ampPulseCoherentBeam{0}, ".format(beam)
            query_amp_pc_val += "{0}, ".format(ens.BottomTrack.Amp_PulseCoherent[beam])

            query_vel_pc_label += "velPulseCoherentBeam{0}, ".format(beam)
            query_vel_pc_val += "{0}, ".format(ens.BottomTrack.Vel_PulseCoherent[beam])

            query_noise_pc_label += "noisePulseCoherentBeam{0}, ".format(beam)
            query_noise_pc_val += "{0}, ".format(ens.BottomTrack.Noise_PulseCoherent[beam])

            query_corr_pc_label += "corrPulseCoherentBeam{0}, ".format(beam)
            query_corr_pc_val += "{0}, ".format(ens.BottomTrack.Corr_PulseCoherent[beam])

        query_range_label = query_range_label[:-2]              # Remove final comma
        query_range_val = query_range_val[:-2]                  # Remove final comma
        query_snr_label = query_snr_label[:-2]                  # Remove final comma
        query_snr_val = query_snr_val[:-2]                      # Remove final comma
        query_amp_label = query_amp_label[:-2]                  # Remove final comma
        query_amp_val = query_amp_val[:-2]                      # Remove final comma
        query_corr_label = query_corr_label[:-2]                # Remove final comma
        query_corr_val = query_corr_val[:-2]                    # Remove final comma
        query_beam_vel_label = query_beam_vel_label[:-2]        # Remove final comma
        query_beam_vel_val = query_beam_vel_val[:-2]            # Remove final comma
        query_beam_ping_label = query_beam_ping_label[:-2]      # Remove final comma
        query_beam_ping_val = query_beam_ping_val[:-2]          # Remove final comma
        query_instr_vel_label = query_instr_vel_label[:-2]      # Remove final comma
        query_instr_vel_val = query_instr_vel_val[:-2]          # Remove final comma
        query_instr_good_label = query_instr_good_label[:-2]    # Remove final comma
        query_instr_good_val = query_instr_good_val[:-2]        # Remove final comma
        query_earth_vel_label = query_earth_vel_label[:-2]      # Remove final comma
        query_earth_vel_val = query_earth_vel_val[:-2]          # Remove final comma
        query_earth_good_label = query_earth_good_label[:-2]    # Remove final comma
        query_earth_good_val = query_earth_good_val[:-2]        # Remove final comma
        query_snr_pc_label = query_snr_pc_label[:-2]            # Remove final comma
        query_snr_pc_val = query_snr_pc_val[:-2]                # Remove final comma
        query_amp_pc_label = query_amp_pc_label[:-2]            # Remove final comma
        query_amp_pc_val = query_amp_pc_val[:-2]                # Remove final comma
        query_vel_pc_label = query_vel_pc_label[:-2]            # Remove final comma
        query_vel_pc_val = query_vel_pc_val[:-2]                # Remove final comma
        query_noise_pc_label = query_noise_pc_label[:-2]        # Remove final comma
        query_noise_pc_val = query_noise_pc_val[:-2]            # Remove final comma
        query_corr_pc_label = query_corr_pc_label[:-2]          # Remove final comma
        query_corr_pc_val = query_corr_pc_val[:-2]              # Remove final comma

        # Add line for each dataset type
        query = "INSERT INTO bottomtrack (" \
                'ensIndex, ' \
                'firstPingTime, ' \
                'lastPingTime, ' \
                'heading, ' \
                'pitch, ' \
                'roll, ' \
                'waterTemp, ' \
                'salinity, ' \
                'xdcrDepth, ' \
                'pressure, ' \
                'sos, ' \
                'status, ' \
                'numBeams, ' \
                'pingCount, ' \
                '{0}, ' \
                '{1}, ' \
                '{2}, ' \
                '{3}, ' \
                '{4}, ' \
                '{5}, ' \
                '{6}, ' \
                '{7}, ' \
                '{8}, ' \
                '{9}, ' \
                '{10}, ' \
                '{11}, ' \
                '{12}, ' \
                '{13}, ' \
                '{14}, ' \
                'vesselSpeed, ' \
                'vesselDirection, ' \
                'avgRange)' \
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?," \
                "{15}," \
                "{16}," \
                "{17}," \
                "{18}," \
                "{19}," \
                "{20}," \
                "{21}," \
                "{22}," \
                "{23}," \
                "{24}," \
                "{25}," \
                "{26}," \
                "{27}," \
                "{28}," \
                "{29}," \
                "?," \
                "?," \
                "?" \
                ");".format(query_range_label,
                                 query_snr_label,
                                 query_amp_label,
                                 query_corr_label,
                                 query_beam_vel_label,
                                 query_beam_ping_label,
                                 query_instr_vel_label,
                                 query_instr_good_label,
                                 query_earth_vel_label,
                                 query_earth_good_label,
                                 query_snr_pc_label,
                                 query_amp_pc_label,
                                 query_vel_pc_label,
                                 query_noise_pc_label,
                                 query_corr_pc_label,
                                 query_range_val,
                                 query_snr_val,
                                 query_amp_val,
                                 query_corr_val,
                                 query_beam_vel_val,
                                 query_beam_ping_val,
                                 query_instr_vel_val,
                                 query_instr_good_val,
                                 query_earth_vel_val,
                                 query_earth_good_val,
                                 query_snr_pc_val,
                                 query_amp_pc_val,
                                 query_vel_pc_val,
                                 query_noise_pc_val,
                                 query_corr_pc_val)

        self.batch_sql.cursor.execute(query, (ens_idx,
                                              ens.BottomTrack.FirstPingTime,
                                              ens.BottomTrack.LastPingTime,
                                              ens.BottomTrack.Heading,
                                              ens.BottomTrack.Pitch,
                                              ens.BottomTrack.Roll,
                                              ens.BottomTrack.WaterTemp,
                                              ens.BottomTrack.Salinity,
                                              ens.BottomTrack.TransducerDepth,
                                              ens.BottomTrack.Pressure,
                                              ens.BottomTrack.SpeedOfSound,
                                              int(ens.BottomTrack.Status),
                                              int(ens.BottomTrack.NumBeams),
                                              int(ens.BottomTrack.ActualPingCount),
                                              ens.BottomTrack.get_vessel_speed(),
                                              ens.BottomTrack.get_vessel_direction(),
                                              ens.BottomTrack.avg_range()))

        # Monitor how many inserts have been done so it does not get too big
        #self.batch_count += 1
        #if self.batch_count > 10:
        #    self.batch_sql.commit()
        #    self.batch_count = 0

    def add_rangetracking_ds(self, ens, ens_idx):
        if not ens.IsRangeTracking:
            return

        query_range_label = ""
        query_range_val = ""
        query_snr_label = ""
        query_snr_val = ""
        query_pings_label = ""
        query_pings_val = ""
        query_amp_label = ""
        query_amp_val = ""
        query_corr_label = ""
        query_corr_val = ""
        query_beam_vel_label = ""
        query_beam_vel_val = ""
        query_instr_vel_label = ""
        query_instr_vel_val = ""
        query_earth_vel_label = ""
        query_earth_vel_val = ""

        for beam in range(int(ens.RangeTracking.NumBeams)):
            query_range_label += "rangeBeam{0}, ".format(beam)
            query_range_val += "{0}, ".format(ens.RangeTracking.Range[beam])

            query_snr_label += "snrBeam{0}, ".format(beam)
            query_snr_val += "{0}, ".format(ens.RangeTracking.SNR[beam])

            query_amp_label += "ampBeam{0}, ".format(beam)
            query_amp_val += "{0}, ".format(ens.RangeTracking.Amplitude[beam])

            query_corr_label += "corrBeam{0}, ".format(beam)
            query_corr_val += "{0}, ".format(ens.RangeTracking.Correlation[beam])

            query_beam_vel_label += "beamVelBeam{0}, ".format(beam)
            query_beam_vel_val += "{0}, ".format(ens.RangeTracking.BeamVelocity[beam])

            query_pings_label += "pingsBeam{0}, ".format(beam)
            query_pings_val += "{0}, ".format(int(ens.RangeTracking.Pings[beam]))

            query_instr_vel_label += "instrVelBeam{0}, ".format(beam)
            query_instr_vel_val += "{0}, ".format(ens.RangeTracking.InstrumentVelocity[beam])

            query_earth_vel_label += "earthVelBeam{0}, ".format(beam)
            query_earth_vel_val += "{0}, ".format(ens.RangeTracking.EarthVelocity[beam])

        query_range_label = query_range_label[:-2]              # Remove final comma
        query_range_val = query_range_val[:-2]                  # Remove final comma
        query_snr_label = query_snr_label[:-2]                  # Remove final comma
        query_snr_val = query_snr_val[:-2]                      # Remove final comma
        query_amp_label = query_amp_label[:-2]                  # Remove final comma
        query_amp_val = query_amp_val[:-2]                      # Remove final comma
        query_corr_label = query_corr_label[:-2]                # Remove final comma
        query_corr_val = query_corr_val[:-2]                    # Remove final comma
        query_beam_vel_label = query_beam_vel_label[:-2]        # Remove final comma
        query_beam_vel_val = query_beam_vel_val[:-2]            # Remove final comma
        query_pings_label = query_pings_label[:-2]          # Remove final comma
        query_pings_val = query_pings_val[:-2]              # Remove final comma
        query_instr_vel_label = query_instr_vel_label[:-2]      # Remove final comma
        query_instr_vel_val = query_instr_vel_val[:-2]          # Remove final comma
        query_earth_vel_label = query_earth_vel_label[:-2]      # Remove final comma
        query_earth_vel_val = query_earth_vel_val[:-2]          # Remove final comma

        # Add line for each dataset type
        query = "INSERT INTO rangetracking (" \
                'ensIndex, ' \
                'numBeams, ' \
                '{0}, ' \
                '{1}, ' \
                '{2}, ' \
                '{3}, ' \
                '{4}, ' \
                '{5}, ' \
                '{6}, ' \
                '{7}) ' \
                "VALUES(?,?," \
                "{8}," \
                "{9}," \
                "{10}," \
                "{11}," \
                "{12}," \
                "{13}," \
                "{14}," \
                "{15}" \
                ");".format(query_range_label,
                                 query_snr_label,
                                 query_amp_label,
                                 query_corr_label,
                                 query_beam_vel_label,
                                 query_pings_label,
                                 query_instr_vel_label,
                                 query_earth_vel_label,
                                 query_range_val,
                                 query_snr_val,
                                 query_amp_val,
                                 query_corr_val,
                                 query_beam_vel_val,
                                 query_pings_val,
                                 query_instr_vel_val,
                                 query_earth_vel_val)

        self.batch_sql.cursor.execute(query, (ens_idx,
                                              int(ens.RangeTracking.NumBeams)))

        # Monitor how many inserts have been done so it does not get too big
        #self.batch_count += 1
        #if self.batch_count > 10:
        #    self.batch_sql.commit()
        #    self.batch_count = 0

    def add_nmea_ds(self, ens, ens_idx, year=2017, month=1, day=1):
        """
        Add the NMEA dataset to the database.
        """
        if not ens.IsNmeaData:
            return

        # GPS DateTime
        ens_date = date(year, month, day)
        gps_time = ens.NmeaData.datetime
        if ens_date and gps_time:
            gps_datetime = datetime.combine(ens_date, gps_time)
        else:
            gps_datetime = ens.NmeaData.datetime

        # Combine all the sentences into a long string
        nmea_sent = ""
        for sent in ens.NmeaData.nmea_sentences:
            nmea_sent = nmea_sent + sent

        # Set null if does not exist
        gga = str(ens.NmeaData.GPGGA)
        if ens.NmeaData.GPGGA is None:
            gga = None

        vtg = str(ens.NmeaData.GPVTG)
        if ens.NmeaData.GPVTG is None:
            vtg = None

        rmc = str(ens.NmeaData.GPRMC)
        if ens.NmeaData.GPRMC is None:
            rmc = None

        gll = str(ens.NmeaData.GPGLL)
        if ens.NmeaData.GPGLL is None:
            gll = None

        gsv = str(ens.NmeaData.GPGSV)
        if ens.NmeaData.GPGSV is None:
            gsv = None

        gsa = str(ens.NmeaData.GPGSA)
        if ens.NmeaData.GPGSA is None:
            gsa = None

        hdt = str(ens.NmeaData.GPHDT)
        if ens.NmeaData.GPHDT is None:
            hdt = None

        hdg = str(ens.NmeaData.GPHDG)
        if ens.NmeaData.GPHDG is None:
            hdg = None

        # Add line for each dataset type
        query = "INSERT INTO nmea (" \
                "ensIndex, " \
                "nmea, " \
                "GPGGA, " \
                "GPVTG, " \
                "GPRMC, " \
                "GPGLL, " \
                "GPGSV, " \
                "GPGSA, " \
                "GPHDT, " \
                "GPHDG, " \
                "latitude, " \
                "longitude, "\
                "speed_knots, " \
                "heading, " \
                "datetime) " \
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);"
        #print(query)

        self.batch_sql.cursor.execute(query, (ens_idx,
                                              nmea_sent,
                                              gga,
                                              vtg,
                                              rmc,
                                              gll,
                                              gsv,
                                              gsa,
                                              hdt,
                                              hdg,
                                              float(ens.NmeaData.latitude),
                                              float(ens.NmeaData.longitude),
                                              float(ens.NmeaData.speed_knots),
                                              float(ens.NmeaData.heading),
                                              gps_datetime))

        # Monitor how many inserts have been done so it does not get too big
        #self.batch_count += 1
        #if self.batch_count > 10:
        #    self.batch_sql.commit()
        #    self.batch_count = 0

        return ens_idx

    def add_dataset(self, table, data, num_elements, element_multiplier, ens_idx, bin_size, blank, bad_val=Ensemble.Ensemble.BadVelocity):
        """
        Add a dataset to the database.  Give the table name, data, number of beams and bins and the ensemble index.
        :param table: Table name as a string.
        :param data: 2D Array of the data.
        :param num_elements: Number of bins.
        :param element_multiplier: Number of beams.
        :param ens_idx: Ensemble index in Ensembles table.
        :param bad_val: If a value is bad or missing, replace it with this value.
        """

        # Vertical beam data
        if element_multiplier == 1:
            for bin_num in range(num_elements):
                val0 = data[bin_num][0]

                # If values are given, calculate bin depth
                bin_depth = bin_num
                if blank and bin_size:
                    bin_depth = blank + (bin_size * bin_num)

                query = "INSERT INTO {0} (" \
                        "ensIndex, " \
                        "bin, " \
                        "binDepth, " \
                        "beam0) " \
                        "VALUES ( ?, ?, ?, ?);".format(table)
                self.batch_sql.cursor.execute(query, (ens_idx, bin_num, bin_depth, val0))

        # 2 Beam data
        elif element_multiplier == 2:
            for bin_num in range(num_elements):
                val0 = data[bin_num][0]
                val1 = data[bin_num][1]

                # If values are given, calculate bin depth
                bin_depth = bin_num
                if blank and bin_size:
                    bin_depth = blank + (bin_size * bin_num)

                query = "INSERT INTO {0} (" \
                        "ensIndex, " \
                        "bin, " \
                        "binDepth, " \
                        "beam0, " \
                        "beam1) " \
                        "VALUES ( ?, ?, ?, ?, ?);".format(table)
                self.batch_sql.cursor.execute(query, (ens_idx, bin_num, bin_depth, val0, val1))

        # 3 Beam data
        elif element_multiplier == 3:
            for bin_num in range(num_elements):
                val0 = data[bin_num][0]
                val1 = data[bin_num][1]
                val2 = data[bin_num][2]

                # If values are given, calculate bin depth
                bin_depth = bin_num
                if blank and bin_size:
                    bin_depth = blank + (bin_size * bin_num)

                query = "INSERT INTO {0} (" \
                        "ensIndex, " \
                        "bin, " \
                        "binDepth, " \
                        "beam0, " \
                        "beam1, " \
                        "beam2) " \
                        "VALUES ( ?, ?, ?, ?, ?, ?);".format(table)
                self.batch_sql.cursor.execute(query, (ens_idx, bin_num, bin_depth, val0, val1, val2))

        # 4 Beam data
        elif element_multiplier == 4:
            for bin_num in range(num_elements):
                val0 = data[bin_num][0]
                val1 = data[bin_num][1]
                val2 = data[bin_num][2]
                val3 = data[bin_num][3]

                # If values are given, calculate bin depth
                bin_depth = bin_num
                if blank and bin_size:
                    bin_depth = blank + (bin_size * bin_num)

                query = "INSERT INTO {0} (" \
                        "ensIndex, " \
                        "bin, " \
                        "binDepth, " \
                        "beam0, " \
                        "beam1, " \
                        "beam2, " \
                        "beam3) " \
                        "VALUES ( ?, ?, ?, ?, ?, ?, ?);".format(table)
                self.batch_sql.cursor.execute(query, (ens_idx, bin_num, bin_depth, val0, val1, val2, val3))

    def add_mag_dir(self, ens, ens_idx, bin_size, blank):
        if ens.IsEarthVelocity and ens.EarthVelocity.num_elements >= 3:

            # Create a temp to hold to original vectors before ship speed removed
            raw_mags = ens.EarthVelocity.Magnitude
            raw_dirs = ens.EarthVelocity.Direction

            if ens.IsBottomTrack:
                # Get the bottom track earth velocity to remove the ship speed
                bt_east = ens.BottomTrack.EarthVelocity[0]
                bt_north = ens.BottomTrack.EarthVelocity[1]
                bt_vert = ens.BottomTrack.EarthVelocity[2]

                # Remove the ship speed
                # This will also regenerate the velocity vectors
                ens.EarthVelocity.remove_vessel_speed(bt_east=bt_east, bt_north=bt_north, bt_vert=bt_vert)

            for bin_num in range(ens.EarthVelocity.num_elements):
                # If values are given, calculate bin depth
                bin_depth = bin_num
                if blank and bin_size:
                    bin_depth = blank + (bin_size * bin_num)

                raw_mag = raw_mags[bin_num]
                raw_dir = raw_dirs[bin_num]
                removed_mag = ens.EarthVelocity.Magnitude[bin_num]
                removed_dir = ens.EarthVelocity.Direction[bin_num]
                query = "INSERT INTO {0} (" \
                        "ensIndex, " \
                        "bin, " \
                        "binDepth, " \
                        "rawMag, " \
                        "rawDir, " \
                        "mag, " \
                        "dir) " \
                        "VALUES ( ?, ?, ?, ?, ?, ?, ?);".format("earthMagDir")
                self.batch_sql.cursor.execute(query, (ens_idx, bin_num, bin_depth, raw_mag, raw_dir, removed_mag, removed_dir))

    def add_transect(self, transect: Transect):
        """
        Add a transect into the db file.
        :param transect: Transect information
        """
        try:
            sql = RtiSQL(self.sql_conn_string, is_sqlite=self.is_sqlite)
            # Postgres uses %s and sqlite uses ? in the query string
            query = 'UPDATE projects SET summary = ?, modified = ? WHERE id=?;'
            sql.execute(query, [json_summary, datetime.now(), project_id])

        except Exception as ex:
            logging.error("Error adding summary to project.", ex)
            return

    def create_tables(self):
        logging.debug("Creating Tables in Database")

        try:
            sql = RtiSQL(self.sql_conn_string, is_sqlite=self.is_sqlite)
        except Exception as e:
            logging.error("Unable to connect to the database")

        auto_increment_str = "INTEGER"

        # Check if the connection is made
        if not sql.cursor:
            logging.error("Database connection not made yet.")
            return

        # Project
        sql.cursor.execute('CREATE TABLE IF NOT EXISTS projects (id ' + auto_increment_str + ' PRIMARY KEY,' 
                            'name text NOT NULL, '
                            'path text,'
                            'prjType text, '
                            'meta json,'
                            'summary json,'
                            'location json, '
                            'adcpConfig json, '
                            'prjConfig json, '
                            'created timestamp, '
                            'modified timestamp,'
                            'revision text);')
        logging.debug("Projects table created")

        # Ensemble Tables
        # Ensemble
        sql.cursor.execute('CREATE TABLE IF NOT EXISTS ensembles (id ' + auto_increment_str + ' PRIMARY KEY, '
                            'ensNum integer NOT NULL, '
                            'numBins integer, '
                            'numBeams integer, '
                            'desiredPings integer, '
                            'actualPings integer, '
                            'status integer, '
                            'dateTime timestamp, '
                            'serialNumber text, '
                            'firmware text,'
                            'subsystemCode character,'
                            'subsystemConfig integer, '
                            'rangeFirstBin real, '
                            'binSize real, '
                            'firstPingTime real, '
                            'lastPingTime real, '
                            'heading real, '
                            'pitch real, '
                            'roll real, '
                            'waterTemp real, '
                            'sysTemp real, '
                            'salinity real, '
                            'pressure real, '
                            'xdcrDepth real, '
                            'sos real, '
                            'rawMagFieldStrength real,'
                            'pitchGravityVector real, '
                            'rollGravityVector real, '
                            'verticalGravityVector real, '
                            'BtSamplesPerSecond real, '
                            'BtSystemFreqHz real, '
                            'BtCPCE real, '
                            'BtNCE real, '
                            'BtRepeatN real, '
                            'WpSamplesPerSecond real, '
                            'WpSystemFreqHz real, '
                            'WpCPCE real, '
                            'WpNCE real, '
                            'WpRepeatN real, '
                            'WpLagSamples real, '
                            'Voltage real, '
                            'XmtVoltage real, '
                            'BtBroadband real, '
                            'BtLagLength real, '
                            'BtNarrowband real, '
                            'BtBeamMux real, '
                            'WpBroadband real, '
                            'WpLagLength real, '
                            'WpTransmitBandwidth real, '
                            'WpReceiveBandwidth real, '
                            'AvgMagnitude real,'
                            'AvgDirection real,'
                            'burstNum integer, '
                            'isUpwardLooking boolean, '
                            'project_id integer, '
                            'meta json);')
        logging.debug("Ensemble Table created")

        # Bottom Track
        sql.cursor.execute('CREATE TABLE IF NOT EXISTS bottomtrack (id ' + auto_increment_str + ' PRIMARY KEY,'
                            'ensIndex integer NOT NULL, '
                            'firstPingTime real, '
                            'lastPingTime real, '
                            'heading real, '
                            'pitch real, '
                            'roll real, '
                            'waterTemp real, '
                            'salinity real, '
                            'xdcrDepth real, '
                            'pressure real, '
                            'sos real, '
                            'status integer, '
                            'numBeams integer, '
                            'pingCount integer, '
                            'rangeBeam0 real, '
                            'rangeBeam1 real, '
                            'rangeBeam2 real, '
                            'rangeBeam3 real, '
                            'snrBeam0 real, '
                            'snrBeam1 real, '
                            'snrBeam2 real, '
                            'snrBeam3 real, '
                            'ampBeam0 real, '
                            'ampBeam1 real, '
                            'ampBeam2 real, '
                            'ampBeam3 real, '
                            'corrBeam0 real, '
                            'corrBeam1 real, '
                            'corrBeam2 real, '
                            'corrBeam3 real, '
                            'beamVelBeam0 real, '
                            'beamVelBeam1 real, '
                            'beamVelBeam2 real, '
                            'beamVelBeam3 real, '
                            'beamGoodBeam0 integer, '
                            'beamGoodBeam1 integer, '
                            'beamGoodBeam2 integer, '
                            'beamGoodBeam3 integer, '
                            'instrVelBeam0 real, '
                            'instrVelBeam1 real, '
                            'instrVelBeam2 real, '
                            'instrVelBeam3 real, '
                            'instrGoodBeam0 integer, '
                            'instrGoodBeam1 integer, '
                            'instrGoodBeam2 integer, '
                            'instrGoodBeam3 integer, '
                            'earthVelBeam0 real, '
                            'earthVelBeam1 real, '
                            'earthVelBeam2 real, '
                            'earthVelBeam3 real, '
                            'earthGoodBeam0 integer, '
                            'earthGoodBeam1 integer, '
                            'earthGoodBeam2 integer, '
                            'earthGoodBeam3 integer, '
                            'snrPulseCoherentBeam0 real, '
                            'snrPulseCoherentBeam1 real, '
                            'snrPulseCoherentBeam2 real, '
                            'snrPulseCoherentBeam3 real, '
                            'ampPulseCoherentBeam0 real, '
                            'ampPulseCoherentBeam1 real, '
                            'ampPulseCoherentBeam2 real, '
                            'ampPulseCoherentBeam3 real, '
                            'velPulseCoherentBeam0 real, '
                            'velPulseCoherentBeam1 real, '
                            'velPulseCoherentBeam2 real, '
                            'velPulseCoherentBeam3 real, '
                            'noisePulseCoherentBeam0 real, '
                            'noisePulseCoherentBeam1 real, '
                            'noisePulseCoherentBeam2 real, '
                            'noisePulseCoherentBeam3 real, '
                            'corrPulseCoherentBeam0 real, '
                            'corrPulseCoherentBeam1 real, '
                            'corrPulseCoherentBeam2 real, '
                            'corrPulseCoherentBeam3 real, '
                            'vesselSpeed real, '
                            'vesselDirection real, '
                            'avgRange real, '
                            'meta json);')
        logging.debug("Bottom Track table created")

        # Range Track
        sql.cursor.execute('CREATE TABLE IF NOT EXISTS rangetracking (id ' + auto_increment_str + ' PRIMARY KEY,'
                            'ensIndex integer NOT NULL, '
                            'numBeams integer, '
                            'snrBeam0 real, '
                            'snrBeam1 real, '
                            'snrBeam2 real, '
                            'snrBeam3 real, '
                            'rangeBeam0 real, '
                            'rangeBeam1 real, '
                            'rangeBeam2 real, '
                            'rangeBeam3 real, '
                            'pingsBeam0 integer, '
                            'pingsBeam1 integer, '
                            'pingsBeam2 integer, '
                            'pingsBeam3 integer, '
                            'ampBeam0 real, '
                            'ampBeam1 real, '
                            'ampBeam2 real, '
                            'ampBeam3 real, '
                            'corrBeam0 real, '
                            'corrBeam1 real, '
                            'corrBeam2 real, '
                            'corrBeam3 real, '
                            'beamVelBeam0 real, '
                            'beamVelBeam1 real, '
                            'beamVelBeam2 real, '
                            'beamVelBeam3 real, '
                            'instrVelBeam0 real, '
                            'instrVelBeam1 real, '
                            'instrVelBeam2 real, '
                            'instrVelBeam3 real, '
                            'earthVelBeam0 real, '
                            'earthVelBeam1 real, '
                            'earthVelBeam2 real, '
                            'earthVelBeam3 real, '
                            'meta json);')
        logging.debug("Range Tracking table created")

        # Beam Velocity
        query = 'CREATE TABLE IF NOT EXISTS beamVelocity (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'meta json,' \
                'bin integer NOT NULL, ' \
                'binDepth real, ' \
                'beam0 real, ' \
                'beam1 real, ' \
                'beam2 real, ' \
                'beam3 real);'
        sql.cursor.execute(query)
        logging.debug("Beam Velocity table created")

        # Instrument Velocity
        query = 'CREATE TABLE IF NOT EXISTS instrumentVelocity (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'meta json,' \
                'bin integer NOT NULL, ' \
                'binDepth real, ' \
                'beam0 real, ' \
                'beam1 real, ' \
                'beam2 real, ' \
                'beam3 real);'
        sql.cursor.execute(query)
        logging.debug("Instrument Velocity table created")

        # Earth Velocity
        query = 'CREATE TABLE IF NOT EXISTS earthVelocity (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'meta json,' \
                'bin integer NOT NULL, ' \
                'binDepth real, ' \
                'beam0 real, ' \
                'beam1 real, ' \
                'beam2 real, ' \
                'beam3 real);'
        sql.cursor.execute(query)
        logging.debug("Earth Velocity table created")

        # Amplitude
        query = 'CREATE TABLE IF NOT EXISTS amplitude (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'meta json,' \
                'bin integer NOT NULL, ' \
                'binDepth real, ' \
                'beam0 real, ' \
                'beam1 real, ' \
                'beam2 real, ' \
                'beam3 real);'
        sql.cursor.execute(query)
        logging.debug("Amplitude table created")

        # Correlation
        query = 'CREATE TABLE IF NOT EXISTS correlation (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'meta json,' \
                'bin integer NOT NULL, ' \
                'binDepth real, ' \
                'beam0 real, ' \
                'beam1 real, ' \
                'beam2 real, ' \
                'beam3 real);'
        sql.cursor.execute(query)
        logging.debug("Correlation table created")

        # Good Beam Ping
        query = 'CREATE TABLE IF NOT EXISTS goodBeamPing (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'meta json,' \
                'bin integer NOT NULL, ' \
                'binDepth real, ' \
                'beam0 integer, ' \
                'beam1 integer, ' \
                'beam2 integer, ' \
                'beam3 integer);'
        sql.cursor.execute(query)
        logging.debug("Good Beam Ping table created")

        # Good Earth Ping
        query = 'CREATE TABLE IF NOT EXISTS goodEarthPing (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'meta json,' \
                'bin integer NOT NULL, ' \
                'binDepth real, ' \
                'beam0 integer, ' \
                'beam1 integer, ' \
                'beam2 integer, ' \
                'beam3 integer);'
        sql.cursor.execute(query)
        logging.debug("Good Earth Ping table created")

        # Water Profile Magnitude and Direction
        query = 'CREATE TABLE IF NOT EXISTS earthMagDir (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'meta json,' \
                'bin integer NOT NULL, ' \
                'binDepth real, ' \
                'mag real, ' \
                'dir real, ' \
                'rawMag real, ' \
                'rawDir real);'
        sql.cursor.execute(query)
        logging.debug("Good Earth Ping table created")

        # NMEA
        # Use Decimal(9,6) for Longitude and Decimal(8,6) for latitude to prevent rounding issues
        query = 'CREATE TABLE IF NOT EXISTS nmea (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'nmea text, ' \
                'GPGGA text, ' \
                'GPVTG text,' \
                'GPRMC text, ' \
                'GPRMF text, ' \
                'GPGLL text, ' \
                'GPGSV text, ' \
                'GPGSA text, ' \
                'GPHDT text,' \
                'GPHDG text,' \
                'latitude Decimal(8,6), ' \
                'longitude Decimal(9,6), ' \
                'speed_knots real, ' \
                'heading real, ' \
                'meta json,' \
                'datetime timestamp);'
        sql.cursor.execute(query)
        logging.debug("NMEA table created")

        # Project
        sql.cursor.execute('CREATE TABLE IF NOT EXISTS transects (id ' + auto_increment_str + ' PRIMARY KEY,' 
                            'siteName text, '
                            'stationNumber text,'
                            'location text, '
                            'party text,'
                            'boat text,'
                            'measurementNumber text, '
                            'comments text, '
                            'xdcrDepth real, '
                            'blankDepth real, '
                            'salinity real, '
                            'magDeclination real, '
                            'compassOffset real, '
                            'gpsXOffset real, '
                            'gpsYOffset real, '
                            'gpsConnected text, '
                            'trackReference text, '
                            'depthReference text, '
                            'headingSource text, '
                            'coordinateSystem text, '
                            'startEdge text, '
                            'leftEdgeDistance real, '
                            'leftEdgeMethod text, '
                            'rightEdgeDistance real, '
                            'rightEdgeMethod text, '
                            'autoEdgeProfile text, '
                            'showEdgeDialog boolean, '
                            'topFitType text, '
                            'topUseCells text, '
                            'bottomFitType text, '
                            'bottomUseCells text, '
                            'ratedDischarge real, '
                            'measurementQuality text, '
                            'previousSetTime timestamp, '
                            'measurementMethod text, '
                            'startEnsIndex integer, '
                            'stopEnsIndex integer, '
                            'created timestamp);')
        logging.debug("Transect table created")

        sql.cursor.execute("PRAGMA synchronous = OFF")

        logging.debug("Table Creation Complete")
        sql.conn.commit()
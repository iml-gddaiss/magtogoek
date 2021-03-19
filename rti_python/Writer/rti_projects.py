from rti_python.Writer.rti_sql import RtiSQL
from rti_python.Ensemble import Ensemble
from datetime import datetime, date, time
import logging


class RtiProjects:
    """
    Handle the projects.
    Create projects and add data to the projects.
    """

    def __init__(self,
                 host='localhost',
                 port=5432,
                 dbname='postgres',
                 user='user',
                 pw='pw'):

        """
        Maintain projects in a database.  The project will have ensembles associated with it.
        :param host: Host name/URL for MySQL server. Is using SQLite, set the SQLite database file name.
        :param dbname: Database name on MySQL server.
        :param user: User name to access MySQL server.
        :param pw: Password to access MySQL server.
        """

        self.is_sqlite = False

        # Construct connection string from MySQL/Postgres
        self.sql_conn_string = "host=\'{0}\' port=\'{1}\' dbname=\'{2}\' user=\'{3}\' password=\'{4}\'".format(host, port, dbname, user, pw)

        # Sql connection when doing batch inserts
        self.batch_sql = None
        self.batch_prj_id = 0
        self.batch_count = 0

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
            query = 'INSERT INTO projects (name, path, created, modified) VALUES (%s,%s,%s,%s) RETURNING ID;'
            sql.cursor.execute(query, (prj_name, prj_file_path, dt, dt))
            prj_idx = sql.cursor.fetchone()[0]

            sql.conn.commit()
            print(prj_idx)
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
            print("Unable to connect to the database")
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
            print("Unable to run query", e)
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
            print("Unable to connect to the database")
            return result

        # Get all projects
        try:
            result = sql.query('SELECT * FROM projects;')
        except Exception as e:
            print("Unable to run query", e)
            return result

        # Close connection
        sql.close()

        return result

    def begin_batch(self, prj_name):
        # Make connection
        try:
            self.batch_sql = RtiSQL(self.sql_conn_string, is_sqlite=self.is_sqlite)
        except Exception as e:
            print("Unable to connect to the database")

        # Get the index for the given project name
        self.batch_prj_id = self.batch_sql.query('SELECT id FROM projects WHERE name=\'{0}\''.format(prj_name))
        print("Project ID: " + str(self.batch_prj_id))

    def end_batch(self):

        # Commit the batch
        self.batch_sql.commit();

        # Close connection
        self.batch_sql.close()

        # Set the connection to none
        self.batch_sql = None

    def add_ensemble(self, ens, burst_num=0):
        '''
        Add the ensemble to the database.
        :param ens: Ensemble to store data.
        :param burst_num: Burst number if a waves deployment.
        :return:
        '''
        if self.batch_sql is not None:
            # Ensemble and Ancillary dataset
            try:
                ens_idx = self.add_ensemble_ds(ens, burst_num)
            except Exception as ex:
                print("Error adding Ensemble, Ancillary and System Setup Dataset to project.", ex)
                return

            # Correlation
            try:
                if ens.IsCorrelation:
                    self.add_dataset("correlation",
                                     ens.Correlation.Correlation,
                                     ens.Correlation.num_elements,
                                     ens.Correlation.element_multiplier,
                                     ens_idx)
            except Exception as ex:
                print("Error adding Correlation to project.", ex)

            # Amplitude
            try:
                if ens.IsAmplitude:
                    self.add_dataset("amplitude",
                                     ens.Amplitude.Amplitude,
                                     ens.Amplitude.num_elements,
                                     ens.Amplitude.element_multiplier,
                                     ens_idx)
            except Exception as ex:
                print("Error adding Amplitude to project.", ex)

            # Beam Velocity
            try:
                if ens.IsBeamVelocity:
                    self.add_dataset("beamvelocity",
                                     ens.Wt.Velocities,
                                     ens.Wt.num_elements,
                                     ens.Wt.element_multiplier,
                                     ens_idx)
            except Exception as ex:
                print("Error adding Beam Velocity to project.", ex)

            # Instrument Velocity
            try:
                if ens.IsInstrumentVelocity:
                    self.add_dataset("instrumentvelocity",
                                     ens.InstrumentVelocity.Velocities,
                                     ens.InstrumentVelocity.num_elements,
                                     ens.InstrumentVelocity.element_multiplier,
                                     ens_idx)
            except Exception as ex:
                print("Error adding Instrument Velocity to project.", ex)

            # Earth Velocity
            try:
                if ens.IsEarthVelocity:
                    self.add_dataset("earthvelocity",
                                     ens.EarthVelocity.Velocities,
                                     ens.EarthVelocity.num_elements,
                                     ens.EarthVelocity.element_multiplier,
                                     ens_idx)
            except Exception as ex:
                print("Error adding Earth Velocity to project.", ex)

            # Good Beam Ping
            try:
                if ens.IsGoodBeam:
                    self.add_dataset("goodbeamping",
                                     ens.GoodBeam.GoodBeam,
                                     ens.GoodBeam.num_elements,
                                     ens.GoodBeam.element_multiplier,
                                     ens_idx,
                                     bad_val=0)
            except Exception as ex:
                print("Error adding Good Beam to project.", ex)

            # Good Earth Ping
            try:
                if ens.IsGoodEarth:
                    self.add_dataset("goodearthping",
                                     ens.GoodEarth.GoodEarth,
                                     ens.GoodEarth.num_elements,
                                     ens.GoodEarth.element_multiplier,
                                     ens_idx,
                                     bad_val=0)
            except Exception as ex:
                print("Error adding Good Earth to project.", ex)

            # Bottom Track
            try:
                if ens.IsBottomTrack:
                    self.add_bottomtrack_ds(ens, ens_idx)
            except Exception as ex:
                print("Error adding Bottom Track to project.", ex)

            # Range Tracking
            try:
                if ens.IsRangeTracking:
                    self.add_rangetracking_ds(ens, ens_idx)
            except Exception as ex:
                print("Error adding Range Tracking to project.", ex)

            # NMEA
            try:
                if ens.IsNmeaData:
                    year = 2017
                    month = 1
                    day = 1
                    if ens.IsEnsembleData:
                        year = ens.EnsembleData.Year
                        month = ens.EnsembleData.Month
                        day = ens.EnsembleData.Day
                    self.add_nmea_ds(ens, ens_idx, year=year, month=month, day=day)
            except Exception as ex:
                print("Error adding NMEA to project.", ex)

        else:
            print("Batch import not started.  Please call begin_batch() first.")

    def add_ensemble_ds(self, ens, burst_num=0):
        """
        Add the Ensemble dataset to the database.
        """
        if not ens.IsEnsembleData or not ens.IsAncillaryData or not ens.IsSystemSetup:
            return

        # Get Date and time for created and modified
        dt = datetime.now()

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
                    'burstNum, ' \
                    'project_id, ' \
                    'created, ' \
                    'modified)' \
                    'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ' \
                    'RETURNING ID;'

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
                                                  burst_num,
                                                  self.batch_prj_id[0][0],
                                                  dt,
                                                  dt))
        ens_idx = self.batch_sql.cursor.fetchone()[0]
        #print("rti_projects:add_ensemble_ds() Ens Index: " + str(ens_idx))

        # Monitor how many inserts have been done so it does not get too big
        self.batch_count += 1
        if self.batch_count > 10:
            self.batch_sql.commit()
            self.batch_count = 0

        return ens_idx

    def add_bottomtrack_ds(self, ens, ens_idx):
        if not ens.IsBottomTrack:
            return

        # Get Date and time for created and modified
        dt = datetime.now()

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
            query_beam_vel_val += "{0}, ".format(ens.BottomTrack.Wt[beam])

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
                'created, ' \
                "modified)" \
                "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s," \
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
                "%s,%s);".format(query_range_label,
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
                                              dt,
                                              dt))

        # Monitor how many inserts have been done so it does not get too big
        self.batch_count += 1
        if self.batch_count > 10:
            self.batch_sql.commit()
            self.batch_count = 0

    def add_rangetracking_ds(self, ens, ens_idx):
        if not ens.IsRangeTracking:
            return

        # Get Date and time for created and modified
        dt = datetime.now()

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
            query_beam_vel_val += "{0}, ".format(ens.RangeTracking.Wt[beam])

            query_pings_label += "pingsBeam{0}, ".format(beam)
            query_pings_val += "{0}, ".format(int(ens.RangeTracking.Pings[beam]))

            query_instr_vel_label += "instrVelBeam{0}, ".format(beam)
            query_instr_vel_val += "{0}, ".format(ens.BottomTrack.InstrumentVelocity[beam])

            query_earth_vel_label += "earthVelBeam{0}, ".format(beam)
            query_earth_vel_val += "{0}, ".format(ens.BottomTrack.EarthVelocity[beam])

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
        query_beam_ping_label = query_pings_label[:-2]      # Remove final comma
        query_beam_ping_val = query_pings_val[:-2]          # Remove final comma
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
                '{7}, ' \
                'created, ' \
                "modified)" \
                "VALUES(%s," \
                "{8}," \
                "{9}," \
                "{10}," \
                "{11}," \
                "{12}," \
                "{13}," \
                "{14}," \
                "{15}," \
                "%s,%s);".format(query_range_label,
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
                                 query_beam_ping_val,
                                 query_instr_vel_val,
                                 query_earth_vel_val)

        self.batch_sql.cursor.execute(query, (ens_idx,
                                              int(ens.BottomTrack.NumBeams),
                                              dt,
                                              dt))

        # Monitor how many inserts have been done so it does not get too big
        self.batch_count += 1
        if self.batch_count > 10:
            self.batch_sql.commit()
            self.batch_count = 0

    def add_nmea_ds(self, ens, ens_idx, year=2017, month=1, day=1):
        """
        Add the NMEA dataset to the database.
        """
        if not ens.IsNmeaData:
            return


        # Get Date and time for created and modified
        dt = datetime.now()

        # GPS DateTime
        ens_date = date(year, month, day)
        gps_time = ens.NmeaData.datetime
        gps_datetime = datetime.combine(ens_date, gps_time)

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

        rmf = str(ens.NmeaData.GPRMF)
        if ens.NmeaData.GPRMF is None:
            rmf = None

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
                "GPRMF, " \
                "GPGLL, " \
                "GPGSV, " \
                "GPGSA, " \
                "GPHDT, " \
                "GPHDG, " \
                "latitude, " \
                "longitude, "\
                "speed_knots, " \
                "heading, " \
                "datetime, " \
                "created, " \
                "modified) " \
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        #print(query)

        self.batch_sql.cursor.execute(query, (ens_idx,
                                              ens.NmeaData.nmea_sentences,
                                              gga,
                                              vtg,
                                              rmc,
                                              rmf,
                                              gll,
                                              gsv,
                                              gsa,
                                              hdt,
                                              hdg,
                                              ens.NmeaData.latitude,
                                              ens.NmeaData.longitude,
                                              ens.NmeaData.speed_knots,
                                              ens.NmeaData.heading,
                                              gps_datetime,
                                              dt,
                                              dt))

        # Monitor how many inserts have been done so it does not get too big
        self.batch_count += 1
        if self.batch_count > 10:
            self.batch_sql.commit()
            self.batch_count = 0

        return ens_idx

    def add_dataset(self, table, data, num_elements, element_multiplier, ens_idx, bad_val=Ensemble.Ensemble.BadVelocity):
        """
        Add a dataset to the database.  Give the table name, data, number of beams and bins and the ensemble index.
        :param table: Table name as a string.
        :param data: 2D Array of the data.
        :param num_elements: Number of bins.
        :param element_multiplier: Number of beams.
        :param ens_idx: Ensemble index in Ensembles table.
        :param bad_val: If a value is bad or missing, replace it with this value.
        """
        # Get Date and time for created and modified
        dt = datetime.now()

        beam0_avail = False
        beam1_avail = False
        beam2_avail = False
        beam3_avail = False
        query_b0_label = ""
        query_b0_val = ""
        query_b1_label = ""
        query_b1_val = ""
        query_b2_label = ""
        query_b2_val = ""
        query_b3_label = ""
        query_b3_val = ""
        for bin_num in range(num_elements):
            if element_multiplier > 0:
                query_b0_label += "Bin{0}, ".format(bin_num)
                if data[bin_num][0]:
                    query_b0_val += "{0}, ".format(data[bin_num][0])
                else:
                    query_b0_val += "{0}, ".format(bad_val)
                beam0_avail = True

            if element_multiplier > 1:
                query_b1_label += "Bin{0}, ".format(bin_num)
                if data[bin_num][1]:
                    query_b1_val += "{0}, ".format(data[bin_num][1])
                else:
                    query_b1_val += "{0}, ".format(bad_val)
                beam1_avail = True

            if element_multiplier > 2:
                query_b2_label += "Bin{0}, ".format(bin_num)
                if data[bin_num][2]:
                    query_b2_val += "{0}, ".format(data[bin_num][2])
                else:
                    query_b2_val += "{0}, ".format(bad_val)
                beam2_avail = True

            if element_multiplier > 3:
                query_b3_label += "Bin{0}, ".format(bin_num)
                if data[bin_num][3]:
                    query_b3_val += "{0}, ".format(data[bin_num][3])
                else:
                    query_b3_val += "{0}, ".format(bad_val)
                beam3_avail = True

        query_b0_label = query_b0_label[:-2]        # Remove final comma
        query_b0_val = query_b0_val[:-2]            # Remove final comma
        query_b1_label = query_b1_label[:-2]        # Remove final comma
        query_b1_val = query_b1_val[:-2]            # Remove final comma
        query_b2_label = query_b2_label[:-2]        # Remove final comma
        query_b2_val = query_b2_val[:-2]            # Remove final comma
        query_b3_label = query_b3_label[:-2]        # Remove final comma
        query_b3_val = query_b3_val[:-2]            # Remove final comma

        # Add line for each beam
        if beam0_avail:
            query = "INSERT INTO {0} (" \
                    "ensIndex, " \
                    "beam, " \
                    "{1}, " \
                    "created, " \
                    "modified) " \
                     "VALUES ( %s, %s, {2}, %s, %s);".format(table, query_b0_label, query_b0_val)
            #print(query)
            self.batch_sql.cursor.execute(query, (ens_idx, 0, dt, dt))

        if beam1_avail:
            query = "INSERT INTO {0} (" \
                    "ensIndex, " \
                    "beam, " \
                    "{1}, " \
                    "created, " \
                    "modified) " \
                     "VALUES ( %s, %s, {2}, %s, %s);".format(table, query_b1_label, query_b1_val)
            #print(query)
            self.batch_sql.cursor.execute(query, (ens_idx, 1, dt, dt))

        if beam2_avail:
            query = "INSERT INTO {0} (" \
                    "ensIndex, " \
                    "beam, " \
                    "{1}, " \
                    "created, " \
                    "modified) " \
                     "VALUES ( %s, %s, {2}, %s, %s);".format(table, query_b2_label, query_b2_val)
            #print(query)
            self.batch_sql.cursor.execute(query, (ens_idx, 2, dt, dt))

        if beam3_avail:
            query = "INSERT INTO {0} (" \
                    "ensIndex, " \
                    "beam, " \
                    "{1}, " \
                    "created, " \
                    "modified) " \
                     "VALUES ( %s, %s, {2}, %s, %s);".format(table, query_b3_label, query_b3_val)
            #print(query)
            self.batch_sql.cursor.execute(query, (ens_idx, 3, dt, dt))

        # Monitor how many inserts have been done so it does not get too big
        self.batch_count += 1
        if self.batch_count > 10:
            self.batch_sql.commit()
            self.batch_count = 0

    def create_tables(self):
        logging.debug("Creating Tables in Database")

        # Make connection
        try:
            sql = RtiSQL(self.sql_conn_string, is_sqlite=self.is_sqlite)
        except Exception as e:
            print("Unable to connect to the database")

        auto_increment_str = "SERIAL"

        # Check if the connection is made
        if not sql.cursor:
            logging.error("Database connection not made yet.")
            return

        # Project
        sql.cursor.execute('CREATE TABLE IF NOT EXISTS projects (id ' + auto_increment_str + ' PRIMARY KEY,' 
                            'name text NOT NULL, '
                            'path text,'
                            'meta json,'
                            'created timestamp, '
                            'modified timestamp);')
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
                            'burstNum integer, '
                            'project_id integer, '
                            'meta json,'
                            'created timestamp, '
                            'modified timestamp);')
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
                            'meta json,'
                            'created timestamp, '
                            'modified timestamp);')
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
                            'amplitudeBeam0 real, '
                            'amplitudeBeam1 real, '
                            'amplitudeBeam2 real, '
                            'amplitudeBeam3 real, '
                            'correlationBeam0 real, '
                            'correlationBeam1 real, '
                            'correlationBeam2 real, '
                            'correlationBeam3 real, '
                            'beamVelocityBeam0 real, '
                            'beamVelocityBeam1 real, '
                            'beamVelocityBeam2 real, '
                            'beamVelocityBeam3 real, '
                            'instrVelBeam0 real, '
                            'instrVelBeam1 real, '
                            'instrVelBeam2 real, '
                            'instrVelBeam3 real, '
                            'earthVelBeam0 real, '
                            'earthVelBeam1 real, '
                            'earthVelBeam2 real, '
                            'earthVelBeam3 real, '
                            'meta json,'
                            'created timestamp, '
                            'modified timestamp);')
        logging.debug("Range Tracking table created")

        # Beam Velocity
        query = 'CREATE TABLE IF NOT EXISTS beamVelocity (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'beam integer NOT NULL, ' \
                'meta json,' \
                'created timestamp, ' \
                'modified timestamp, '
        for ensBin in range(0, 200):
            query += 'Bin' + str(ensBin) + ' real, '

        query = query[:-2]          # Remove final comma
        query += ');'
        sql.cursor.execute(query)
        logging.debug("Beam Velocity table created")

        # Instrument Velocity
        query = 'CREATE TABLE IF NOT EXISTS instrumentVelocity (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'beam integer NOT NULL, ' \
                'meta json,' \
                'created timestamp, ' \
                'modified timestamp, '
        for ensBin in range(0, 200):
            query += 'Bin' + str(ensBin) + ' real, '

        query = query[:-2]          # Remove final comma
        query += ');'
        sql.cursor.execute(query)
        logging.debug("Instrument Velocity table created")

        # Earth Velocity
        query = 'CREATE TABLE IF NOT EXISTS earthVelocity (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'beam integer NOT NULL, ' \
                'meta json,' \
                'created timestamp, ' \
                'modified timestamp, '
        for ensBin in range(0, 200):
            query += 'Bin' + str(ensBin) + ' real, '

        query = query[:-2]          # Remove final comma
        query += ');'
        sql.cursor.execute(query)
        logging.debug("Earth Velocity table created")

        # Amplitude
        query = 'CREATE TABLE IF NOT EXISTS amplitude (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'beam integer NOT NULL, ' \
                'meta json,' \
                'created timestamp, ' \
                'modified timestamp, '
        for ensBin in range(0, 200):
            query += 'Bin' + str(ensBin) + ' real, '

        query = query[:-2]          # Remove final comma
        query += ');'
        sql.cursor.execute(query)
        logging.debug("Amplitude table created")

        # Correlation
        query = 'CREATE TABLE IF NOT EXISTS correlation (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'beam integer NOT NULL, ' \
                'meta json,' \
                'created timestamp, ' \
                'modified timestamp, '
        for ensBin in range(0, 200):
            query += 'Bin' + str(ensBin) + ' real, '

        query = query[:-2]          # Remove final comma
        query += ');'
        sql.cursor.execute(query)
        logging.debug("Correlation table created")

        # Good Beam Ping
        query = 'CREATE TABLE IF NOT EXISTS goodBeamPing (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'beam integer NOT NULL, ' \
                'meta json,' \
                'created timestamp, ' \
                'modified timestamp, '
        for ensBin in range(0, 200):
            query += 'Bin' + str(ensBin) + ' integer, '

        query = query[:-2]          # Remove final comma
        query += ');'
        sql.cursor.execute(query)
        logging.debug("Good Beam Ping table created")

        # Good Earth Ping
        query = 'CREATE TABLE IF NOT EXISTS goodEarthPing (id ' + auto_increment_str + ' PRIMARY KEY, ' \
                'ensIndex integer NOT NULL, ' \
                'beam integer NOT NULL, ' \
                'meta json,' \
                'created timestamp, ' \
                'modified timestamp, '
        for ensBin in range(0, 200):
            query += 'Bin' + str(ensBin) + ' integer, '

        query = query[:-2]          # Remove final comma
        query += ');'
        sql.cursor.execute(query)
        logging.debug("Good Earth Ping table created")

        # NMEA
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
                'latitude DECIMAL(8,6), ' \
                'longitude DECIMAL(9,6), ' \
                'speed_knots real, ' \
                'heading real, ' \
                'meta json,' \
                'datetime timestamp, ' \
                'created timestamp, ' \
                'modified timestamp);'
        sql.cursor.execute(query)
        logging.debug("NMEA table created")

        logging.debug("Table Creation Complete")
        sql.conn.commit()

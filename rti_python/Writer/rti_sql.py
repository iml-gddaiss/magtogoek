import psycopg2
import sqlite3
import pandas as pd
import numpy as np
import os
import logging

"""
Update tables
ALTER TABLE ensembles ADD COLUMN project_id integer;
ALTER TABLE ensembles ADD COLUMN created timestamp;
ALTER TABLE ensembles ADD COLUMN modified timestamp;
"""


class RtiSQL:

    def __init__(self, conn: str, is_sqlite: bool = False):
        """
        Make a connection to the database.  You can use MySQL/Postgres or SQLite.
        :param conn: MySQL -> "host='localhost' dbname='my_database' user='postgres' password='secret'". SQLite -> "/path/to/example.db"
        :param is_sqlite: If set True, it will use the SQLite database, false will use MySQL
        """
        self.conn_string = conn
        self.is_sqlite = is_sqlite
        self.conn = None
        self.cursor = None

        # Make a connection
        self.sql_conn(conn)

    def sql_conn(self, conn_string):
        # print the connection string we will use to connect
        logging.debug("Connecting to database\n	->%s" % (conn_string))

        # get a connection, if a connect cannot be made an exception will be raised here
        if self.is_sqlite:
            # SQLite connection
            # Make a connection and create the tables
            #if not os.path.exists(self.conn_string):
            self.conn = sqlite3.connect(self.conn_string)
            # conn.cursor will return a cursor object, you can use this cursor to perform queries
            self.cursor = self.conn.cursor()
            logging.debug("Connected!\n")
        else:
            # MySQL connection
            self.conn = psycopg2.connect(conn_string)
            # conn.cursor will return a cursor object, you can use this cursor to perform queries
            self.cursor = self.conn.cursor()
            logging.debug("Connected!\n")

    def close(self):
        self.cursor.close()
        self.conn.close()

    def query(self, query):
        """
        Send the query and get the results from the query
        :param query: Query to execute on the database.
        :return: Results of query.  It is iterable.
        """
        logging.debug(query)
        self.cursor.execute(query)      # Send query
        self.conn.commit()

        # Return the results
        return self.cursor.fetchall()

    def insert(self, query):
        """
        Send the query to insert data.  There is no fetch with an insert.
        :param query: Query to execute on the database.
        :return: Results of query.  It is iterable.
        """
        print(query)
        self.cursor.execute(query)      # Send query to insert data
        self.conn.commit()

    def execute(self, query):
        return self.cursor.execute(query)

    def commit(self):
        return self.conn.commit()

    def ss_query(self, ss_code=None, ss_config=None):
        """
        Create a query string for the subsystem code and subsystem configuration.
        If no values are given, then empty strings are created.
        :param ss_code: Subsystem Code.
        :param ss_config: Subsystem Configuration.
        :return: Subsystem Code Query Str, Subsystem Config Index Query Str
        """

        # Use Subsystem code if given
        if ss_code:
            ss_code_str = "AND ensembles.subsystemcode = \'{}\'".format(ss_code)
        else:
            ss_code_str = ""

        # Use Subsystem configuration if given
        if ss_config:
            ss_config_str = "AND ensembles.subsystemconfig = {} ".format(ss_config)
        else:
            ss_config_str = ""

        return ss_code_str, ss_config_str

    def get_earth_vel_data(self, project_idx, beam, ss_code=None, ss_config=None):
        """
        Get all the earth velocity data for the given project and beam.
        :param project_idx: Project index.
        :param beam: Beam number.
        :param ss_code: Subsystem Code.
        :param ss_config: Subsystem Configuration.
        :return: Earth velocity data for beam in the project.
        """

        # Create the string of bins for query
        bin_nums = ""
        for x in range(0, 200):
            bin_nums += "bin" + str(x) + ", "
        bin_nums = bin_nums[:-2]  # Remove final comma

        """
        # Use Subsystem code if given
        if ss_code:
            ss_code_str = "AND ensembles.subsystemcode = \'{}\'".format(ss_code)
        else:
            ss_code_str = ""

        # Use Subsystem configuration if given
        if ss_config:
            ss_config_str = "AND ensembles.subsystemconfig = {} ".format(ss_config)
        else:
            ss_config_str = ""
        """
        ss_code_str, ss_config_str = self.ss_query(ss_code, ss_config)

        # Get all projects
        try:
            # Get all the ensembles for the project
            ens_query = 'SELECT ensembles.ensnum, ensembles.numbeams, ensembles.numbins, earthvelocity.beam, {} ' \
                        'FROM ensembles ' \
                        'INNER JOIN earthvelocity ON ensembles.id = earthvelocity.ensindex ' \
                        'WHERE ensembles.project_id = %s AND earthvelocity.beam = %s ' \
                        '{} {}' \
                        'ORDER BY ensembles.ensnum ASC;'.format(bin_nums, ss_code_str, ss_config_str)

            # Sqlite uses ? where sql uses %s
            if self.is_sqlite:
                ens_query = ens_query.replace("%s", "?")

            print(ens_query)
            self.cursor.execute(ens_query, (project_idx, beam))
            vel_results = self.cursor.fetchall()
            self.conn.commit()

        except Exception as e:
            print("Unable to run query", e)
            return pd.DataFrame()

        # Make a dataframe
        df = pd.DataFrame(vel_results)
        if not df.empty:
            columns = ['ensnum', 'numbeams', 'numbins', 'beam']
            for x in range(0, 200):
                columns.append('bin' + str(x))
            df.columns = columns
            #print(df.head())

        return df

    def get_mag(self, project_idx, ss_code=None, ss_config=None):
        ss_code_str, ss_config_str = self.ss_query(ss_code, ss_config)

        # Get all projects
        try:
            # Get all the ensembles for the project
            ens_query = 'SELECT ensembles.dateTime, ensembles.subsystemCode, ensembles.SubsystemConfig, ' \
                        'earthMagDir.bin, ensembles.rangeFirstBin, ensembles.binSize, ensembles.isUpwardLooking, earthMagDir.mag ' \
                        'FROM ensembles ' \
                        'INNER JOIN earthMagDir ON ensembles.id = earthMagDir.ensindex ' \
                        'WHERE ensembles.project_id = %s ' \
                        '{} {}' \
                        'ORDER BY ensembles.dateTime ASC;'.format(ss_code_str, ss_config_str)

            # Sqlite uses ? where sql uses %s
            if self.is_sqlite:
                ens_query = ens_query.replace("%s", "?")

            print(ens_query)
            self.cursor.execute(ens_query, (project_idx, ))
            mag_results = self.cursor.fetchall()
            self.conn.commit()

        except Exception as e:
            print("Unable to run query", e)
            return pd.DataFrame()

        # Make a dataframe
        df = pd.DataFrame(mag_results)
        if not df.empty:
            df.columns = ['datetime', "ss_code", "ss_config", "bin_num", "blank", "bin_size", "isUpwardLooking", 'mag']

        return df

    def get_bottom_track_vel(self, project_idx):
        """
        Get Bottom track velocities.
        :param project_idx: Project index.
        :return: Dataframe with all the velocities. (Beam, Instrument and Earth)
        """

        # Get all projects
        try:
            # Get all the ensembles for the project
            ens_query = 'SELECT ensembles.ensnum, ensembles.numbins, ' \
                        'beamvelbeam0, beamvelbeam1, beamvelbeam2, beamvelbeam3, ' \
                        'instrvelbeam0, instrvelbeam1, instrvelbeam2, instrvelbeam3, ' \
                        'earthvelbeam0, earthvelbeam1, earthvelbeam2, earthvelbeam3 ' \
                        'FROM ensembles ' \
                        'INNER JOIN bottomtrack ON ensembles.id = bottomtrack.ensindex ' \
                        'WHERE ensembles.project_id = %s ORDER BY ensembles.ensnum ASC;'

            # Sqlite uses ? where sql uses %s
            if self.is_sqlite:
                ens_query = ens_query.replace("%s", "?")

            self.cursor.execute(ens_query, (project_idx,))
            vel_results = self.cursor.fetchall()
            self.conn.commit()

        except Exception as e:
            print("Unable to run query", e)
            return pd.DataFrame()

        if vel_results:
            # Make a dataframe
            df = pd.DataFrame(vel_results)
            df.columns = ['ensnum', 'numbins', 'Beam0', 'Beam1', 'Beam2', 'Beam3', 'Instr0', 'Instr1', 'Instr2', 'Instr3', 'Earth0', 'Earth1', 'Earth2', 'Earth3']
        else:
            df = pd.DataFrame()

        return df

    def get_bottom_track_range(self, project_idx, ss_code=None, ss_config=None):
        """
        Get Bottom track Range.
        :param project_idx: Project index.
        :param ss_code: Subsystem Code.
        :param ss_config: Subsystem Configuration.
        :return: Dataframe with all the velocities. (Beam, Instrument and Earth)
        """

        # Set the Subsystem query
        ss_code_str, ss_config_str = self.ss_query(ss_code, ss_config)

        # Get all projects
        try:
            # Get all the ensembles for the project
            ens_query = 'SELECT ensembles.ensnum, ensembles.dateTime, ensembles.numbeams, ensembles.numbins, ' \
                        'ensembles.binsize, ensembles.rangefirstbin, ' \
                        'rangebeam0, rangebeam1, rangebeam2, rangebeam3, avgRange ' \
                        'FROM ensembles ' \
                        'INNER JOIN bottomtrack ON ensembles.id = bottomtrack.ensindex ' \
                        'WHERE ensembles.project_id = %s ' \
                        '{} {}' \
                        'ORDER BY ensembles.ensnum ASC;'.format(ss_code_str, ss_config_str)

            # Sqlite uses ? where sql uses %s
            if self.is_sqlite:
                ens_query = ens_query.replace("%s", "?")

            self.cursor.execute(ens_query, (project_idx,))
            vel_results = self.cursor.fetchall()
            self.conn.commit()

        except Exception as e:
            print("Unable to run query", e)
            return pd.DataFrame()

        # Make a dataframe
        df = pd.DataFrame(vel_results)
        if not df.empty:
            df.columns = ['ensnum', 'datetime', 'NumBeams', 'NumBins', 'BinSize', 'RangeFirstBin', 'RangeBeam0', 'RangeBeam1', 'RangeBeam2', 'RangeBeam3', 'avgRange']

        return df

    def get_adcp_info(self, project_idx):
        """
        Get information about the ensemble data.
        :param project_idx: Project index.
        :return: Earth velocity data for beam in the project.
        """

        # Get all projects
        try:
            # Get all the ensembles for the project
            ens_query = 'SELECT ensnum, datetime, serialnumber, firmware, numbins, numbeams, subsystemconfig FROM ensembles WHERE project_id = %s ORDER BY ensnum ASC;'

            # Sqlite uses ? where sql uses %s
            if self.is_sqlite:
                ens_query = ens_query.replace("%s", "?")

            self.cursor.execute(ens_query, (project_idx,))
            results = self.cursor.fetchall()
            self.conn.commit()

            ens_data = {}
            ens_data['ensnum'] = results[0][0]
            ens_data['datetime'] = results[0][1]
            ens_data['serialnumber'] = results[0][2]
            ens_data['firmware'] = results[0][3]
            ens_data['numbins'] = results[0][4]
            ens_data['numbeams'] = results[0][5]
            ens_data['subsystemconfig'] = results[0][6]

        except Exception as e:
            print("Unable to run query", e)
            return {}

        return ens_data

    def get_compass_data(self, project_idx, ss_code=None, ss_config=None):
        """
        Get compass ensemble data.
        :param project_idx: Project index.
        :return: Compass data in the project.
        """

        # Set the Subsystem query
        ss_code_str, ss_config_str = self.ss_query(ss_code, ss_config)

        # Get all projects
        try:
            # Get all the ensembles for the project
            ens_query = 'SELECT ensnum, datetime, heading, pitch, roll  FROM ensembles ' \
                        'WHERE ensembles.project_id = %s ' \
                        '{} {}' \
                        'ORDER BY ensembles.ensnum ASC;'.format(ss_code_str, ss_config_str)

            # Sqlite uses ? where sql uses %s
            if self.is_sqlite:
                ens_query = ens_query.replace("%s", "?")

            self.cursor.execute(ens_query, (project_idx,))
            results = self.cursor.fetchall()
            self.conn.commit()

            df = pd.DataFrame(results)
            df.columns = ['ensnum', 'datetime', 'heading', 'pitch', 'roll']

        except Exception as e:
            print("Unable to run query", e)
            return pd.DataFrame()

        return df

    def get_voltage_data(self, project_idx, ss_code=None, ss_config=None):
        """
        Get voltage ensemble data.

        :param project_idx: Project index.
        :param ss_code: Subsystem Code.  If not set, then all subsystem codes' data will be retrieved.
        :param ss_config: Subsystem Configuration Number: if not set, then all the configurations' data will be retrieved.
        :return: Voltage data in the project.
        """

        # Set the Subsystem query
        ss_code_str, ss_config_str = self.ss_query(ss_code, ss_config)

        # Get all projects
        try:
            # Get all the ensembles for the project
            ens_query = 'SELECT ensnum, datetime, voltage  FROM ensembles ' \
                        'WHERE ensembles.project_id = %s ' \
                        '{} {}' \
                        'ORDER BY ensembles.ensnum ASC;'.format(ss_code_str, ss_config_str)

            # Sqlite uses ? instead of %s
            if self.is_sqlite:
                ens_query = ens_query.replace("%s", "?")

            self.cursor.execute(ens_query, (project_idx,))
            results = self.cursor.fetchall()
            self.conn.commit()

            df = pd.DataFrame(results)
            df.columns = ['ensnum', 'datetime', 'voltage']

        except Exception as e:
            print("Unable to run query", e)
            return pd.DataFrame()

        return df

    def get_subsystem_configs(self, project_idx):
        """
        Get compass ensemble data.
        :param project_idx: Project index.
        :return: Compass data in the project.
        """

        # Get all projects
        try:
            # Get all the ensembles for the project
            ens_query = 'SELECT subsystemcode, subsystemconfig  FROM ensembles WHERE project_id = %s ORDER BY ensnum ASC;'

            # Sqlite uses ? where sql uses %s
            if self.is_sqlite:
                ens_query = ens_query.replace("%s", "?")

            self.cursor.execute(ens_query, (project_idx,))
            results = self.cursor.fetchall()
            self.conn.commit()

            df = pd.DataFrame(results)
            df.columns = ['subsystemcode', 'subsystemconfig']

        except Exception as e:
            print("Unable to run query", e)
            return

        #codes = df.subsystemcode.unique()
        #configs = df.subsystemconfig.unique()
        #configs = pd.unique(df['subsystemcode', 'subsystemconfig'].values.ravel())

        return df.drop_duplicates()

if __name__ == "__main__":
    conn_string = "host='localhost' port='5432' dbname='rti' user='test' password='123456'"
    sql = RtiSQL(conn_string)
    sql.create_tables()
    sql.close()



"""
Delete all tables.

DROP TABLE projects;
DROP TABLE amplitude;
DROP TABLE beamvelocity;
DROP TABLE bottomtrack;
DROP TABLE rangetracking;
DROP TABLE correlation;
DROP TABLE earthvelocity;
DROP TABLE ensembles;
DROP TABLE goodbeamping;
DROP TABLE goodearthping;
DROP TABLE instrumentvelocity;
DROP TABLE nmea;
"""

"""
Remove all data from all tables.

DELETE FROM projects;
DELETE FROM amplitude;
DELETE FROM beamvelocity;
DELETE FROM bottomtrack;
DELETE FROM rangetracking;
DELETE FROM correlation;
DELETE FROM earthvelocity;
DELETE FROM ensembles;
DELETE FROM goodbeamping;
DELETE FROM goodearthping;
DELETE FROM instrumentvelocity;
DELETE FROM nmea;


"""

import logging
from pathlib import Path, PurePath, PureWindowsPath
import json
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from rti_python.Utilities.check_binary_file import RtiCheckFile
from rti_python.Writer.rti_sqlite_projects import RtiSqliteProjects
from rti_python.Writer.rti_sql import RtiSQL


# Set logging level
logging.basicConfig(format='%(asctime)s [%(levelname)s] : %(message)s', level=logging.DEBUG)


class ReadPlotCSV:
    """
    Read in a raw binary file.  Then filter the data based on query strings.
    Then plot the data with streamlit and output to CSV.
    """

    def __init__(self):
        self.project = None
        self.beam_b0_fig = None
        self.beam_b1_fig = None
        self.beam_b2_fig = None
        self.beam_b3_fig = None
        self.beam_min = 0
        self.beam_max = 0

        self.instr_x_fig = None
        self.instr_y_fig = None
        self.instr_z_fig = None
        self.instr_err_fig = None
        self.instr_min = 0
        self.instr_max = 0

        self.earth_east_fig = None
        self.earth_north_fig = None
        self.earth_vert_fig = None
        self.earth_east_vsr_fig = None
        self.earth_north_vsr_fig = None
        self.earth_vert_vsr_fig = None
        self.earth_min = 0
        self.earth_max = 0
        self.earth_vsr_min = 0
        self.earth_vsr_max = 0

        self.mag_fig = None
        self.dir_fig = None
        self.mag_min = 0
        self.mag_max = 0
        self.mag_vsr_fig = None
        self.dir_vsr_fig = None
        self.mag_vsr_min = 0
        self.mag_vsr_max = 0

        self.amp_b0_fig = None
        self.amp_b1_fig = None
        self.amp_b2_fig = None
        self.amp_b3_fig = None
        self.amp_fig_subplots = None
        self.amp_min = 0
        self.amp_max = 0

        self.corr_b0_fig = None
        self.corr_b1_fig = None
        self.corr_b2_fig = None
        self.corr_b3_fig = None
        self.corr_fig_subplots = None
        self.corr_min = 0
        self.corr_max = 0

        self.beam_fig_subplots = None
        self.instr_fig_subplots = None
        self.earth_fig_subplots = None
        self.earth_raw_vsr_fig_subplots = None
        self.magdir_fig_subplots = None

        self.water_temp_fig = None
        self.sys_temp_fig = None
        self.temps_subplots = None

    def select_and_process(self):
        """
        Select the files you would like to process.  Then create a DB file based on the binary files.
        If a DB file is selected, then load the data.

        Upward, the roll is around 0 degrees.
        Downward, the roll is around -180 or 180

        Bad Velocity is 88.888

        :param max_roll: Maximum roll value to allow.
        :param max_vel: Maximum velocity to allow.
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param max_mag: Maximum water Magnitude value to allow.
        """
        # Create a file checker
        rti_check = RtiCheckFile()

        # Event handler for ensembles
        rti_check.ensemble_event += self.ens_handler

        # Select all the files to load
        file_paths = rti_check.select_files()

        # Verify a file was selected
        if len(file_paths) > 0:
            logging.debug(file_paths)

            # Get the folder path from the first file path
            folder_path = PurePath(file_paths[0]).parent
            prj_name = Path(file_paths[0]).stem
            db_name = str(prj_name) + ".db"

            # Create a project file to store the results
            db_path = str(folder_path / db_name)
            logging.debug(db_path)

            # Check if the database file exist
            # If the database file does not exist,
            # we will create the database file
            if not Path(db_path).exists():
                self.project = RtiSqliteProjects(file_path=db_path)
                self.project.create_tables()
                prj_idx = self.project.add_prj_sql(str(prj_name), db_path)

                # Begin the batch writing to the database
                self.project.begin_batch(str(prj_name))

                # Process the selected file
                rti_check.process(file_paths, show_live_error=False)

                # Get the summary and add it to the sqlite project
                file_summary = rti_check.get_summary()
                self.project.add_summary(json.dumps(file_summary), prj_idx)

                # End any remaining batch
                self.project.end_batch()
            else:
                # Create a connection to the sqlite project file
                self.project = RtiSqliteProjects(file_path=db_path)
                prj_idx = self.project.check_project_exist(str(prj_name))

            return True
        return False

    def export_to_csv_(self, max_roll: float = 160.0):
        """
        Export the data to a CSV.

        :param max_roll: Maximum roll value to allow.
        """
        # Filter some of the data
        filter_query = "WHERE ensembles.roll > " + str(max_roll) + " OR ensembles.roll < -" + str(max_roll)

        # Setup a query to get the data from the database
        query = "SELECT " \
                "ensembles.ensNum," \
                "ensembles.dateTIme," \
                "beamVelocity.bin," \
                "beamVelocity.binDepth," \
                "beamVelocity.beam0," \
                "beamVelocity.beam1,"\
                "beamVelocity.beam2," \
                "beamVelocity.beam3," \
                "instrumentVelocity.beam0," \
                "instrumentVelocity.beam1,"\
                "instrumentVelocity.beam2," \
                "instrumentVelocity.beam3," \
                "earthVelocity.beam0," \
                "earthVelocity.beam1,"\
                "earthVelocity.beam2," \
                "earthVelocity.beam3," \
                "bottomtrack.beamVelBeam0," \
                "bottomtrack.beamVelBeam1," \
                "bottomtrack.beamVelBeam2," \
                "bottomtrack.beamVelBeam3," \
                "bottomtrack.instrVelBeam0," \
                "bottomtrack.instrVelBeam1," \
                "bottomtrack.instrVelBeam2," \
                "bottomtrack.instrVelBeam3," \
                "bottomtrack.earthVelBeam0," \
                "bottomtrack.earthVelBeam1,"\
                "bottomtrack.earthVelBeam2," \
                "bottomtrack.earthVelBeam3," \
                "bottomtrack.avgRange " \
                "FROM ensembles " \
                "INNER JOIN beamVelocity ON ensembles.id=beamVelocity.ensIndex " \
                "INNER JOIN instrumentVelocity ON ensembles.id=instrumentVelocity.ensIndex "\
                "INNER JOIN earthVelocity ON ensembles.id=earthVelocity.ensIndex " \
                "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"

        # Filter the data using the query
        df = self.query_data(self.project.file_path, query)

        # Rename the columns so we know which column is bottom track and to handle duplicate column names
        df.rename(columns={"beamVelBeam0": "btBeamVelB0",
                           "beamVelBeam1": "btBeamVelB1",
                           "beamVelBeam2": "btBeamVelB2",
                           "beamVelBeam3": "btBeamVelB3",
                           "instrVelBeam0": "btInstrVelB0",
                           "instrVelBeam1": "btInstrVelB1",
                           "instrVelBeam2": "btInstrVelB2",
                           "instrVelBeam3": "btInstrVelB3",
                           "earthVelBeam0": "btEarthVelB0",
                           "earthVelBeam1": "btEarthVelB1",
                           "earthVelBeam2": "btEarthVelB2",
                           "earthVelBeam3": "btEarthVelB3",
                           "beamVelocity.beam0": "beamVelB0",
                           "beamVelocity.beam1": "beamVelB1",
                           "beamVelocity.beam2": "beamVelB2",
                           "beamVelocity.beam3": "beamVelB3",
                           "instrumentVelocity.beam0": "instrVelB0",
                           "instrumentVelocity.beam1": "instrVelB1",
                           "instrumentVelocity.beam2": "instrVelB2",
                           "instrumentVelocity.beam3": "instrVelB3",
                           "earthVelocity.beam0": "earthVelB0",
                           "earthVelocity.beam1": "earthVelB1",
                           "earthVelocity.beam2": "earthVelB2",
                           "earthVelocity.beam3": "earthVelB3",
                           },
                  inplace=True)

        # Get the folder path from the project file path
        # Then create the CSV file
        folder_path = PurePath(self.project.file_path).parent
        prj_name = PurePath(self.project.file_path).stem
        csv_name = folder_path.joinpath(str(prj_name) + ".csv").as_posix()
        logging.debug("CSV File: " + csv_name)

        # Write the results to the CSV file
        df.to_csv(csv_name, index=False)

    def export_beam_to_csv(self, max_roll: float = 160.0, max_vel: float = 88.0):
        """
        Export the data to a CSV.

        :param max_roll: Maximum roll value to allow.
        :param max_vel: Maximum velocity to allow.
        """
        # Filter some of the data
        filter_query = "WHERE ensembles.roll > " + str(max_roll) + " OR ensembles.roll < -" + str(max_roll)

        # Setup a query to get the data from the database
        query = "SELECT " \
                "ensembles.ensNum," \
                "ensembles.dateTIme," \
                "beamVelocity.bin," \
                "beamVelocity.binDepth," \
                "beamVelocity.beam0," \
                "beamVelocity.beam1,"\
                "beamVelocity.beam2," \
                "beamVelocity.beam3," \
                "bottomtrack.beamVelBeam0," \
                "bottomtrack.beamVelBeam1," \
                "bottomtrack.beamVelBeam2," \
                "bottomtrack.beamVelBeam3," \
                "bottomtrack.avgRange " \
                "FROM ensembles " \
                "INNER JOIN beamVelocity ON ensembles.id=beamVelocity.ensIndex " \
                "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"

        # Filter the data using the query
        df = self.query_data(self.project.file_path, query)

        # Rename the columns so we know which column is bottom track and to handle duplicate column names
        df.rename(columns={"beamVelBeam0": "btBeamVelB0",
                           "beamVelBeam1": "btBeamVelB1",
                           "beamVelBeam2": "btBeamVelB2",
                           "beamVelBeam3": "btBeamVelB3",
                           "beam0": "beamVelB0",
                           "beam1": "beamVelB1",
                           "beam2": "beamVelB2",
                           "beam3": "beamVelB3",
                           },
                  inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and postive the same
        df['beamVelB0'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['beamVelB0']]
        df['beamVelB1'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['beamVelB1']]
        df['beamVelB2'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['beamVelB2']]
        df['beamVelB3'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['beamVelB3']]

        # Get the folder path from the project file path
        # Then create the CSV file
        folder_path = PurePath(self.project.file_path).parent
        prj_name = PurePath(self.project.file_path).stem + "_beam_vel"
        csv_name = folder_path.joinpath(str(prj_name) + ".csv").as_posix()
        logging.debug("CSV File: " + csv_name)

        # Write the results to the CSV file
        df.to_csv(csv_name, index=False)

    def export_instr_to_csv(self, max_roll: float = 160.0, max_vel: float = 88.0):
        """
        Export the data to a CSV.

        :param max_roll: Maximum roll value to allow.
        :param max_vel: Maximum velocity to allow.
        """
        # Filter some of the data
        filter_query = "WHERE ensembles.roll > " + str(max_roll) + " OR ensembles.roll < -" + str(max_roll)

        # Setup a query to get the data from the database
        query = "SELECT " \
                "ensembles.ensNum," \
                "ensembles.dateTIme," \
                "instrumentVelocity.bin," \
                "instrumentVelocity.binDepth," \
                "instrumentVelocity.beam0," \
                "instrumentVelocity.beam1,"\
                "instrumentVelocity.beam2," \
                "instrumentVelocity.beam3," \
                "bottomtrack.beamVelBeam0," \
                "bottomtrack.beamVelBeam1," \
                "bottomtrack.beamVelBeam2," \
                "bottomtrack.beamVelBeam3," \
                "bottomtrack.avgRange " \
                "FROM ensembles " \
                "INNER JOIN instrumentVelocity ON ensembles.id=instrumentVelocity.ensIndex " \
                "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"

        # Filter the data using the query
        df = self.query_data(self.project.file_path, query)

        # Rename the columns so we know which column is bottom track and to handle duplicate column names
        df.rename(columns={"beamVelBeam0": "btBeamVelB0",
                           "beamVelBeam1": "btBeamVelB1",
                           "beamVelBeam2": "btBeamVelB2",
                           "beamVelBeam3": "btBeamVelB3",
                           "beam0": "instrVelB0",
                           "beam1": "instrVelB1",
                           "beam2": "instrVelB2",
                           "beam3": "instrVelB3",
                           },
                  inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and postive the same
        df['instrVelB0'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['instrVelB0']]
        df['instrVelB1'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['instrVelB1']]
        df['instrVelB2'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['instrVelB2']]
        df['instrVelB3'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['instrVelB3']]

        # Get the folder path from the project file path
        # Then create the CSV file
        folder_path = PurePath(self.project.file_path).parent
        prj_name = PurePath(self.project.file_path).stem + "_instrument_vel"
        csv_name = folder_path.joinpath(str(prj_name) + ".csv").as_posix()
        logging.debug("CSV File: " + csv_name)

        # Write the results to the CSV file
        df.to_csv(csv_name, index=False)

    def export_earth_to_csv(self, max_roll: float = 160.0, max_vel: float = 88.0):
        """
        Export the data to a CSV.

        :param max_roll: Maximum roll value to allow.
        :param max_vel: Maximum velocity to allow.
        """
        # Filter some of the data
        filter_query = "WHERE ensembles.roll > " + str(max_roll) + " OR ensembles.roll < -" + str(max_roll)

        # Setup a query to get the data from the database
        query = "SELECT " \
                "ensembles.ensNum," \
                "ensembles.dateTIme," \
                "earthVelocity.bin," \
                "earthVelocity.binDepth," \
                "earthVelocity.beam0," \
                "earthVelocity.beam1,"\
                "earthVelocity.beam2," \
                "earthVelocity.beam3," \
                "bottomtrack.beamVelBeam0," \
                "bottomtrack.beamVelBeam1," \
                "bottomtrack.beamVelBeam2," \
                "bottomtrack.beamVelBeam3," \
                "bottomtrack.avgRange " \
                "FROM ensembles " \
                "INNER JOIN earthVelocity ON ensembles.id=earthVelocity.ensIndex " \
                "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"

        # Filter the data using the query
        df = self.query_data(self.project.file_path, query)

        # Rename the columns so we know which column is bottom track and to handle duplicate column names
        df.rename(columns={"beamVelBeam0": "btBeamVelB0",
                           "beamVelBeam1": "btBeamVelB1",
                           "beamVelBeam2": "btBeamVelB2",
                           "beamVelBeam3": "btBeamVelB3",
                           "beam0": "earthVelB0",
                           "beam1": "earthVelB1",
                           "beam2": "earthVelB2",
                           "beam3": "earthVelB3",
                           },
                  inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and postive the same
        df['earthVelB0'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['earthVelB0']]
        df['earthVelB1'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['earthVelB1']]
        df['earthVelB2'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['earthVelB2']]
        df['earthVelB3'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['earthVelB3']]

        # Get the folder path from the project file path
        # Then create the CSV file
        folder_path = PurePath(self.project.file_path).parent
        prj_name = PurePath(self.project.file_path).stem + "_earth_vel"
        csv_name = folder_path.joinpath(str(prj_name) + ".csv").as_posix()
        logging.debug("CSV File: " + csv_name)

        # Write the results to the CSV file
        df.to_csv(csv_name, index=False)

    def export_mag_dir_to_csv(self, max_roll: float = 160.0, max_vel: float = 88.0):
        """
        Export the magnitude and direction data to a CSV.

        :param max_roll: Maximum roll value to allow.
        :param max_vel: Maximum velocity to allow.
        """
        # Filter some of the data
        filter_query = "WHERE ensembles.roll > " + str(max_roll) + " OR ensembles.roll < -" + str(max_roll)

        # Setup a query to get the data from the database
        query = "SELECT " \
                "ensembles.ensNum," \
                "ensembles.dateTIme," \
                "earthMagDir.bin," \
                "earthMagDir.binDepth," \
                "earthMagDir.mag," \
                "earthMagDir.dir,"\
                "earthMagDir.rawMag," \
                "earthMagDir.rawDir," \
                "bottomtrack.beamVelBeam0," \
                "bottomtrack.beamVelBeam1," \
                "bottomtrack.beamVelBeam2," \
                "bottomtrack.beamVelBeam3," \
                "bottomtrack.avgRange " \
                "FROM ensembles " \
                "INNER JOIN earthMagDir ON ensembles.id=earthMagDir.ensIndex " \
                "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"

        # Filter the data using the query
        df = self.query_data(self.project.file_path, query)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and postive the same
        df['mag'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['mag']]
        df['rawMag'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['rawMag']]

        # Get the folder path from the project file path
        # Then create the CSV file
        folder_path = PurePath(self.project.file_path).parent
        prj_name = PurePath(self.project.file_path).stem + "_earth_mag_dir_vel"
        csv_name = folder_path.joinpath(str(prj_name) + ".csv").as_posix()
        logging.debug("CSV File: " + csv_name)

        # Write the results to the CSV file
        df.to_csv(csv_name, index=False)

    def export_avg_depth_vel_dist_travel_to_csv(self, max_roll: float = 160.0, max_vel: float = 88.0):
        """
        Create a CSV with the average depth, average velocity and distance traveled.

        Average depth is already done, but is the average of the bottom track ranges not including
        the bad values.

        Average velocity is average velocity magnitude of all the bins in each ensemble.

        Distance Traveld is speed (BT) * delta_time.

        :param max_roll: Maximum roll value to allow.
        :param max_vel: Maximum velocity to allow.
        """

        # Filter some of the data
        filter_query = "WHERE ensembles.roll > " + str(max_roll) + " OR ensembles.roll < -" + str(max_roll)

        # Setup a query to get the data from the database
        query = "SELECT " \
                "ensembles.ensNum," \
                "ensembles.dateTime," \
                "earthMagDir.bin," \
                "earthMagDir.binDepth," \
                "earthMagDir.mag," \
                "earthMagDir.dir,"\
                "bottomtrack.beamVelBeam0," \
                "bottomtrack.beamVelBeam1," \
                "bottomtrack.beamVelBeam2," \
                "bottomtrack.beamVelBeam3," \
                "bottomtrack.avgRange, " \
                "bottomtrack.vesselSpeed, " \
                "bottomtrack.vesselDirection " \
                "FROM ensembles " \
                "INNER JOIN earthMagDir ON ensembles.id=earthMagDir.ensIndex " \
                "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"

        # Filter the data using the query
        df = self.query_data(self.project.file_path, query)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and postive the same
        # This is also used to remove BAD_VELOCITY
        df['mag'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['mag']]
        df['vesselSpeed'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['vesselSpeed']]
        df['vesselDirection'] = [x if abs(x) < abs(max_vel) else np.nan for x in df['vesselDirection']]

        # Convert the dateTime column from a string to datetime
        df['dateTime'] = pd.to_datetime(df['dateTime'])

        # Average the magnitude value
        # Find all the datetime to breakup the DB into ensembles
        # (b-a)/np.timedelta64 subtracts to the 2 times then converts to seconds
        unique_dt = df['dateTime'].unique()
        delta_time = [(b-a)/np.timedelta64(1,'s') for a, b in zip(unique_dt, unique_dt[1:])]
        # We Ignored the first value, but fill it in with a nan
        delta_time = [np.nan] + delta_time

        # Get all the rows for a specific ensemble
        # Then average the mag column.  This will average all the bins
        avg_vel = []
        dist_trav = []
        dir_trav = []
        avg_depth = []
        date_time = []
        for index, ens_dt in enumerate(unique_dt):
            # Get all the ensembles for a specific datetime
            df_ens = df[df.dateTime == ens_dt]

            # Calculate the average velocity for the ensemble
            vel_mean = df_ens['mag'].mean()
            avg_vel.append(vel_mean)

            # Convert the delta time to seconds
            #delta_time_sec = time.mktime(delta_time[index])
            delta_time_sec = delta_time[index]

            # Get the average speed of the ADCP moving
            avg_vessel_speed = df_ens['vesselSpeed'].mean()

            # Get the average direction the ADCP moving
            dir_trav.append(df_ens['vesselDirection'].mean())

            # Calculate the distanced traveled from the average vel and delta time
            dist_trav.append(delta_time_sec * avg_vessel_speed)

            # Set the average depth
            avg_depth.append(df_ens['avgRange'].mean())

            # Set the time to
            date_time.append(ens_dt)

        # Get the folder path from the project file path
        # Then create the CSV file
        folder_path = PurePath(self.project.file_path).parent
        prj_name = PurePath(self.project.file_path).stem + "_avg_depth_vel_dist_trav"
        csv_name = folder_path.joinpath(str(prj_name) + ".csv").as_posix()
        logging.debug("CSV File: " + csv_name)

        # Write the results to the CSV file
        with open(csv_name, "w") as file:
            file.write("datetime, avgDepth, avgVel, distanceTraveled, directionTraveled \n")
            for index in range(len(unique_dt)):
                # Replace nan with blank so plotting in excel works
                avg_vel_str = str(avg_vel[index])
                if np.isnan(avg_vel[index]):
                    avg_vel_str = ""

                # Replace nan with blank so plotting in excel works
                avg_depth_str = str(avg_depth[index])
                if np.isnan(avg_depth[index]):
                    avg_depth_str = ""

                # Replace nan with blank so plotting in excel works
                dist_trav_str = str(dist_trav[index])
                if np.isnan(dist_trav[index]):
                    dist_trav_str = ""

                # Replace nan with blank so plotting in excel works
                dir_trav_str = str(dir_trav[index])
                if np.isnan(dir_trav[index]):
                    dir_trav_str = ""

                file.write(str(unique_dt[index]) + "," + avg_depth_str + "," + avg_vel_str + "," + dist_trav_str + "," + dir_trav_str + "\n")

    def export_to_csv(self, df: pd.DataFrame, file_name_suffix: str):
        """
        Export the data to a CSV.

        :param df: Dataframe to export to CSV.
        :param file_name_suffix: Suffix to add to the file name before the file extension.
        """

        # Get the folder path from the project file path
        # Then create the CSV file
        folder_path = PurePath(self.project.file_path).parent
        prj_name = PurePath(self.project.file_path).stem + file_name_suffix
        csv_name = folder_path.joinpath(str(prj_name) + ".csv").as_posix()
        logging.debug("CSV File: " + csv_name)

        # Write the results to the CSV file
        df.to_csv(csv_name, index=False)

    def display_all_data(self, max_roll: float = 160, max_vel: float = 88.0, max_bt_vel: float = 88.0, max_mag: float = 88.0):
        """
        Process the data and display the plots in streamlit.

        Upward, the roll is around 0 degrees.
        Downward, the roll is around -180 or 180

        Bad Velocity is 88.888

        :param max_roll: Maximum roll value to allow.
        :param max_vel: Maximum velocity to allow.
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param max_mag: Maximum water Magnitude value to allow.
        """
        filter_data = "WHERE ensembles.roll > " + str(max_roll) + " OR ensembles.roll < -" + str(max_roll)

        # Beam Velocity
        self.beam_0_vel(filter_data, max_vel=max_vel, display_text=False, display_stats=False, display_plot=False)
        self.beam_0_vel_remove_ship(filter_data, max_vel=max_vel, max_bt_vel=max_bt_vel, display_text=False, display_stats=True, display_plot=False)
        self.beam_1_vel(filter_data, max_vel=max_vel, display_text=False, display_stats=False, display_plot=False)
        self.beam_1_vel_remove_ship(filter_data, max_vel=max_vel, max_bt_vel=max_bt_vel, display_text=False, display_stats=True, display_plot=False)
        self.beam_2_vel(filter_data, max_vel=max_vel, display_text=False, display_stats=False, display_plot=False)
        self.beam_2_vel_remove_ship(filter_data, max_vel=max_vel, max_bt_vel=max_bt_vel, display_text=False, display_stats=True, display_plot=False)
        self.beam_3_vel(filter_data, max_vel=max_vel, display_text=False, display_stats=False, display_plot=False)
        self.beam_3_vel_remove_ship(filter_data, max_vel=max_vel, max_bt_vel=max_bt_vel, display_text=False, display_stats=True, display_plot=False)
        self.display_beam_vel_plots()

        # Instrument Velocity
        self.intr_x_vel_remove_ship(filter_data, max_vel=max_vel, max_bt_vel=max_bt_vel, display_text=False, display_stats=True, display_plot=False)
        self.intr_y_vel_remove_ship(filter_data, max_vel=max_vel, max_bt_vel=max_bt_vel, display_text=False, display_stats=True, display_plot=False)
        self.intr_z_vel_remove_ship(filter_data, max_vel=max_vel, max_bt_vel=max_bt_vel, display_text=False, display_stats=True, display_plot=False)
        self.intr_err_vel_remove_ship(filter_data, max_vel=max_vel, max_bt_vel=max_bt_vel, display_text=False, display_stats=True, display_plot=False)
        self.display_instr_vel_plots()

        # Earth Velocity
        self.earth_east_vel_remove_ship(filter_data, max_vel=max_vel, max_bt_vel=max_bt_vel, display_text=False, display_stats=True, display_plot=False)
        self.earth_north_vel_remove_ship(filter_data, max_vel=max_vel, max_bt_vel=max_bt_vel, display_text=False, display_stats=True, display_plot=False)
        self.earth_vert_vel_remove_ship(filter_data, max_vel=max_vel, max_bt_vel=max_bt_vel, display_text=False, display_stats=True, display_plot=False)
        self.display_earth_vel_plots()

        # Magnitude and Direction
        self.mag_plot(filter_data, max_mag=max_mag, max_bt_vel=max_bt_vel, display_text=True, display_stats=True, display_plot=False)
        self.dir_plot(filter_data, max_vel=max_vel, max_bt_vel=max_bt_vel, display_text=True, display_stats=True, display_plot=False)
        self.display_mag_dir_plots();

        # Display all the plots in a single HTML
        self.display_all_plots()

    def beam_0_vel(self, filter_query: str, max_vel: float = 88.0, round_val: int = 3, use_bin_depth=True, display_text: bool = True, display_stats: bool = True, display_plot: bool = True, is_export: bool = True):
        """
        Get the Beam 0 raw values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param round_val: Round the values displayed to this decimal place.
        :param use_bin_depth: Use bin or bin depth for the y axis
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        :param is_export: Flag if the data should be export to a CSV.
        """
        bv_query = "SELECT dateTime,bin,binDepth,beam0 " \
                   "FROM ensembles " \
                   "INNER JOIN beamVelocity ON ensembles.id=beamVelocity.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and postive the same
        data['beam0'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['beam0']]
        data['binDepth'] = [round(x, 1) for x in data['binDepth']]

        if is_export:
            # Export to CSV
            self.export_to_csv(data, "_beam_vel_0_raw")

        # Display the raw data
        if display_text:
            st.subheader("Beam Velocity - Beam 0 Raw Data")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Beam Velocity - Beam 0")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['beam0'].mean(), round_val)
            median_beamVel = round(data['beam0'].median(), round_val)
            min_beamVel = round(data['beam0'].min(), round_val)
            max_beamVel = round(data['beam0'].max(), round_val)
            std_beamVel = round(data['beam0'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        if display_plot:
            # Get the data from the query
            st.subheader("Plot Beam 0 Velocity")
            #if use_bin_depth:
            bin_nums = data['binDepth']
            #else:
            #    bin_nums = data['bin']
            dates = data['dateTime']
            z = data['beam0']

            # Create the plot
            fig = go.Figure(data=go.Heatmap(
                z=z,
                x=dates,
                y=bin_nums,
                colorscale='Viridis'))

            # Set the layout with downward looking
            fig.update_layout(
                title="Beam 0 Velocity",
                xaxis_title="DateTime",
                yaxis_title="Bin Number",
                yaxis_autorange='reversed'  # Downward looking 'reversed'
            )

            # Add the plot
            st.plotly_chart(fig)
            fig.write_html(self.gen_file_path(file_suffix="_plot_beam_vel_0", file_ext=".html"))

    def beam_0_vel_remove_ship(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, use_bin_depth=True, display_text: bool = True, display_stats: bool = True, display_plot: bool = True, is_export: bool = True):
        """
        Get the Beam 0 raw values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param use_bin_depth: Use bin or bin depth for the y axis
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        :param is_export: Flag if the data should be export to CSV.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTime, ensembles.isUpwardLooking, beamVelocity.bin,beamVelocity.binDepth,beamVelocity.beam0,bottomtrack.beamVelBeam0,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN beamVelocity ON ensembles.id=beamVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"beamVelBeam0": "btVelB0", "beam0": "beamB0"}, inplace=True)

        # Check if the data is upward or downward looking
        is_upward_looking = False
        if len(data['isUpwardLooking']) > 0 and data['isUpwardLooking'].mean() > 0:
            is_upward_looking = True

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['beamB0'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['beamB0']]
        data['btVelB0'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelB0']]
        data['avgRange'] = [x if x != 0 else np.nan for x in data['avgRange']]
        data['binDepth'] = [round(x, 1) for x in data['binDepth']]

        # Remove vessel speed
        # Add the bottom track velocity to remove the velocity
        data['beamVelB0_VSR'] = data['beamB0'] + data['btVelB0']

        # Set the min and max values
        self.beam_min = min(self.beam_min, data['beamVelB0_VSR'].min())
        self.beam_max = max(self.beam_max, data['beamVelB0_VSR'].max())

        if is_export:
            # Export to CSV
            self.export_to_csv(data, "_beam_vel_0_vsr")

        # Display the raw data
        if display_text:
            st.subheader("Beam Velocity Beam 0 Raw Data (Vessel Speed Removed)")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Beam Velocity - Beam 0")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['beamB0'].mean(), round_val)
                median_beamVel = round(data['beamB0'].median(), round_val)
                min_beamVel = round(data['beamB0'].min(), round_val)
                max_beamVel = round(data['beamB0'].max(), round_val)
                std_beamVel = round(data['beamB0'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Beam Velocity**")
                mean_beamBtVel = round(data['btVelB0'].mean(), round_val)
                median_beamBtVel = round(data['btVelB0'].median(), round_val)
                min_beamBtVel = round(data['btVelB0'].min(), round_val)
                max_beamBtVel = round(data['btVelB0'].max(), round_val)
                std_beamBtVel = round(data['btVelB0'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

            with col3:
                st.subheader("Beam Velocity")
                st.markdown("**(Vessel Speed Removed)**")
                mean_beamBtVel_vsr = round(data['beamVelB0_VSR'].mean(), round_val)
                median_beamBtVel_vsr = round(data['beamVelB0_VSR'].median(), round_val)
                min_beamBtVel_vsr = round(data['beamVelB0_VSR'].min(), round_val)
                max_beamBtVel_vsr = round(data['beamVelB0_VSR'].max(), round_val)
                std_beamBtVel_vsr = round(data['beamVelB0_VSR'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel_vsr))
                st.markdown("***Average Median: *** " + str(median_beamBtVel_vsr))
                st.markdown("***Min: *** " + str(min_beamBtVel_vsr))
                st.markdown("***Max: *** " + str(max_beamBtVel_vsr))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel_vsr))

        # Get the data from the query
        #if use_bin_depth:
        bin_nums = data['binDepth']
        #else:
        #    bin_nums = data['bin']
        dates = data['dateTime']
        z = data['beamVelB0_VSR']

        bt_range = data['avgRange']

        # Create the plot
        beam_vel = go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'
        )

        bt_line = go.Scatter(
            x=dates,
            y=bt_range
        )

        plots = [beam_vel, bt_line]

        # Combine all the plots
        self.beam_b0_fig = go.Figure(data=plots)

        if is_upward_looking:
            # Set the layout with downward looking
            self.beam_b0_fig.update_layout(
                title="Beam 0 Velocity",
                xaxis_title="DateTime",
                yaxis_title="Bin Number",
            )
        else:
            # Set the layout with downward looking
            self.beam_b0_fig.update_layout(
                title="Beam 0 Velocity",
                xaxis_title="DateTime",
                yaxis_title="Bin Number",
                yaxis_autorange='reversed'  # Downward looking 'reversed'
            )

        if display_plot:
            # Add the plot
            st.subheader("Plot Beam Velocity - Beam 0 (Vessel Speed Removed)")
            st.plotly_chart(self.beam_b0_fig)
            self.beam_b0_fig.write_html(self.gen_file_path(file_suffix="_plot_beam_vel_vsr_0", file_ext=".html"))

    def beam_1_vel(self, filter_query: str, max_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Beam 1 raw values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param round_val: Round the values displayed to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT dateTIme,bin,binDepth,beam1 FROM ensembles INNER JOIN beamVelocity ON ensembles.id=beamVelocity.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and postive the same
        data['beam1'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['beam1']]

        if display_text:
            # Display the raw data
            st.subheader("Beam Velocity - Beam 1 Raw Data")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            # Display the stats of the data
            st.subheader("Beam Velocity - Beam 1")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['beam1'].mean(), round_val)
            median_beamVel = round(data['beam1'].median(), round_val)
            min_beamVel = round(data['beam1'].min(), round_val)
            max_beamVel = round(data['beam1'].max(), round_val)
            std_beamVel = round(data['beam1'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        if display_plot:
            # Get the data from the query
            st.subheader("Plot Beam 1 Velocity")
            bin_nums = data['bin']
            dates = data['dateTime']
            z = data['beam1']

            # Create the plot
            fig = go.Figure(data=go.Heatmap(
                z=z,
                x=dates,
                y=bin_nums,
                colorscale='Viridis'))

            # Set the layout with downward looking
            fig.update_layout(
                title="Beam 1 Velocity",
                xaxis_title="DateTime",
                yaxis_title="Bin Number",
                yaxis_autorange='reversed'  # Downward looking 'reversed'
            )

            # Add the plot
            st.plotly_chart(fig)

    def beam_1_vel_remove_ship(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Beam 1 raw values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,beamVelocity.bin,beamVelocity.binDepth,beamVelocity.beam1,bottomtrack.beamVelBeam1,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN beamVelocity ON ensembles.id=beamVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"beamVelBeam1": "btVelB1", "beam1": "beamB1"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['beamB1'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['beamB1']]
        data['btVelB1'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelB1']]

        # Remove vessel speed
        # Add the bottom track velocity to remove the velocity
        data['beamVelB1_VSR'] = data['beamB1'] + data['btVelB1']

        # Set the min and max values
        self.beam_min = min(self.beam_min, data['beamVelB1_VSR'].min())
        self.beam_max = max(self.beam_max, data['beamVelB1_VSR'].max())

        if display_text:
            # Display the raw data
            st.subheader("Beam Velocity - Beam 1 Raw Data (Vessel Speed Removed)")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Beam Velocity - Beam 1")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['beamB1'].mean(), round_val)
                median_beamVel = round(data['beamB1'].median(), round_val)
                min_beamVel = round(data['beamB1'].min(), round_val)
                max_beamVel = round(data['beamB1'].max(), round_val)
                std_beamVel = round(data['beamB1'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Beam Velocity**")
                mean_beamBtVel = round(data['btVelB1'].mean(), round_val)
                median_beamBtVel = round(data['btVelB1'].median(), round_val)
                min_beamBtVel = round(data['btVelB1'].min(), round_val)
                max_beamBtVel = round(data['btVelB1'].max(), round_val)
                std_beamBtVel = round(data['btVelB1'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

            with col3:
                st.subheader("Beam Velocity")
                st.markdown("**(Vessel Speed Removed)**")
                mean_beamBtVel_vsr = round(data['beamVelB1_VSR'].mean(), round_val)
                median_beamBtVel_vsr = round(data['beamVelB1_VSR'].median(), round_val)
                min_beamBtVel_vsr = round(data['beamVelB1_VSR'].min(), round_val)
                max_beamBtVel_vsr = round(data['beamVelB1_VSR'].max(), round_val)
                std_beamBtVel_vsr = round(data['beamVelB1_VSR'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel_vsr))
                st.markdown("***Average Median: *** " + str(median_beamBtVel_vsr))
                st.markdown("***Min: *** " + str(min_beamBtVel_vsr))
                st.markdown("***Max: *** " + str(max_beamBtVel_vsr))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel_vsr))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['beamVelB1_VSR']

        # Create the plot
        self.beam_b1_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.beam_b1_fig.update_layout(
            title="Beam 1 Velocity",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Beam Velocity - Beam 1 (Vessel Speed Removed)")
            st.plotly_chart(self.beam_b1_fig)

    def beam_2_vel(self, filter_query: str, max_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Beam 2 raw values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param round_val: Round the values displayed to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT dateTIme,bin,binDepth,beam2 FROM ensembles INNER JOIN beamVelocity ON ensembles.id=beamVelocity.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and postive the same
        data['beam2'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['beam2']]

        if display_text:
            # Display the raw data
            st.subheader("Beam Velocity - Beam 2 Raw Data")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            # Display the stats of the data
            st.subheader("Beam Velocity - Beam 2")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['beam2'].mean(), round_val)
            median_beamVel = round(data['beam2'].median(), round_val)
            min_beamVel = round(data['beam2'].min(), round_val)
            max_beamVel = round(data['beam2'].max(), round_val)
            std_beamVel = round(data['beam2'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        if display_plot:
            # Get the data from the query
            st.subheader("Plot Beam Velocity - Beam 2")
            bin_nums = data['bin']
            dates = data['dateTime']
            z = data['beam2']

            # Create the plot
            fig = go.Figure(data=go.Heatmap(
                z=z,
                x=dates,
                y=bin_nums,
                colorscale='Viridis'))

            # Set the layout with downward looking
            fig.update_layout(
                title="Beam Velocity - Beam 2",
                xaxis_title="DateTime",
                yaxis_title="Bin Number",
                yaxis_autorange='reversed'  # Downward looking 'reversed'
            )

            # Add the plot
            st.plotly_chart(fig)

    def beam_2_vel_remove_ship(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Beam 2 raw values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,beamVelocity.bin,beamVelocity.binDepth,beamVelocity.beam2,bottomtrack.beamVelBeam2,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN beamVelocity ON ensembles.id=beamVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"beamVelBeam2": "btVelB2", "beam2": "beamB2"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['beamB2'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['beamB2']]
        data['btVelB2'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelB2']]

        # Remove vessel speed
        # Add the bottom track velocity to remove the velocity
        data['beamVelB2_VSR'] = data['beamB2'] + data['btVelB2']

        # Set the min and max values
        self.beam_min = min(self.beam_min, data['beamVelB2_VSR'].min())
        self.beam_max = max(self.beam_max, data['beamVelB2_VSR'].max())

        if display_text:
            # Display the raw data
            st.subheader("Beam Velocity - Beam 2 Raw Data (Vessel Speed Removed)")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Beam Velocity - Beam 2")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['beamB2'].mean(), round_val)
                median_beamVel = round(data['beamB2'].median(), round_val)
                min_beamVel = round(data['beamB2'].min(), round_val)
                max_beamVel = round(data['beamB2'].max(), round_val)
                std_beamVel = round(data['beamB2'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Beam Velocity**")
                mean_beamBtVel = round(data['btVelB2'].mean(), round_val)
                median_beamBtVel = round(data['btVelB2'].median(), round_val)
                min_beamBtVel = round(data['btVelB2'].min(), round_val)
                max_beamBtVel = round(data['btVelB2'].max(), round_val)
                std_beamBtVel = round(data['btVelB2'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

            with col3:
                st.subheader("Beam Velocity")
                st.markdown("**(Vessel Speed Removed)**")
                mean_beamBtVel_vsr = round(data['beamVelB2_VSR'].mean(), round_val)
                median_beamBtVel_vsr = round(data['beamVelB2_VSR'].median(), round_val)
                min_beamBtVel_vsr = round(data['beamVelB2_VSR'].min(), round_val)
                max_beamBtVel_vsr = round(data['beamVelB2_VSR'].max(), round_val)
                std_beamBtVel_vsr = round(data['beamVelB2_VSR'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel_vsr))
                st.markdown("***Average Median: *** " + str(median_beamBtVel_vsr))
                st.markdown("***Min: *** " + str(min_beamBtVel_vsr))
                st.markdown("***Max: *** " + str(max_beamBtVel_vsr))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel_vsr))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['beamVelB2_VSR']

        # Create the plot
        self.beam_b2_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.beam_b2_fig.update_layout(
            title="Beam 2 Velocity",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Beam Velocity - Beam 2 (Vessel Speed Removed)")
            st.plotly_chart(self.beam_b2_fig)

    def beam_3_vel(self, filter_query: str, max_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Beam 3 raw values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param round_val: Round the values displayed to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT dateTIme,bin,binDepth,beam3 FROM ensembles INNER JOIN beamVelocity ON ensembles.id=beamVelocity.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and postive the same
        data['beam3'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['beam3']]

        if display_text:
            # Display the raw data
            st.subheader("Beam Velocity - Beam 3 Raw Data")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Beam Velocity - Beam 3")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['beam3'].mean(), round_val)
            median_beamVel = round(data['beam3'].median(), round_val)
            min_beamVel = round(data['beam3'].min(), round_val)
            max_beamVel = round(data['beam3'].max(), round_val)
            std_beamVel = round(data['beam3'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        if display_plot:
            # Get the data from the query
            st.subheader("Plot Beam Velocity - Beam 3")
            bin_nums = data['bin']
            dates = data['dateTime']
            z = data['beam3']

            # Create the plot
            fig = go.Figure(data=go.Heatmap(
                z=z,
                x=dates,
                y=bin_nums,
                colorscale='Viridis'))

            # Set the layout with downward looking
            fig.update_layout(
                title="Beam 3 Velocity",
                xaxis_title="DateTime",
                yaxis_title="Bin Number",
                yaxis_autorange='reversed'  # Downward looking 'reversed'
            )

            # Add the plot
            st.plotly_chart(fig)

    def beam_3_vel_remove_ship(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Beam 3 raw values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,beamVelocity.bin,beamVelocity.binDepth,beamVelocity.beam3,bottomtrack.beamVelBeam3,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN beamVelocity ON ensembles.id=beamVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"beamVelBeam3": "btVelB3", "beam3": "beamB3"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['beamB3'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['beamB3']]
        data['btVelB3'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelB3']]

        # Remove vessel speed
        # Add the bottom track velocity to remove the velocity
        data['beamVelB3_VSR'] = data['beamB3'] + data['btVelB3']

        # Set the min and max values
        self.beam_min = min(self.beam_min, data['beamVelB3_VSR'].min())
        self.beam_max = max(self.beam_max, data['beamVelB3_VSR'].max())

        if display_text:
            # Display the raw data
            st.subheader("Beam Velocity - Beam 3 Raw Data (Vessel Speed Removed)")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Beam Velocity - Beam 3")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['beamB3'].mean(), round_val)
                median_beamVel = round(data['beamB3'].median(), round_val)
                min_beamVel = round(data['beamB3'].min(), round_val)
                max_beamVel = round(data['beamB3'].max(), round_val)
                std_beamVel = round(data['beamB3'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Beam Velocity**")
                mean_beamBtVel = round(data['btVelB3'].mean(), round_val)
                median_beamBtVel = round(data['btVelB3'].median(), round_val)
                min_beamBtVel = round(data['btVelB3'].min(), round_val)
                max_beamBtVel = round(data['btVelB3'].max(), round_val)
                std_beamBtVel = round(data['btVelB3'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

            with col3:
                st.subheader("Beam Velocity")
                st.markdown("**(Vessel Speed Removed)**")
                mean_beamBtVel_vsr = round(data['beamVelB3_VSR'].mean(), round_val)
                median_beamBtVel_vsr = round(data['beamVelB3_VSR'].median(), round_val)
                min_beamBtVel_vsr = round(data['beamVelB3_VSR'].min(), round_val)
                max_beamBtVel_vsr = round(data['beamVelB3_VSR'].max(), round_val)
                std_beamBtVel_vsr = round(data['beamVelB3_VSR'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel_vsr))
                st.markdown("***Average Median: *** " + str(median_beamBtVel_vsr))
                st.markdown("***Min: *** " + str(min_beamBtVel_vsr))
                st.markdown("***Max: *** " + str(max_beamBtVel_vsr))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel_vsr))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['beamVelB3_VSR']

        # Create the plot
        self.beam_b3_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.beam_b3_fig.update_layout(
            title="Beam 3 Velocity",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Beam Velocity - Beam 3 (Vessel Speed Removed)")
            st.plotly_chart(self.beam_b3_fig)

    def display_beam_vel_plots(self):
        """
        Display the Beam Velocity plots stacked.
        Also save the plots to html files.
        """
        # Make all the min and max match for all plots
        self.beam_b0_fig.data[0].update(zmin=self.beam_min, zmax=self.beam_max, zauto=False, xaxis="x", yaxis="y")
        self.beam_b1_fig.data[0].update(zmin=self.beam_min, zmax=self.beam_max, zauto=False, xaxis="x", yaxis="y")
        self.beam_b2_fig.data[0].update(zmin=self.beam_min, zmax=self.beam_max, zauto=False, xaxis="x", yaxis="y")
        self.beam_b3_fig.data[0].update(zmin=self.beam_min, zmax=self.beam_max, zauto=False, xaxis="x", yaxis="y")

        # Display and save the plot
        #st.plotly_chart(self.beam_b0_fig)
        #self.beam_b0_fig.write_html(self.gen_file_path(file_suffix="_plot_beam_vel_0", file_ext=".html"))

        #st.plotly_chart(self.beam_b1_fig)
        #self.beam_b1_fig.to_html(self.gen_file_path(file_suffix="_plot_beam_vel_1", file_ext=".html"))

        #st.plotly_chart(self.beam_b2_fig)
        #self.beam_b2_fig.to_html(self.gen_file_path(file_suffix="_plot_beam_vel_2", file_ext=".html"))

        #st.plotly_chart(self.beam_b3_fig)
        #self.beam_b3_fig.to_html(self.gen_file_path(file_suffix="_plot_beam_vel_3", file_ext=".html"))

        # Get the min and max for all the plots
        #zmin = min(self.beam_b0_fig.data[0].zmin, self.beam_b1_fig.data[0].zmin, self.beam_b2_fig.data[0].zmin, self.beam_b3_fig.data[0].zmin)
        #zmax = max(self.beam_b0_fig.data[0].zmax, self.beam_b1_fig.data[0].zmax, self.beam_b2_fig.data[0].zmax, self.beam_b3_fig.data[0].zmax)

        self.beam_fig_subplots = make_subplots(rows=4, cols=1, row_titles=("Beam 0", "Beam 1", "Beam 2", "Beam 3"), shared_xaxes="all", shared_yaxes="all")
        self.beam_fig_subplots.update_layout(title_text="Beam Velocity")
        self.beam_fig_subplots.add_trace(self.beam_b0_fig.data[0], row=1, col=1)
        self.beam_fig_subplots.add_trace(self.beam_b1_fig.data[0], row=2, col=1)
        self.beam_fig_subplots.add_trace(self.beam_b2_fig.data[0], row=3, col=1)
        self.beam_fig_subplots.add_trace(self.beam_b3_fig.data[0], row=4, col=1)
        self.beam_fig_subplots.write_html(self.gen_file_path(file_suffix="_plot_beam_vel", file_ext=".html"))
        st.plotly_chart(self.beam_fig_subplots)

    def intr_x_vel_remove_ship(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Instrument X Velocity values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,instrumentVelocity.bin,instrumentVelocity.binDepth,instrumentVelocity.beam0,bottomtrack.instrVelBeam0,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN instrumentVelocity ON ensembles.id=instrumentVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"instrVelBeam0": "btVelX", "beam0": "instrX"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['instrX'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['instrX']]
        data['btVelX'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelX']]

        # Remove vessel speed
        # Add the bottom track velocity to remove the velocity
        data['instrVelX_VSR'] = data['instrX'] + data['btVelX']

        # Set the min and max values
        self.instr_min = min(self.instr_min, data['instrVelX_VSR'].min())
        self.instr_max = max(self.instr_max, data['instrVelX_VSR'].max())

        if display_text:
            # Display the raw data
            st.subheader("Instrument Velocity - X Data (Vessel Speed Removed)")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Instrument Velocity - X")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['instrX'].mean(), round_val)
                median_beamVel = round(data['instrX'].median(), round_val)
                min_beamVel = round(data['instrX'].min(), round_val)
                max_beamVel = round(data['instrX'].max(), round_val)
                std_beamVel = round(data['instrX'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Instrument Velocity**")
                mean_beamBtVel = round(data['btVelX'].mean(), round_val)
                median_beamBtVel = round(data['btVelX'].median(), round_val)
                min_beamBtVel = round(data['btVelX'].min(), round_val)
                max_beamBtVel = round(data['btVelX'].max(), round_val)
                std_beamBtVel = round(data['btVelX'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

            with col3:
                st.subheader("Instrument Velocity")
                st.markdown("**(Vessel Speed Removed)**")
                mean_beamBtVel_vsr = round(data['instrVelX_VSR'].mean(), round_val)
                median_beamBtVel_vsr = round(data['instrVelX_VSR'].median(), round_val)
                min_beamBtVel_vsr = round(data['instrVelX_VSR'].min(), round_val)
                max_beamBtVel_vsr = round(data['instrVelX_VSR'].max(), round_val)
                std_beamBtVel_vsr = round(data['instrVelX_VSR'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel_vsr))
                st.markdown("***Average Median: *** " + str(median_beamBtVel_vsr))
                st.markdown("***Min: *** " + str(min_beamBtVel_vsr))
                st.markdown("***Max: *** " + str(max_beamBtVel_vsr))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel_vsr))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['instrVelX_VSR']

        # Create the plot
        self.instr_x_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.instr_x_fig.update_layout(
            title="Instrument X Velocity",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Instrument - X Velocity (Vessel Speed Removed)")
            st.plotly_chart(self.instr_x_fig)

    def intr_y_vel_remove_ship(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Instrument Y Velocity values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,instrumentVelocity.bin,instrumentVelocity.binDepth,instrumentVelocity.beam1,bottomtrack.instrVelBeam1,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN instrumentVelocity ON ensembles.id=instrumentVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"instrVelBeam1": "btVelY", "beam1": "instrY"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['instrY'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['instrY']]
        data['btVelY'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelY']]

        # Remove vessel speed
        # Add the bottom track velocity to remove the velocity
        data['instrVelY_VSR'] = data['instrY'] + data['btVelY']

        # Set the min and max values
        self.instr_min = min(self.instr_min, data['instrVelY_VSR'].min())
        self.instr_max = max(self.instr_max, data['instrVelY_VSR'].max())

        if display_text:
            # Display the raw data
            st.subheader("Instrument Velocity - Y Data (Vessel Speed Removed)")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Instrument Velocity - Y")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['instrY'].mean(), round_val)
                median_beamVel = round(data['instrY'].median(), round_val)
                min_beamVel = round(data['instrY'].min(), round_val)
                max_beamVel = round(data['instrY'].max(), round_val)
                std_beamVel = round(data['instrY'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Instrument Velocity**")
                mean_beamBtVel = round(data['btVelY'].mean(), round_val)
                median_beamBtVel = round(data['btVelY'].median(), round_val)
                min_beamBtVel = round(data['btVelY'].min(), round_val)
                max_beamBtVel = round(data['btVelY'].max(), round_val)
                std_beamBtVel = round(data['btVelY'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

            with col3:
                st.subheader("Instrument Velocity")
                st.markdown("**(Vessel Speed Removed)**")
                mean_beamBtVel_vsr = round(data['instrVelY_VSR'].mean(), round_val)
                median_beamBtVel_vsr = round(data['instrVelY_VSR'].median(), round_val)
                min_beamBtVel_vsr = round(data['instrVelY_VSR'].min(), round_val)
                max_beamBtVel_vsr = round(data['instrVelY_VSR'].max(), round_val)
                std_beamBtVel_vsr = round(data['instrVelY_VSR'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel_vsr))
                st.markdown("***Average Median: *** " + str(median_beamBtVel_vsr))
                st.markdown("***Min: *** " + str(min_beamBtVel_vsr))
                st.markdown("***Max: *** " + str(max_beamBtVel_vsr))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel_vsr))

        # Get the data from the query

        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['instrVelY_VSR']

        # Create the plot
        self.instr_y_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.instr_y_fig.update_layout(
            title="Instrument Y Velocity",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Instrument Velocity - Y (Vessel Speed Removed)")
            st.plotly_chart(self.instr_y_fig)

    def intr_z_vel_remove_ship(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Instrument Z Velocity values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,instrumentVelocity.bin,instrumentVelocity.binDepth,instrumentVelocity.beam2,bottomtrack.instrVelBeam2,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN instrumentVelocity ON ensembles.id=instrumentVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"instrVelBeam2": "btVelZ", "beam2": "instrZ"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['instrZ'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['instrZ']]
        data['btVelZ'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelZ']]

        # Remove vessel speed
        # Add the bottom track velocity to remove the velocity
        data['instrVelZ_VSR'] = data['instrZ'] + data['btVelZ']

        # Set the min and max values
        self.instr_min = min(self.instr_min, data['instrVelZ_VSR'].min())
        self.instr_max = max(self.instr_max, data['instrVelZ_VSR'].max())

        if display_text:
            # Display the raw data
            st.subheader("Instrument Velocity - Z Data (Vessel Speed Removed)")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Instrument Velocity - Z")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['instrZ'].mean(), round_val)
                median_beamVel = round(data['instrZ'].median(), round_val)
                min_beamVel = round(data['instrZ'].min(), round_val)
                max_beamVel = round(data['instrZ'].max(), round_val)
                std_beamVel = round(data['instrZ'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Instrument Velocity**")
                mean_beamBtVel = round(data['btVelZ'].mean(), round_val)
                median_beamBtVel = round(data['btVelZ'].median(), round_val)
                min_beamBtVel = round(data['btVelZ'].min(), round_val)
                max_beamBtVel = round(data['btVelZ'].max(), round_val)
                std_beamBtVel = round(data['btVelZ'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

            with col3:
                st.subheader("Instrument Velocity")
                st.markdown("**(Vessel Speed Removed)**")
                mean_beamBtVel_vsr = round(data['instrVelZ_VSR'].mean(), round_val)
                median_beamBtVel_vsr = round(data['instrVelZ_VSR'].median(), round_val)
                min_beamBtVel_vsr = round(data['instrVelZ_VSR'].min(), round_val)
                max_beamBtVel_vsr = round(data['instrVelZ_VSR'].max(), round_val)
                std_beamBtVel_vsr = round(data['instrVelZ_VSR'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel_vsr))
                st.markdown("***Average Median: *** " + str(median_beamBtVel_vsr))
                st.markdown("***Min: *** " + str(min_beamBtVel_vsr))
                st.markdown("***Max: *** " + str(max_beamBtVel_vsr))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel_vsr))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['instrVelZ_VSR']

        # Create the plot
        self.instr_z_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.instr_z_fig.update_layout(
            title="Instrument Z Velocity",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Instrument Velocity - Z (Vessel Speed Removed)")
            st.plotly_chart(self.instr_z_fig)

    def intr_err_vel_remove_ship(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Instrument Error Velocity values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,instrumentVelocity.bin,instrumentVelocity.binDepth,instrumentVelocity.beam3,bottomtrack.instrVelBeam3,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN instrumentVelocity ON ensembles.id=instrumentVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"instrVelBeam3": "btVelErr", "beam3": "instrErr"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['instrErr'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['instrErr']]
        data['btVelErr'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelErr']]

        # Remove vessel speed
        # Add the bottom track velocity to remove the velocity
        data['instrVelErr_VSR'] = data['instrErr'] + data['btVelErr']

        # Set the min and max values
        self.instr_min = min(self.instr_min, data['instrVelErr_VSR'].min())
        self.instr_max = max(self.instr_max, data['instrVelErr_VSR'].max())

        if display_text:
            # Display the raw data
            st.subheader("Instrument Velocity - Error Data (Vessel Speed Removed)")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Instrument Velocity - Error")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['instrErr'].mean(), round_val)
                median_beamVel = round(data['instrErr'].median(), round_val)
                min_beamVel = round(data['instrErr'].min(), round_val)
                max_beamVel = round(data['instrErr'].max(), round_val)
                std_beamVel = round(data['instrErr'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Instrument Velocity**")
                mean_beamBtVel = round(data['btVelErr'].mean(), round_val)
                median_beamBtVel = round(data['btVelErr'].median(), round_val)
                min_beamBtVel = round(data['btVelErr'].min(), round_val)
                max_beamBtVel = round(data['btVelErr'].max(), round_val)
                std_beamBtVel = round(data['btVelErr'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

            with col3:
                st.subheader("Instrument Velocity")
                st.markdown("**(Vessel Speed Removed)**")
                mean_beamBtVel_vsr = round(data['instrVelErr_VSR'].mean(), round_val)
                median_beamBtVel_vsr = round(data['instrVelErr_VSR'].median(), round_val)
                min_beamBtVel_vsr = round(data['instrVelErr_VSR'].min(), round_val)
                max_beamBtVel_vsr = round(data['instrVelErr_VSR'].max(), round_val)
                std_beamBtVel_vsr = round(data['instrVelErr_VSR'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel_vsr))
                st.markdown("***Average Median: *** " + str(median_beamBtVel_vsr))
                st.markdown("***Min: *** " + str(min_beamBtVel_vsr))
                st.markdown("***Max: *** " + str(max_beamBtVel_vsr))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel_vsr))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['instrVelErr_VSR']

        # Create the plot
        self.instr_err_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.instr_err_fig.update_layout(
            title="Instrument Error Velocity",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Instrument Velocity - Error (Vessel Speed Removed)")
            st.plotly_chart(self.instr_err_fig)

    def display_instr_vel_plots(self):
        """
        Display all the Instrument Velocity plots stacked.
        """
        # Make all the min and max match for all plots
        self.instr_x_fig.data[0].update(zmin=self.instr_min, zmax=self.instr_max, zauto=False, xaxis="x", yaxis="y")
        self.instr_y_fig.data[0].update(zmin=self.instr_min, zmax=self.instr_max, zauto=False, xaxis="x", yaxis="y")
        self.instr_z_fig.data[0].update(zmin=self.instr_min, zmax=self.instr_max, zauto=False, xaxis="x", yaxis="y")
        self.instr_err_fig.data[0].update(zmin=self.instr_min, zmax=self.instr_max, zauto=False, xaxis="x", yaxis="y")

        # Add the plot
        #st.plotly_chart(self.instr_x_fig)
        #st.plotly_chart(self.instr_y_fig)
        #st.plotly_chart(self.instr_z_fig)
        #st.plotly_chart(self.instr_err_fig)

        self.instr_fig_subplots = make_subplots(rows=4, cols=1, row_titles=("X", "Y", "Z", "Error"), shared_xaxes="all", shared_yaxes="all")
        self.instr_fig_subplots.update_layout(title_text="Instrument Velocity")
        self.instr_fig_subplots.add_trace(self.instr_x_fig.data[0], row=1, col=1)
        self.instr_fig_subplots.add_trace(self.instr_y_fig.data[0], row=2, col=1)
        self.instr_fig_subplots.add_trace(self.instr_z_fig.data[0], row=3, col=1)
        self.instr_fig_subplots.add_trace(self.instr_err_fig.data[0], row=4, col=1)
        self.instr_fig_subplots.write_html(self.gen_file_path(file_suffix="_plot_instr_vel", file_ext=".html"))
        st.plotly_chart(self.instr_fig_subplots)

    def earth_east_vel(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Earth East Velocity values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,earthVelocity.bin,earthVelocity.binDepth,earthVelocity.beam0,bottomtrack.earthVelBeam0,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN earthVelocity ON ensembles.id=earthVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"earthVelBeam0": "btVelEast", "beam0": "earthEast"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['earthEast'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['earthEast']]
        data['btVelEast'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelEast']]

        if display_text:
            # Display the raw data
            st.subheader("Earth Velocity - East Data")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Earth Velocity - East")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['earthEast'].mean(), round_val)
                median_beamVel = round(data['earthEast'].median(), round_val)
                min_beamVel = round(data['earthEast'].min(), round_val)
                max_beamVel = round(data['earthEast'].max(), round_val)
                std_beamVel = round(data['earthEast'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Earth Velocity**")
                mean_beamBtVel = round(data['btVelEast'].mean(), round_val)
                median_beamBtVel = round(data['btVelEast'].median(), round_val)
                min_beamBtVel = round(data['btVelEast'].min(), round_val)
                max_beamBtVel = round(data['btVelEast'].max(), round_val)
                std_beamBtVel = round(data['btVelEast'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['earthEast']

        # Create the plot
        self.earth_east_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.earth_east_fig.update_layout(
            title="Earth East Velocity",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Earth - East Velocity")
            st.plotly_chart(self.earth_east_fig)

    def earth_north_vel(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Earth North Velocity values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,earthVelocity.bin,earthVelocity.binDepth,earthVelocity.beam1,bottomtrack.earthVelBeam1,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN earthVelocity ON ensembles.id=earthVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"earthVelBeam1": "btVelNorth", "beam1": "earthNorth"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['earthNorth'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['earthNorth']]
        data['btVelNorth'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelNorth']]

        if display_text:
            # Display the raw data
            st.subheader("Earth Velocity - North Data")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Earth Velocity - North")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['earthNorth'].mean(), round_val)
                median_beamVel = round(data['earthNorth'].median(), round_val)
                min_beamVel = round(data['earthNorth'].min(), round_val)
                max_beamVel = round(data['earthNorth'].max(), round_val)
                std_beamVel = round(data['earthNorth'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Earth Velocity**")
                mean_beamBtVel = round(data['btVelNorth'].mean(), round_val)
                median_beamBtVel = round(data['btVelNorth'].median(), round_val)
                min_beamBtVel = round(data['btVelNorth'].min(), round_val)
                max_beamBtVel = round(data['btVelNorth'].max(), round_val)
                std_beamBtVel = round(data['btVelNorth'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['earthNorth']

        # Create the plot
        self.earth_north_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.earth_north_fig.update_layout(
            title="Earth North Velocity",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Earth - North Velocity")
            st.plotly_chart(self.earth_north_fig)

    def earth_vert_vel(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Earth Vertical Velocity values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,earthVelocity.bin,earthVelocity.binDepth,earthVelocity.beam2,bottomtrack.earthVelBeam2,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN earthVelocity ON ensembles.id=earthVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"earthVelBeam2": "btVelVert", "beam2": "earthVert"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['earthVert'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['earthVert']]
        data['btVelVert'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelVert']]

        if display_text:
            # Display the raw data
            st.subheader("Earth Velocity - Vertical Data")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Earth Velocity - Vertical")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['earthVert'].mean(), round_val)
                median_beamVel = round(data['earthVert'].median(), round_val)
                min_beamVel = round(data['earthVert'].min(), round_val)
                max_beamVel = round(data['earthVert'].max(), round_val)
                std_beamVel = round(data['earthVert'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Earth Velocity**")
                mean_beamBtVel = round(data['btVelVert'].mean(), round_val)
                median_beamBtVel = round(data['btVelVert'].median(), round_val)
                min_beamBtVel = round(data['btVelVert'].min(), round_val)
                max_beamBtVel = round(data['btVelVert'].max(), round_val)
                std_beamBtVel = round(data['btVelVert'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['earthVert']

        # Create the plot
        self.earth_vert_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.earth_vert_fig.update_layout(
            title="Earth Vertical Velocity",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Earth - Vertical Velocity")
            st.plotly_chart(self.earth_vert_fig)

    def earth_east_vel_remove_ship(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Earth East Velocity values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,earthVelocity.bin,earthVelocity.binDepth,earthVelocity.beam0,bottomtrack.earthVelBeam0,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN earthVelocity ON ensembles.id=earthVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"earthVelBeam0": "btVelEast", "beam0": "earthEast"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['earthEast'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['earthEast']]
        data['btVelEast'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelEast']]

        # Remove vessel speed
        # Add the bottom track velocity to remove the velocity
        data['earthVelEast_VSR'] = data['earthEast'] + data['btVelEast']

        # Set the min and max values
        self.earth_vsr_min = min(self.earth_min, data['earthVelEast_VSR'].min())
        self.earth_vsr_max = max(self.earth_max, data['earthVelEast_VSR'].max())

        if display_text:
            # Display the raw data
            st.subheader("Earth Velocity - East Data (Vessel Speed Removed)")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Earth Velocity - East")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['earthEast'].mean(), round_val)
                median_beamVel = round(data['earthEast'].median(), round_val)
                min_beamVel = round(data['earthEast'].min(), round_val)
                max_beamVel = round(data['earthEast'].max(), round_val)
                std_beamVel = round(data['earthEast'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Earth Velocity**")
                mean_beamBtVel = round(data['btVelEast'].mean(), round_val)
                median_beamBtVel = round(data['btVelEast'].median(), round_val)
                min_beamBtVel = round(data['btVelEast'].min(), round_val)
                max_beamBtVel = round(data['btVelEast'].max(), round_val)
                std_beamBtVel = round(data['btVelEast'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

            with col3:
                st.subheader("Earth Velocity")
                st.markdown("**(Vessel Speed Removed)**")
                mean_beamBtVel_vsr = round(data['earthVelEast_VSR'].mean(), round_val)
                median_beamBtVel_vsr = round(data['earthVelEast_VSR'].median(), round_val)
                min_beamBtVel_vsr = round(data['earthVelEast_VSR'].min(), round_val)
                max_beamBtVel_vsr = round(data['earthVelEast_VSR'].max(), round_val)
                std_beamBtVel_vsr = round(data['earthVelEast_VSR'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel_vsr))
                st.markdown("***Average Median: *** " + str(median_beamBtVel_vsr))
                st.markdown("***Min: *** " + str(min_beamBtVel_vsr))
                st.markdown("***Max: *** " + str(max_beamBtVel_vsr))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel_vsr))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['earthVelEast_VSR']

        # Create the plot
        self.earth_east_vsr_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.earth_east_vsr_fig.update_layout(
            title="Earth East Velocity",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Earth - East Velocity (Vessel Speed Removed)")
            st.plotly_chart(self.earth_east_vsr_fig)

    def earth_north_vel_remove_ship(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Earth North Velocity values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,earthVelocity.bin,earthVelocity.binDepth,earthVelocity.beam1,bottomtrack.earthVelBeam1,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN earthVelocity ON ensembles.id=earthVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"earthVelBeam1": "btVelNorth", "beam1": "earthNorth"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['earthNorth'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['earthNorth']]
        data['btVelNorth'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelNorth']]

        # Remove vessel speed
        # Add the bottom track velocity to remove the velocity
        data['earthVelNorth_VSR'] = data['earthNorth'] + data['btVelNorth']

        # Set the min and max values
        self.earth_vsr_min = min(self.earth_min, data['earthVelNorth_VSR'].min())
        self.earth_vsr_max = max(self.earth_max, data['earthVelNorth_VSR'].max())

        if display_text:
            # Display the raw data
            st.subheader("Earth Velocity - North Data (Vessel Speed Removed)")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Earth Velocity - North")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['earthNorth'].mean(), round_val)
                median_beamVel = round(data['earthNorth'].median(), round_val)
                min_beamVel = round(data['earthNorth'].min(), round_val)
                max_beamVel = round(data['earthNorth'].max(), round_val)
                std_beamVel = round(data['earthNorth'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Earth Velocity**")
                mean_beamBtVel = round(data['btVelNorth'].mean(), round_val)
                median_beamBtVel = round(data['btVelNorth'].median(), round_val)
                min_beamBtVel = round(data['btVelNorth'].min(), round_val)
                max_beamBtVel = round(data['btVelNorth'].max(), round_val)
                std_beamBtVel = round(data['btVelNorth'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

            with col3:
                st.subheader("Earth Velocity")
                st.markdown("**(Vessel Speed Removed)**")
                mean_beamBtVel_vsr = round(data['earthVelNorth_VSR'].mean(), round_val)
                median_beamBtVel_vsr = round(data['earthVelNorth_VSR'].median(), round_val)
                min_beamBtVel_vsr = round(data['earthVelNorth_VSR'].min(), round_val)
                max_beamBtVel_vsr = round(data['earthVelNorth_VSR'].max(), round_val)
                std_beamBtVel_vsr = round(data['earthVelNorth_VSR'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel_vsr))
                st.markdown("***Average Median: *** " + str(median_beamBtVel_vsr))
                st.markdown("***Min: *** " + str(min_beamBtVel_vsr))
                st.markdown("***Max: *** " + str(max_beamBtVel_vsr))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel_vsr))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['earthVelNorth_VSR']

        # Create the plot
        self.earth_north_vsr_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.earth_north_vsr_fig.update_layout(
            title="Earth North Velocity",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Earth - North Velocity (Vessel Speed Removed)")
            st.plotly_chart(self.earth_north_vsr_fig)

    def earth_vert_vel_remove_ship(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Earth Vertical Velocity values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,earthVelocity.bin,earthVelocity.binDepth,earthVelocity.beam2,bottomtrack.earthVelBeam2,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN earthVelocity ON ensembles.id=earthVelocity.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        data.rename(columns={"earthVelBeam2": "btVelVert", "beam2": "earthVert"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['earthVert'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['earthVert']]
        data['btVelVert'] = [x if abs(x) < abs(max_bt_vel) else np.nan for x in data['btVelVert']]

        # Remove vessel speed
        # Add the bottom track velocity to remove the velocity
        data['earthVelVert_VSR'] = data['earthVert'] + data['btVelVert']

        # Set the min and max values
        self.earth_vsr_min = min(self.earth_min, data['earthVelVert_VSR'].min())
        self.earth_vsr_max = max(self.earth_max, data['earthVelVert_VSR'].max())

        if display_text:
            # Display the raw data
            st.subheader("Earth Velocity - Vertical Data (Vessel Speed Removed)")
            st.write(data)

        if display_stats:
            col1, col2, col3 = st.beta_columns(3)

            with col1:
                # Display the stats of the data
                st.subheader("Earth Velocity - Vertical")
                st.markdown("**(Raw)**")
                mean_beamVel = round(data['earthVert'].mean(), round_val)
                median_beamVel = round(data['earthVert'].median(), round_val)
                min_beamVel = round(data['earthVert'].min(), round_val)
                max_beamVel = round(data['earthVert'].max(), round_val)
                std_beamVel = round(data['earthVert'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamVel))
                st.markdown("***Average Median: *** " + str(median_beamVel))
                st.markdown("***Min: *** " + str(min_beamVel))
                st.markdown("***Max: *** " + str(max_beamVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamVel))

            with col2:
                st.subheader("Bottom Track")
                st.markdown("**Earth Velocity**")
                mean_beamBtVel = round(data['btVelVert'].mean(), round_val)
                median_beamBtVel = round(data['btVelVert'].median(), round_val)
                min_beamBtVel = round(data['btVelVert'].min(), round_val)
                max_beamBtVel = round(data['btVelVert'].max(), round_val)
                std_beamBtVel = round(data['btVelVert'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel))
                st.markdown("***Average Median: *** " + str(median_beamBtVel))
                st.markdown("***Min: *** " + str(min_beamBtVel))
                st.markdown("***Max: *** " + str(max_beamBtVel))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel))

            with col3:
                st.subheader("Earth Velocity")
                st.markdown("**(Vessel Speed Removed)**")
                mean_beamBtVel_vsr = round(data['earthVelVert_VSR'].mean(), round_val)
                median_beamBtVel_vsr = round(data['earthVelVert_VSR'].median(), round_val)
                min_beamBtVel_vsr = round(data['earthVelVert_VSR'].min(), round_val)
                max_beamBtVel_vsr = round(data['earthVelVert_VSR'].max(), round_val)
                std_beamBtVel_vsr = round(data['earthVelVert_VSR'].std(), round_val)
                st.markdown("***Average Mean: *** " + str(mean_beamBtVel_vsr))
                st.markdown("***Average Median: *** " + str(median_beamBtVel_vsr))
                st.markdown("***Min: *** " + str(min_beamBtVel_vsr))
                st.markdown("***Max: *** " + str(max_beamBtVel_vsr))
                st.markdown("***Standard Deviation: *** " + str(std_beamBtVel_vsr))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['earthVelVert_VSR']

        # Create the plot
        self.earth_vert_vsr_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.earth_vert_vsr_fig.update_layout(
            title="Earth Vertical Velocity",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Earth - Vertical Velocity (Vessel Speed Removed)")
            st.plotly_chart(self.earth_vert_vsr_fig)

    def display_earth_vel_plots(self):
        """
        Display all the Earth Velocity plots stacked.
        """
        # Make all the min and max match for all plots
        self.earth_east_vsr_fig.data[0].update(zmin=self.earth_min, zmax=self.earth_max, zauto=False, xaxis="x", yaxis="y")
        self.earth_north_vsr_fig.data[0].update(zmin=self.earth_min, zmax=self.earth_max, zauto=False, xaxis="x", yaxis="y")
        self.earth_vert_vsr_fig.data[0].update(zmin=self.earth_min, zmax=self.earth_max, zauto=False, xaxis="x", yaxis="y")
        self.instr_err_fig.data[0].update(zmin=self.earth_min, zmax=self.earth_max, zauto=False, xaxis="x", yaxis="y")

        # Add Earth plots
        self.earth_fig_subplots = make_subplots(rows=4, cols=1, row_titles=("East", "North", "Vertical", "Error"), shared_xaxes="all", shared_yaxes="all")
        self.earth_fig_subplots.update_layout(title_text="Earth Velocity")
        self.earth_fig_subplots.add_trace(self.earth_east_vsr_fig.data[0], row=1, col=1)
        self.earth_fig_subplots.add_trace(self.earth_north_vsr_fig.data[0], row=2, col=1)
        self.earth_fig_subplots.add_trace(self.earth_vert_vsr_fig.data[0], row=3, col=1)
        self.earth_fig_subplots.add_trace(self.instr_err_fig.data[0], row=4, col=1)
        self.earth_fig_subplots.write_html(self.gen_file_path(file_suffix="_plot_earth_vel_vsr", file_ext=".html"))
        st.plotly_chart(self.earth_fig_subplots)

    def display_earth_vel_raw_vsr_plots(self):
        """
        Display the Earth Velocity plot as raw and Vessel Speed Removed stacked.
        """
        e_min = min(self.earth_min, self.earth_vsr_min)
        e_max = max(self.earth_max, self.earth_vsr_max)

        # Make all the min and max match for all plots
        self.earth_east_vsr_fig.data[0].update(zmin=e_min, zmax=e_max, zauto=False, xaxis="x", yaxis="y")
        self.earth_north_vsr_fig.data[0].update(zmin=e_min, zmax=e_max, zauto=False, xaxis="x", yaxis="y")
        self.earth_vert_vsr_fig.data[0].update(zmin=e_min, zmax=e_max, zauto=False, xaxis="x", yaxis="y")
        self.instr_err_fig.data[0].update(zmin=e_min, zmax=e_max, zauto=False, xaxis="x", yaxis="y")

        self.earth_east_fig.data[0].update(zmin=e_min, zmax=e_max, zauto=False, xaxis="x", yaxis="y")
        self.earth_north_fig.data[0].update(zmin=e_min, zmax=e_max, zauto=False, xaxis="x", yaxis="y")
        self.earth_vert_fig.data[0].update(zmin=e_min, zmax=e_max, zauto=False, xaxis="x", yaxis="y")
        self.instr_err_fig.data[0].update(zmin=e_min, zmax=e_max, zauto=False, xaxis="x", yaxis="y")

        # Add the plots to the subplot
        self.earth_raw_vsr_fig_subplots = make_subplots(rows=8,
                                                        cols=1,
                                                        row_titles=("East", "North", "Vertical", "Error", "East VSR", "North VSR", "Vertical VSR", "Error"),
                                                        shared_xaxes="all",     # Share zoom with all plots
                                                        shared_yaxes="all")     # Share zoom with all plots

        self.earth_raw_vsr_fig_subplots.update_layout(title_text="Earth Velocity")
        self.earth_raw_vsr_fig_subplots.add_trace(self.earth_east_fig.data[0], row=1, col=1)
        self.earth_raw_vsr_fig_subplots.add_trace(self.earth_north_fig.data[0], row=2, col=1)
        self.earth_raw_vsr_fig_subplots.add_trace(self.earth_vert_fig.data[0], row=3, col=1)
        self.earth_raw_vsr_fig_subplots.add_trace(self.instr_err_fig.data[0], row=4, col=1)
        self.earth_raw_vsr_fig_subplots.add_trace(self.earth_east_vsr_fig.data[0], row=5, col=1)
        self.earth_raw_vsr_fig_subplots.add_trace(self.earth_north_vsr_fig.data[0], row=6, col=1)
        self.earth_raw_vsr_fig_subplots.add_trace(self.earth_vert_vsr_fig.data[0], row=7, col=1)
        self.earth_raw_vsr_fig_subplots.add_trace(self.instr_err_fig.data[0], row=8, col=1)
        self.earth_raw_vsr_fig_subplots.write_html(self.gen_file_path(file_suffix="_plot_earth_vel_raw_vsr", file_ext=".html"))
        st.plotly_chart(self.earth_raw_vsr_fig_subplots)

    def mag_plot(self, filter_query: str, max_mag: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Water Magnitude Raw values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_mag: Maximum Magnitude velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,earthMagDir.bin,earthMagDir.binDepth,earthMagDir.rawMag,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN earthMagDir ON ensembles.id=earthMagDir.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        #data.rename(columns={"earthVelBeam2": "btVelVert", "beam2": "earthVert"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['rawMag'] = [x if abs(x) < abs(max_mag) else np.nan for x in data['rawMag']]

        # Set the min and max values
        self.mag_min = min(self.mag_min, data['rawMag'].min())
        self.mag_max = max(self.mag_max, data['rawMag'].max())

        if display_text:
            # Display the raw data
            st.subheader("Water Magnitude")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Water Magnitude")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['rawMag'].mean(), round_val)
            median_beamVel = round(data['rawMag'].median(), round_val)
            min_beamVel = round(data['rawMag'].min(), round_val)
            max_beamVel = round(data['rawMag'].max(), round_val)
            std_beamVel = round(data['rawMag'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['rawMag']

        # Create the plot
        self.mag_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.mag_fig.update_layout(
            title="Water Magnitude",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Water Magnitude")
            st.plotly_chart(self.mag_fig)

    def dir_plot(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Water Direction Raw values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,earthMagDir.bin,earthMagDir.binDepth,earthMagDir.rawDir,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN earthMagDir ON ensembles.id=earthMagDir.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        #data.rename(columns={"earthVelBeam2": "btVelVert", "beam2": "earthVert"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        #data['dir'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['dir']]

        if display_text:
            # Display the raw data
            st.subheader("Water Direction")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Water Direction")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['rawDir'].mean(), round_val)
            median_beamVel = round(data['rawDir'].median(), round_val)
            min_beamVel = round(data['rawDir'].min(), round_val)
            max_beamVel = round(data['rawDir'].max(), round_val)
            std_beamVel = round(data['rawDir'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['rawDir']

        # Create the plot
        self.dir_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.dir_fig.update_layout(
            title="Water Direction",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Water Direction")
            st.plotly_chart(self.dir_fig)

    def mag_vsr_plot(self, filter_query: str, max_mag: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Water Magnitude values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_mag: Maximum Magnitude velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,earthMagDir.bin,earthMagDir.binDepth,earthMagDir.mag,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN earthMagDir ON ensembles.id=earthMagDir.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        #data.rename(columns={"earthVelBeam2": "btVelVert", "beam2": "earthVert"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        data['mag'] = [x if abs(x) < abs(max_mag) else np.nan for x in data['mag']]

        # Set the min and max values
        self.mag_vsr_min = min(self.mag_vsr_min, data['mag'].min())
        self.mag_vsr_max = max(self.mag_vsr_max, data['mag'].max())

        if display_text:
            # Display the raw data
            st.subheader("Water Magnitude - (Vessel Speed Removed)")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Water Magnitude")
            st.markdown("**(Vessel Speed Removed)**")
            mean_beamVel = round(data['mag'].mean(), round_val)
            median_beamVel = round(data['mag'].median(), round_val)
            min_beamVel = round(data['mag'].min(), round_val)
            max_beamVel = round(data['mag'].max(), round_val)
            std_beamVel = round(data['mag'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['mag']

        # Create the plot
        self.mag_vsr_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.mag_vsr_fig.update_layout(
            title="Water Magnitude",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Water Magnitude (Vessel Speed Removed)")
            st.plotly_chart(self.mag_vsr_fig)

    def dir_vsr_plot(self, filter_query: str, max_vel: float = 88.0, max_bt_vel: float = 88.0, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Water Direction values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param max_vel: Maximum velocity to allow.  Bad Velocity is 88.888
        :param max_bt_vel: Maximum Bottom Track Velocity to allow.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,earthMagDir.bin,earthMagDir.binDepth,earthMagDir.dir,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN earthMagDir ON ensembles.id=earthMagDir.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Rename the columns so we know which column is bottom track
        #data.rename(columns={"earthVelBeam2": "btVelVert", "beam2": "earthVert"}, inplace=True)

        # Clean up data
        # Check if the number exceeds the max value
        # Use absolute value to handle negative and positive the same
        #data['dir'] = [x if abs(x) < abs(max_vel) else np.nan for x in data['dir']]

        if display_text:
            # Display the raw data
            st.subheader("Water Direction - (Vessel Speed Removed)")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Water Direction")
            st.markdown("**(Vessel Speed Removed)**")
            mean_beamVel = round(data['dir'].mean(), round_val)
            median_beamVel = round(data['dir'].median(), round_val)
            min_beamVel = round(data['dir'].min(), round_val)
            max_beamVel = round(data['dir'].max(), round_val)
            std_beamVel = round(data['dir'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['dir']

        # Create the plot
        self.dir_vsr_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.dir_vsr_fig.update_layout(
            title="Water Direction",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Plot Water Direction (Vessel Speed Removed)")
            st.plotly_chart(self.dir_vsr_fig)

    def display_mag_dir_plots(self):
        """
        Display the magnitude and direction plot together.
        """
        # Create 2 different color bars
        # Make the mags and dir overlap
        self.mag_fig.data[0].update(colorbar=dict(len=0.40, y=0.80))
        self.dir_fig.data[0].update(colorbar=dict(len=0.40, y=0.20))
        self.mag_vsr_fig.data[0].update(colorbar=dict(len=0.40, y=0.80))
        self.dir_vsr_fig.data[0].update(colorbar=dict(len=0.40, y=0.20))

        e_min = min(self.mag_min, self.mag_vsr_min)
        e_max = max(self.mag_max, self.mag_vsr_max)

        # Make all the min and max match for all plots
        self.mag_fig.data[0].update(zmin=e_min, zmax=e_max, zauto=False, xaxis="x", yaxis="y")
        self.dir_fig.data[0].update(zmin=0, zmax=360, zauto=False, xaxis="x", yaxis="y")
        self.mag_vsr_fig.data[0].update(zmin=e_min, zmax=e_max, zauto=False, xaxis="x", yaxis="y")
        self.dir_vsr_fig.data[0].update(zmin=0, zmax=360, zauto=False, xaxis="x", yaxis="y")

        self.magdir_fig_subplots = make_subplots(rows=4,                                        # Number of rows
                                                 cols=1,                                        # Number of columns
                                                 row_titles=("Magnitude", "Mag VSR", "Direction", "Dir VSR"),         # Plot titles
                                                 shared_xaxes="all",                            # Share movement in X axis
                                                 shared_yaxes="all",                            # Share movement in Y axis
                                                 vertical_spacing=0.05)                         # Spacing between plots

        self.magdir_fig_subplots.update_layout(title_text="Magnitude and Direction")

        self.magdir_fig_subplots.add_trace(self.mag_fig.data[0], row=1, col=1)
        self.magdir_fig_subplots.add_trace(self.mag_vsr_fig.data[0], row=2, col=1)

        self.magdir_fig_subplots.add_trace(self.dir_fig.data[0], row=3, col=1)
        self.magdir_fig_subplots.add_trace(self.dir_vsr_fig.data[0], row=4, col=1)

        self.magdir_fig_subplots.write_html(self.gen_file_path(file_suffix="_plot_mag_dir_raw_vsr", file_ext=".html"))
        st.plotly_chart(self.magdir_fig_subplots)

    def amp_b0(self, filter_query: str, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Amplitude Beam 0 values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,amplitude.bin,amplitude.binDepth,amplitude.beam0,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN amplitude ON ensembles.id=amplitude.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Set the min and max values
        self.amp_min = min(self.amp_min, data['beam0'].min())
        self.amp_max = max(self.amp_max, data['beam0'].max())

        if display_text:
            # Display the raw data
            st.subheader("Amplitude - Beam 0")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Amplitude - Beam 0")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['beam0'].mean(), round_val)
            median_beamVel = round(data['beam0'].median(), round_val)
            min_beamVel = round(data['beam0'].min(), round_val)
            max_beamVel = round(data['beam0'].max(), round_val)
            std_beamVel = round(data['beam0'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['beam0']

        # Create the plot
        self.amp_b0_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.amp_b0_fig.update_layout(
            title="Amplitude - Beam 0",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Amplitude - Beam 0")
            st.plotly_chart(self.amp_b0_fig)

    def amp_b1(self, filter_query: str, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Amplitude Beam 1 values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,amplitude.bin,amplitude.binDepth,amplitude.beam1,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN amplitude ON ensembles.id=amplitude.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Set the min and max values
        self.amp_min = min(self.amp_min, data['beam1'].min())
        self.amp_max = max(self.amp_max, data['beam1'].max())

        if display_text:
            # Display the raw data
            st.subheader("Amplitude - Beam 1")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Amplitude - Beam 1")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['beam1'].mean(), round_val)
            median_beamVel = round(data['beam1'].median(), round_val)
            min_beamVel = round(data['beam1'].min(), round_val)
            max_beamVel = round(data['beam1'].max(), round_val)
            std_beamVel = round(data['beam1'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['beam1']

        # Create the plot
        self.amp_b1_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.amp_b1_fig.update_layout(
            title="Amplitude - Beam 0",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Amplitude - Beam 1")
            st.plotly_chart(self.amp_b1_fig)

    def amp_b2(self, filter_query: str, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Amplitude Beam 2 values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,amplitude.bin,amplitude.binDepth,amplitude.beam2,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN amplitude ON ensembles.id=amplitude.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Set the min and max values
        self.amp_min = min(self.amp_min, data['beam2'].min())
        self.amp_max = max(self.amp_max, data['beam2'].max())

        if display_text:
            # Display the raw data
            st.subheader("Amplitude - Beam 2")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Amplitude - Beam 2")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['beam2'].mean(), round_val)
            median_beamVel = round(data['beam2'].median(), round_val)
            min_beamVel = round(data['beam2'].min(), round_val)
            max_beamVel = round(data['beam2'].max(), round_val)
            std_beamVel = round(data['beam2'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['beam2']

        # Create the plot
        self.amp_b2_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.amp_b2_fig.update_layout(
            title="Amplitude - Beam 0",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Amplitude - Beam 2")
            st.plotly_chart(self.amp_b2_fig)

    def amp_b3(self, filter_query: str, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Amplitude Beam 3 values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,amplitude.bin,amplitude.binDepth,amplitude.beam3,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN amplitude ON ensembles.id=amplitude.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Set the min and max values
        self.amp_min = min(self.amp_min, data['beam3'].min())
        self.amp_max = max(self.amp_max, data['beam3'].max())

        if display_text:
            # Display the raw data
            st.subheader("Amplitude - Beam 3")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Amplitude - Beam 3")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['beam3'].mean(), round_val)
            median_beamVel = round(data['beam3'].median(), round_val)
            min_beamVel = round(data['beam3'].min(), round_val)
            max_beamVel = round(data['beam3'].max(), round_val)
            std_beamVel = round(data['beam3'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['beam3']

        # Create the plot
        self.amp_b3_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.amp_b3_fig.update_layout(
            title="Amplitude - Beam 0",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Amplitude - Beam 3")
            st.plotly_chart(self.amp_b3_fig)

    def display_amp_plots(self):
        """
        Display all the Amplitude plots stacked.
        """
        # Make all the min and max match for all plots
        self.amp_b0_fig.data[0].update(zmin=self.amp_min, zmax=self.amp_max, zauto=False, xaxis="x", yaxis="y")
        self.amp_b1_fig.data[0].update(zmin=self.amp_min, zmax=self.amp_max, zauto=False, xaxis="x", yaxis="y")
        self.amp_b2_fig.data[0].update(zmin=self.amp_min, zmax=self.amp_max, zauto=False, xaxis="x", yaxis="y")
        self.amp_b3_fig.data[0].update(zmin=self.amp_min, zmax=self.amp_max, zauto=False, xaxis="x", yaxis="y")

        # Add Earth plots
        self.amp_fig_subplots = make_subplots(rows=4, cols=1, row_titles=("East", "North", "Vertical", "Error"), shared_xaxes="all", shared_yaxes="all")
        self.amp_fig_subplots.update_layout(title_text="Amplitude")
        self.amp_fig_subplots.add_trace(self.amp_b0_fig.data[0], row=1, col=1)
        self.amp_fig_subplots.add_trace(self.amp_b1_fig.data[0], row=2, col=1)
        self.amp_fig_subplots.add_trace(self.amp_b2_fig.data[0], row=3, col=1)
        self.amp_fig_subplots.add_trace(self.amp_b3_fig.data[0], row=4, col=1)
        self.amp_fig_subplots.write_html(self.gen_file_path(file_suffix="_plot_amp", file_ext=".html"))
        st.plotly_chart(self.amp_fig_subplots)

    def corr_b0(self, filter_query: str, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Correlation Beam 0 values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,correlation.bin,correlation.binDepth,correlation.beam0,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN correlation ON ensembles.id=correlation.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Set the min and max values
        self.corr_min = min(self.corr_min, data['beam0'].min())
        self.corr_max = max(self.corr_max, data['beam0'].max())

        if display_text:
            # Display the raw data
            st.subheader("Correlation - Beam 0")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Correlation - Beam 0")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['beam0'].mean(), round_val)
            median_beamVel = round(data['beam0'].median(), round_val)
            min_beamVel = round(data['beam0'].min(), round_val)
            max_beamVel = round(data['beam0'].max(), round_val)
            std_beamVel = round(data['beam0'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['beam0']

        # Create the plot
        self.corr_b0_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.corr_b0_fig.update_layout(
            title="Correlation - Beam 0",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Correlation - Beam 0")
            st.plotly_chart(self.corr_b0_fig)

    def corr_b1(self, filter_query: str, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Correlation Beam 1 values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,correlation.bin,correlation.binDepth,correlation.beam1,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN correlation ON ensembles.id=correlation.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Set the min and max values
        self.corr_min = min(self.corr_min, data['beam1'].min())
        self.corr_max = max(self.corr_max, data['beam1'].max())

        if display_text:
            # Display the raw data
            st.subheader("Correlation - Beam 1")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Correlation - Beam 1")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['beam1'].mean(), round_val)
            median_beamVel = round(data['beam1'].median(), round_val)
            min_beamVel = round(data['beam1'].min(), round_val)
            max_beamVel = round(data['beam1'].max(), round_val)
            std_beamVel = round(data['beam1'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['beam1']

        # Create the plot
        self.corr_b1_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.corr_b1_fig.update_layout(
            title="Correlation - Beam 1",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Correlation - Beam 1")
            st.plotly_chart(self.corr_b1_fig)

    def corr_b2(self, filter_query: str, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Correlation Beam 2 values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTime,correlation.bin,correlation.binDepth,correlation.beam2,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN correlation ON ensembles.id=correlation.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Set the min and max values
        self.corr_min = min(self.corr_min, data['beam2'].min())
        self.corr_max = max(self.corr_max, data['beam2'].max())

        if display_text:
            # Display the raw data
            st.subheader("Correlation - Beam 2")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Correlation - Beam 2")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['beam2'].mean(), round_val)
            median_beamVel = round(data['beam2'].median(), round_val)
            min_beamVel = round(data['beam2'].min(), round_val)
            max_beamVel = round(data['beam2'].max(), round_val)
            std_beamVel = round(data['beam2'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['beam2']

        # Create the plot
        self.corr_b2_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.corr_b2_fig.update_layout(
            title="Correlation - Beam 2",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Correlation - Beam 2")
            st.plotly_chart(self.corr_b2_fig)

    def corr_b3(self, filter_query: str, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Correlation Beam 3 values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTIme,correlation.bin,correlation.binDepth,correlation.beam3,bottomtrack.avgRange " \
                   "FROM ensembles " \
                   "INNER JOIN correlation ON ensembles.id=correlation.ensIndex " \
                   "INNER JOIN bottomtrack ON ensembles.id=bottomtrack.ensIndex " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        # Set the min and max values
        self.corr_min = min(self.corr_min, data['beam3'].min())
        self.corr_max = max(self.corr_max, data['beam3'].max())

        if display_text:
            # Display the raw data
            st.subheader("Correlation - Beam 3")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Correlation - Beam 3")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['beam3'].mean(), round_val)
            median_beamVel = round(data['beam3'].median(), round_val)
            min_beamVel = round(data['beam3'].min(), round_val)
            max_beamVel = round(data['beam3'].max(), round_val)
            std_beamVel = round(data['beam3'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        bin_nums = data['bin']
        dates = data['dateTime']
        z = data['beam3']

        # Create the plot
        self.corr_b3_fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dates,
            y=bin_nums,
            colorscale='Viridis'))

        # Set the layout with downward looking
        self.corr_b3_fig.update_layout(
            title="Correlation - Beam 2",
            xaxis_title="DateTime",
            yaxis_title="Bin Number",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Correlation - Beam 3")
            st.plotly_chart(self.corr_b3_fig)

    def display_corr_plots(self):
        """
        Display all the Correlation plots stacked.
        """
        # Make all the min and max match for all plots
        self.corr_b0_fig.data[0].update(zmin=self.corr_min, zmax=self.corr_max, zauto=False, xaxis="x", yaxis="y")
        self.corr_b1_fig.data[0].update(zmin=self.corr_min, zmax=self.corr_max, zauto=False, xaxis="x", yaxis="y")
        self.corr_b2_fig.data[0].update(zmin=self.corr_min, zmax=self.corr_max, zauto=False, xaxis="x", yaxis="y")
        self.corr_b3_fig.data[0].update(zmin=self.corr_min, zmax=self.corr_max, zauto=False, xaxis="x", yaxis="y")

        # Add plots
        self.corr_fig_subplots = make_subplots(rows=4, cols=1, row_titles=("B0", "B1", "B2", "B3"), shared_xaxes="all", shared_yaxes="all")
        self.corr_fig_subplots.update_layout(title_text="Correlation")
        self.corr_fig_subplots.add_trace(self.corr_b0_fig.data[0], row=1, col=1)
        self.corr_fig_subplots.add_trace(self.corr_b1_fig.data[0], row=2, col=1)
        self.corr_fig_subplots.add_trace(self.corr_b2_fig.data[0], row=3, col=1)
        self.corr_fig_subplots.add_trace(self.corr_b3_fig.data[0], row=4, col=1)
        self.corr_fig_subplots.write_html(self.gen_file_path(file_suffix="_plot_corr", file_ext=".html"))
        st.plotly_chart(self.corr_fig_subplots)

    def water_temp(self, filter_query: str, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the Water Temperature values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTime,  ensembles.waterTemp " \
                   "FROM ensembles " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        if display_text:
            # Display the raw data
            st.subheader("Water Temperature (C)")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("Water Temperature (C)")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['waterTemp'].mean(), round_val)
            median_beamVel = round(data['waterTemp'].median(), round_val)
            min_beamVel = round(data['waterTemp'].min(), round_val)
            max_beamVel = round(data['waterTemp'].max(), round_val)
            std_beamVel = round(data['waterTemp'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        temps = data['waterTemp']
        dates = data['dateTime']

        # Create the plot
        self.water_temp_fig = go.Figure(data=go.Scatter(
            x=dates,
            y=temps))

        # Set the layout with downward looking
        self.water_temp_fig.update_layout(
            title="Water Temperature (C)",
            xaxis_title="DateTime",
            yaxis_title="Temperature (C)",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("Water Temperature (C)")
            st.plotly_chart(self.water_temp_fig)

    def system_temp(self, filter_query: str, round_val: int = 3, display_text: bool = True, display_stats: bool = True, display_plot: bool = True):
        """
        Get the System Temperature values.  Display and plot the data.  Use the filter query
        to filter the data.

        :param filter_query: Filter string to run in the query.
        :param round_val: Round the stat values to this decimal place.
        :param display_text: Flag if the data should be displayed by streamlit.
        :param display_stats: Flag if the stats should be displayed by streamlit.
        :param display_plot: Flag if the plot should be displayed by streamlit.
        """
        bv_query = "SELECT ensembles.ensNum,ensembles.dateTime,  ensembles.sysTemp " \
                   "FROM ensembles " + filter_query + ";"
        data = self.query_data(self.project.file_path, query=bv_query)

        if display_text:
            # Display the raw data
            st.subheader("System Temperature (C)")
            st.write(data)

        if display_stats:
            # Display the stats of the data
            st.subheader("System Temperature (C)")
            st.markdown("**(Raw)**")
            mean_beamVel = round(data['sysTemp'].mean(), round_val)
            median_beamVel = round(data['sysTemp'].median(), round_val)
            min_beamVel = round(data['sysTemp'].min(), round_val)
            max_beamVel = round(data['sysTemp'].max(), round_val)
            std_beamVel = round(data['sysTemp'].std(), round_val)
            st.markdown("***Average Mean: *** " + str(mean_beamVel))
            st.markdown("***Average Median: *** " + str(median_beamVel))
            st.markdown("***Min: *** " + str(min_beamVel))
            st.markdown("***Max: *** " + str(max_beamVel))
            st.markdown("***Standard Deviation: *** " + str(std_beamVel))

        # Get the data from the query
        temps = data['sysTemp']
        dates = data['dateTime']

        # Create the plot
        self.sys_temp_fig = go.Figure(data=go.Scatter(
            x=dates,
            y=temps))

        # Set the layout with downward looking
        self.sys_temp_fig.update_layout(
            title="System Temperature (C)",
            xaxis_title="DateTime",
            yaxis_title="Temperature (C)",
            yaxis_autorange='reversed'  # Downward looking 'reversed'
        )

        if display_plot:
            # Add the plot
            st.subheader("System Temperature (C)")
            st.plotly_chart(self.sys_temp_fig)

    def display_temp_plots(self):
        # Group all the plots
        self.temps_subplots = make_subplots(rows=2,
                                            cols=1,
                                            row_titles=("Water", "System"),
                                            shared_xaxes="all",  # Share movement in X axis
                                            shared_yaxes="all",  # Share movement in Y axis
                                            vertical_spacing=0.025)  # Spacing between plots

        self.temps_subplots.update_layout(title_text="Temperatures")

        # Add all the plots
        self.temps_subplots.add_trace(self.water_temp_fig.data[0], row=1, col=1)
        self.temps_subplots.add_trace(self.sys_temp_fig.data[0], row=1, col=1)

        self.temps_subplots.write_html(self.gen_file_path(file_suffix="_temperatures", file_ext=".html"))
        st.plotly_chart(self.temps_subplots)

    def display_all_plots(self):
        # Get the min and max for all plots
        zmin = min(self.beam_min, self.instr_min, self.earth_vsr_min, self.mag_min)
        zmax = max(self.beam_max, self.instr_max, self.earth_vsr_max, self.mag_max)

        # Remove settings so that all the colorbars will overlap
        self.mag_vsr_fig.data[0].update(colorbar=dict(len=None, y=None))

        # Make all the min and max match for all plots
        self.beam_b0_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")
        self.beam_b1_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")
        self.beam_b2_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")
        self.beam_b3_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")

        self.instr_x_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")
        self.instr_y_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")
        self.instr_z_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")
        self.instr_err_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")

        self.earth_east_vsr_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")
        self.earth_north_vsr_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")
        self.earth_vert_vsr_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")

        self.mag_vsr_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")

        # Group all the plots
        all_fig_subplots = make_subplots(rows=12,
                                         cols=1,
                                         row_titles=("Beam 0", "Beam 1", "Beam 2", "Beam 3", "X", "Y", "Z", "East", "North", "Vert", "Error", "Magnitude"),
                                         shared_xaxes="all",  # Share movement in X axis
                                         shared_yaxes="all",  # Share movement in Y axis
                                         vertical_spacing=0.025)  # Spacing between plots

        all_fig_subplots.update_layout(title_text="Speeds (Vessel Speed Removed)")

        # Add all the plots
        all_fig_subplots.add_trace(self.beam_b0_fig.data[0], row=1, col=1)
        all_fig_subplots.add_trace(self.beam_b1_fig.data[0], row=2, col=1)
        all_fig_subplots.add_trace(self.beam_b2_fig.data[0], row=3, col=1)
        all_fig_subplots.add_trace(self.beam_b3_fig.data[0], row=4, col=1)

        all_fig_subplots.add_trace(self.instr_x_fig.data[0], row=5, col=1)
        all_fig_subplots.add_trace(self.instr_y_fig.data[0], row=6, col=1)
        all_fig_subplots.add_trace(self.instr_z_fig.data[0], row=7, col=1)

        all_fig_subplots.add_trace(self.earth_east_vsr_fig.data[0], row=8, col=1)
        all_fig_subplots.add_trace(self.earth_north_vsr_fig.data[0], row=9, col=1)
        all_fig_subplots.add_trace(self.earth_vert_vsr_fig.data[0], row=10, col=1)
        all_fig_subplots.add_trace(self.instr_err_fig.data[0], row=11, col=1)

        all_fig_subplots.add_trace(self.mag_vsr_fig.data[0], row=12, col=1)

        all_fig_subplots.write_html(self.gen_file_path(file_suffix="_plots", file_ext=".html"))

    def display_mag_dir_earth_corr_amp(self):
        # Get the min and max for all plots
        zmin = min(self.earth_vsr_min, self.mag_vsr_min)
        zmax = max(self.earth_vsr_max, self.mag_vsr_max)

        # Make all the min and max match for all plots
        self.earth_east_vsr_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")
        self.earth_north_vsr_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")
        self.earth_vert_vsr_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")
        self.instr_err_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")
        self.mag_vsr_fig.data[0].update(zmin=zmin, zmax=zmax, zauto=False, xaxis="x", yaxis="y")

        # Make the earth and mag overlap
        # Then move the other bars to align with plots
        self.mag_vsr_fig.data[0].update(colorbar=dict(len=0.1, y=0.95))
        self.dir_vsr_fig.data[0].update(colorbar=dict(len=0.1, y=0.82))

        vel_len = 0.50
        vel_y = 0.45
        self.earth_east_vsr_fig.data[0].update(colorbar=dict(len=vel_len, y=vel_len))
        self.earth_north_vsr_fig.data[0].update(colorbar=dict(len=vel_len, y=vel_len))
        self.earth_vert_vsr_fig.data[0].update(colorbar=dict(len=vel_len, y=vel_len))
        self.instr_err_fig.data[0].update(colorbar=dict(len=vel_len, y=vel_len))

        self.amp_b0_fig.data[0].update(colorbar=dict(len=0.10, y=0.18))

        self.corr_b0_fig.data[0].update(colorbar=dict(len=0.10, y=0.05))

        # Group all the plots
        all_fig_subplots = make_subplots(rows=8,
                                         cols=1,
                                         row_titles=("Magnitude", "Direction", "East", "North", "Vertical", "Error", "Amplitude", "Correlation"),
                                         shared_xaxes="all",  # Share movement in X axis
                                         shared_yaxes="all",  # Share movement in Y axis
                                         vertical_spacing=0.025)  # Spacing between plots

        # Add all the plots
        all_fig_subplots.add_trace(self.mag_vsr_fig.data[0], row=1, col=1)
        all_fig_subplots.add_trace(self.dir_vsr_fig.data[0], row=2, col=1)

        all_fig_subplots.add_trace(self.earth_east_vsr_fig.data[0], row=3, col=1)
        all_fig_subplots.add_trace(self.earth_north_vsr_fig.data[0], row=4, col=1)
        all_fig_subplots.add_trace(self.earth_vert_vsr_fig.data[0], row=5, col=1)
        all_fig_subplots.add_trace(self.instr_err_fig.data[0], row=6, col=1)

        all_fig_subplots.add_trace(self.amp_b0_fig.data[0], row=7, col=1)
        all_fig_subplots.add_trace(self.corr_b0_fig.data[0], row=8, col=1)

        all_fig_subplots.write_html(self.gen_file_path(file_suffix="_results", file_ext=".html"))

    def ens_handler(self, sender, ens):
        """
        Handle all the incoming data from the codec.  Add the ensembles
        to the project so they can be written to the database file.
        """
        if ens.IsEnsembleData:
            logging.debug(str(ens.EnsembleData.EnsembleNumber))

        # Add data to the SQLite project
        self.project.add_ensemble(ens)

    def query_data(self, conn_string: str, query: str):
        """
        Query the DB file for the data.
        This query is intended to remove the bad data.
        """
        # SQLite connection
        # Make a connection and create the tables
        # if not os.path.exists(self.conn_string):
        conn = sqlite3.connect(conn_string)

        # Query the data to a dataframe using pandas
        df = pd.read_sql_query(query, conn)

        # Return the results
        return df

    def filter_data(self, query: str):
        """
        Use the query string to get specific data you want in the CSV file.
        The data is taken from the DB file generated earlier.
        """

        # Filter the data using the query
        df = self.query_data(self.project.file_path, query)

        # Get the folder path from the project file path
        # Then create the CSV file
        folder_path = PurePath(self.project.file_path).parent
        prj_name = PurePath(self.project.file_path).stem
        csv_name = folder_path.joinpath(str(prj_name) + ".csv").as_posix()
        logging.debug("CSV File: " + csv_name)

        # Write the results to the CSV file
        df.to_csv(csv_name, index=False)

    def gen_file_path(self, file_suffix: str, file_ext: str = ".csv"):
        """
        Generate a file path for the project.
        This will place all the files in the same folder and the project file.
        This will append the file_suffix to the file name.
        This will use the extenstion given.

        :param file_suffix: File suffix to append to the file name.
        :param file_ext: File extension.
        """

        # Get the folder path from the project file path
        # Then create the CSV file
        folder_path = PurePath(self.project.file_path).parent
        prj_name = PurePath(self.project.file_path).stem + file_suffix
        file_path = folder_path.joinpath(str(prj_name) + file_ext).as_posix()
        logging.debug("File Path: " + file_path)

        return file_path


if __name__ == "__main__":
    to_csv = ReadPlotCSV()
    to_csv.select_and_process()

import logging
from pathlib import Path, PurePath, PureWindowsPath
import json
import sqlite3
import pandas as pd
from rti_python.Utilities.check_binary_file import RtiCheckFile
from rti_python.Writer.rti_sqlite_projects import RtiSqliteProjects
from rti_python.Writer.rti_sql import RtiSQL

# Set logging level
#logging.basicConfig(format='%(asctime)s [%(levelname)s] : %(message)s', level=logging.DEBUG)


class ReadRawToCSV:
    """
    Read in a raw binary file.  Then filter the data.  Then output to CSV
    """

    def __init__(self):
        self.project = None

    def select_and_process(self):
        """
        Select the files you would like to process.  Then create a DB file based on the binary files.
        If a DB file is selected, then load the data.
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


if __name__ == "__main__":
    to_csv = ReadRawToCSV()
    to_csv.select_and_process()
    to_csv.filter_data("SELECT * FROM ensembles WHERE roll > 160 OR roll < -160;")
